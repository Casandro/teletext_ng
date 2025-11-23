#!/bin/python3
import os
import time
import requests
from requests.auth import HTTPDigestAuth
import json
import datetime
import time
import random
from random import randint
import shutil
import sys
import base64
import gzip
import subprocess
import operator
import logging

import threading



class ConfigFileHandler:
    data = None
    modified = None

    def __init__(self, path):
        print("Init %s"%path)
        self.path=path
        if os.path.exists(self.path):
            self.load_file()
        else:
            print("File %s does not exist" %path)
            self.data={}

    def load_file(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                self.data=json.load(f)
                self.modified=os.path.getmtime(self.path)

    def save_file(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)

    def get(self, key):
        if os.path.exists(self.path):
            dt=os.path.getmtime(self.path)
            if (dt>self.modified):
                self.load_file()
        if self.data is None:
            print("data is None")
            return None
        if key in self.data:
            return self.data[key]
        return None

    def set(self, key, data):
        self.data[key]=data
        self.save_file()
        self.modified=time.time()

    def list(self):
        tmplist=[]
        if self.data is None:
            return tmplist
        for x in self.data:
            tmplist.append(x)
        return tmplist


class tvhLogger:
    chain = None
    def __init__(self, chain=None):
        self.ident=0
        self.stack=[]
        self.table=[]
    def logStart(self, s):
        print(s)
    def logEnd(self, s=None):
        print(s)
    def log(self, s):
        print(s)
    def log_table(self, l):
        self.table.append(l)
    def log_table_end(self):
        width={}
        for line in self.table:
            c=0
            for col in line:
                x=len(str(col))
                if not c in width:
                    width[c]=x
                else:
                    if x>width[c]:
                        width[c]=x
                c=c+1
        for line in self.table:
            c=0
            l=""
            for col in line:
                l=l+str(col)+" "*(width[c]-len(str(col))+1)
            self.log(l)
        self.table=[]


class TVHeadend:
    def __init__(self, username, password, path):
        self.username=username
        self.password=password
        self.path=path
    def getJson(self, path):
        logging.debug("getJson")
        req=requests.get(self.path+"/api/"+path, auth=HTTPDigestAuth(self.username, self.password))
        req.encoding="utf-8"
        if req.status_code!=200:
            raise Exception("status_code: %s, text:%s" % (req_status_code, req.text))
        return json.loads(req.text)
    def getObject(self, uuid):
        return self.getJson("raw/export?uuid=%s" % uuid)
    def getMuxCmd(self, uuid, pids):
        return "wget -o /dev/null -O - --read-timeout=20 --tries=1 %s/stream/mux/%s?pids=0,1,%s --user=%s --password=%s " % (self.path, uuid, ",".join(map(str,pids)), self.username, self.password)


def copy_properties(input_h, prop_list):
    output={}
    for p in prop_list:
        if p in input_h:
            output[p]=input_h[p]
    return output

class TeletextServer:
    def __init__(self, path, user, token):
        self.path=path
        self.user=user
        self.token=token
    def getJson(self, endpoint, i, retries=10):
        body={}
        body["token"]=self.token
        body["user"]=self.user
        body["endpoint"]=endpoint
        body["body"]=i
        #Fixme: compress data!

#        with open("/tmp/teletext-%s-%s" % (endpoint, round(time.time())), "w") as f:
#            f.write(json.dumps(body))
        timeout=1
        cnt=0
        status_code=None
        while status_code!=200:
            cnt=cnt+1
            req=requests.post(self.path, data=gzip.compress(json.dumps(body).encode("UTF-8")), headers={"Content-Encoding": "gzip"})
            status_code=req.status_code
            if cnt>retries:
                break
            time.sleep(timeout)
            timeout=timeout*1.1
        if req.status_code!=200:
            raise Exception("status_code: %s, text: %s" % (req.status_code, req.text))
        return json.loads(req.text)


class TVHeadendServer:
    mux_list=[]
    tmpdir="/tmp/teletext/"
    outdir=None
    locked=False
    internal_locks={}
    def __init__(self, config_file):
        self.config=ConfigFileHandler(config_file)
        tvh_config=self.config.get("tvheadend")
        tvh_user=tvh_config["username"]
        tvh_password=tvh_config["password"]
        tvh_path=tvh_config["path"]

        tts_config=self.config.get("server")
        tts_path=tts_config["path"]
        tts_user=tts_config["user"]
        tts_token=tts_config["token"]

        if not self.config.get("tmpdir") is None:
            self.tmpdir=self.config.get("tmpdir")
        if not self.config.get("outdir") is None:
            self.outdir=self.config.get("outdir")

        capture_limit=1.5
        start_time=time.time()
        
        self.logger=tvhLogger()
        self.tvheadend_path=tvh_path 
        self.tvheadend=TVHeadend(tvh_user, tvh_password, tvh_path)
        self.teletextserver=TeletextServer(tts_path, tts_user, tts_token)

        last_service_update=None

        threads=[]
        mux_sum=0
        time_sum=0
        while True:
            if last_service_update is None or last_service_update < time.time()-4*3600:
                self.update_services()
                last_service_update=time.time()

            time_sum=time_sum+1
            mux_sum=mux_sum+len(threads)
        
            avg_mux=mux_sum/time_sum
            ltime=time.time()
            time.sleep(10)
            for n in threads:
                if not n.is_alive():
                    threads.remove(n)
            print("Current average mux number %s Current number of muxes %s" % (avg_mux, len(threads)))
            start_new=False
            if avg_mux<capture_limit and len(threads)<round(capture_limit+0.4):
                start_new=True
            if capture_limit-len(threads)>1:
                start_new=True
            if start_new:
                t=threading.Thread(target=self.handle_transponder, args=())
                t.start()
                threads.append(t)


    #    while True:
     #       self.handle_transponder([])

    def update_services(self):
        self.logger.logStart("Update Services")
        muxes_raw=self.tvheadend.getJson("raw/export?class=dvb_mux")
        services_raw=self.tvheadend.getJson("raw/export?class=service")
        services_hash={}
        for service in services_raw:
            services_hash[service["uuid"]]=service
        wurst={}
        self.muxes={}
        for mux in muxes_raw:
            if (not "scan_last" in mux) or mux["scan_last"] == 0:
                continue
            if (not "scan_result" in mux) or mux["scan_result"] != 1:
                continue
            if mux["enabled"] != 1:
                continue
            if len(mux["services"])==0:
                continue
        
            services={}
            for sn in mux["services"]:
                service=services_hash[sn]
                if "last_seen" in service and service["last_seen"]<=time.time()-7*24*3600:
                    continue
                del service["uuid"]
                services[int(service["sid"])]=service
            mux["services"]=services

            self.muxes[mux["uuid"]]=mux
            del mux["uuid"]
        self.logger.logEnd("Update Services")
        with open("/tmp/muxes.json", "w") as f:
            f.write(json.dumps(self.muxes))
        return self.teletextserver.getJson("post_muxes", self.muxes)

    
    def handle_transponder(self):
        self.logger.logStart("Handle Transponder %s" )
        self.logger.logStart("get JSON")
        m=self.teletextserver.getJson("get_mux", None)
        self.logger.logEnd("%s" % m)
        mux=m["mux"]
        pids=m["pids"]
        self.internal_locks[mux]=m["names"]
        capture_time=time.time()
        # temp directory
        path=self.tmpdir
        if not os.path.isdir(path):
            os.makedirs(path)
        prefix="%s/%s-" % (path, capture_time)

        wget_cmd=self.tvheadend.getMuxCmd(mux, pids)
        tsteletext_cmd="ts_teletext --ts --stop -p%s '-s'" % (prefix)
        cmd="timeout 8000 %s | %s > /dev/null" % (wget_cmd, tsteletext_cmd)
        print(cmd)
        del self.internal_locks[mux]
        time.sleep(1)
        self.logger.logStart("actual capture")
        os.system(cmd)
        self.logger.logEnd()

        mux_result={}
        mux_result["pids"]={}
        mux_result["capture_time"]=capture_time
        mux_result["mux"]=mux
        
        for pid in pids:
            pid_s="0x{:04x}.zip".format(pid)
            filename=prefix+pid_s
            if not os.path.isfile(filename):
                print("File %s does not exist" % (filename))
                continue
            with open(filename+".txt", "rb") as f:
                header=f.read()
            os.unlink(filename+".txt")
            with open(filename, "rb") as f:
                content_bin=f.read()
            os.unlink(filename)
            content_gzip=gzip.compress(content_bin)
            content_base64=base64.b64encode(content_gzip).decode("ASCII")
            print("%s %s %s" % (pid, len(content_bin), header))
            service_hash={}
            service_hash["header"]=header.decode("UTF-8")
            service_hash["content"]=content_base64
            mux_result["pids"][int(pid)]=service_hash
        self.logger.logStart("uploading")
        tmp=self.teletextserver.getJson("upload", mux_result)
        self.logger.logEnd()
        self.logger.logEnd()
        return

def handle_transponder_thread(tvh):
    print("Handle transponder thread %s %s" %(threading.current_thread().name, tvh))
    tvh.handle_transponders([])
            

#logging.basicConfig(level=0)
#server=TVHeadendServer("teletext", "teletext", "http://192.168.5.5:9981/", "http://localhost:8888/", "wurst", "passwort")
server=TVHeadendServer("wurst.json")

#print(json.dumps(server.muxes, indent=True))
