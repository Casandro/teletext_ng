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
    def getJson(self, endpoint,i):
        body={}
        body["token"]=self.token
        body["user"]=self.user
        body["endpoint"]=endpoint
        body["body"]=i
        req=requests.post(self.path, data=json.dumps(body))
        if req.status_code!=200:
            raise Exception("status_code: %s, text: %s" % (req.status_code, req.text))
        return json.loads(req.text)


class TVHeadendServer:
    mux_list=[]
    tmpdir="/tmp/"
    outdir="/tmp/outdir/"
    def __init__(self, tvh_user, tvh_password, tvh_path, tts_path, tts_user, tts_token):
        self.tvheadend_path=tvh_path 
        self.tvheadend=TVHeadend(tvh_user, tvh_password, tvh_path)
        self.teletextserver=TeletextServer(tts_path, tts_user, tts_token)
        self.update_services()
        self.update_oldest_changed()
        self.handle_transponders()
#        print(json.dumps(self.muxes, indent=True))
    def update_services(self):
        muxes_raw=self.tvheadend.getJson("raw/export?class=dvb_mux")
        services_raw=self.tvheadend.getJson("raw/export?class=service")
        services_hash={}
        for service in services_raw:
            services_hash[service["uuid"]]=service
        self.muxes={}
        for mux in muxes_raw:
            if (not "scan_last" in mux) or mux["scan_last"] == 0:
                continue
            last_scan=mux["scan_last"]
            text_services={}
            for s in mux["services"]:
                service=services_hash[s]
                nservice={}
                for stream in service["stream"]:
                    if stream["type"]!="TELETEXT":
                        continue
                    text_temp={}
                    text_temp["properties"]=copy_properties(service, ("svcname", "provider", "last_seen"))
                    text_services[stream["pid"]]=text_temp
            if len(text_services)==0:
                continue
            omux={}
            omux["properties"]=copy_properties(mux, ("frequency", "symbolrate", "orbital", "delsys", "polarisation"))
            omux["texts"]=text_services
            self.muxes[mux["uuid"]]=omux
        self.update_service_names()

    def update_service_names(self): #Update service names
        services={}
        for sn in self.muxes:
            s=self.muxes[sn]
            for x in s["texts"]:
                text=s["texts"][x]
                service={}
                #Copy properties of mux
                for p in s["properties"]:
                    service[p]=s["properties"][p]
                #copy service properties
                for p in text["properties"]:
                    service[p]=text["properties"][p]
                service["pid"]=x
                name="%s_%s"%(sn, x)
                services[name]=service
        tmp=self.teletextserver.getJson("translate", services)
        muxes=[]
        for service in tmp:
            mux=service.split("_")[0]
            service_name=tmp[service]
            if service_name!="BLOCK":
                if not mux in muxes:
                    muxes.append(mux)
        new_muxes={}
        for mux_id in muxes:
            mux=self.muxes[mux_id]
            texts={}
            for text_pid in mux["texts"]:
                name="%s_%s"%(mux_id, text_pid)
                if tmp[name]!='BLOCK':
                    text=mux["texts"][text_pid]
                    text["service_name"]=tmp[name]
                texts[text_pid]=text
            if len(texts)>0:
                mux["texts"]=texts
                service_names=[]
                for pid in texts:
                    sn=texts[pid]["service_name"]
                    if not (sn in service_names):
                        service_names.append(sn)
                mux["service_names"]=service_names
                new_muxes[mux_id]=mux
        self.muxes=new_muxes

    def update_oldest_changed(self): #Fixme, create version that works on self.mux_list
        service_hash={}
        for mux_id in self.muxes:
            mux=self.muxes[mux_id]
            service_hash[mux_id]=mux["service_names"]
        tmp=self.teletextserver.getJson("oldest_service", service_hash)
        tmp_list=[]
        for mux_id in self.muxes:
            tmp_list.append([mux_id, 0])
        self.mux_list=tmp_list
        self.update_oldest_changes_from_list()

    def update_oldest_changes_from_list(self): # Updates self.mux_list
        service_hash={}
        for mux_li in self.mux_list:
            mux_id=mux_li[0]
            mux=self.muxes[mux_id]
            service_hash[mux_id]=mux["service_names"]
        tmp=self.teletextserver.getJson("oldest_service", service_hash)
        tmp_list=[]
        for mux_id in tmp:
            mux=self.muxes[mux_id]
            if "oldest_changed" in mux and mux["oldest_changed"]<tmp[mux_id]: #If the oldest time on the mux has been updated
                continue # skip that mux, so we won't use it again this cyle
            mux["oldest_changed"]=tmp[mux_id]
            tmp_list.append([mux_id, tmp[mux_id]])
        self.mux_list=sorted(tmp_list, key=operator.itemgetter(1))

            
    def handle_transponders(self): 
        while len(self.mux_list)>0:
            mux=self.mux_list[0]
            self.mux_list.remove(mux)
            self.handle_transponder(mux[0])
            self.update_oldest_changes_from_list()
        return
    
    def handle_transponder(self, uuid):
        capture_time=time.time()
#        date_prefix=datetime.datetime.utcfromtimestamp(capture_time).isoformat(timespec="seconds")+"+00:00"
        date_prefix=datetime.datetime.fromtimestamp(capture_time, datetime.UTC).isoformat(timespec="seconds")

        path="%s/%s" % (self.tmpdir,uuid)
        if not os.path.isdir(path):
            os.makedirs(path)
        prefix="%s/%s-" % (path, date_prefix)
        mux=self.muxes[uuid]
        pids=[]
        service_names=[]
        for pid in mux["texts"]:
            pids.append(pid)
            name=mux["texts"][pid]["service_name"]
            if not name in service_names:
                service_names.append(name)
        tmp=self.teletextserver.getJson("lock", service_names)
        print(tmp)
        if tmp!="OK":
            print("Locking did not work")
            tmp=self.teletextserver.getJson("unlock", service_names)
            print(tmp)

        wget_cmd=self.tvheadend.getMuxCmd(uuid, pids)
        tsteletext_cmd="ts_teletext --ts --stop -p%s" % (prefix)
        cmd="timeout 8000 %s | %s > /dev/null 2> /dev/null" % (wget_cmd, tsteletext_cmd)
        print(cmd)
        os.system(cmd)

        for pid in mux["texts"]:
            name=mux["texts"][pid]["service_name"]
            pid_s="0x{:04x}.zip".format(pid)
            filename=prefix+pid_s
            if not os.path.isfile(filename):
                print("File %s does not exist" % (filename))
                continue
            with open(filename, "rb") as f:
                content_bin=f.read()
            content_gzip=gzip.compress(content_bin)
            content_base64=base64.b64encode(content_gzip).decode("ASCII")
            print("raw: %s, gzip: %s, base64: %s" % (len(content_bin), len(content_gzip), len(content_base64)))
            odir=self.outdir+"/"+name
            if not os.path.isdir(odir):
                os.makedirs(odir)
            shutil.move(filename, odir)
            print(filename, name)
            service_hash={}
            service_hash["service"]=name
            service_hash["time"]=capture_time
            service_hash["pid"]=pid
            service_hash["content"]=content_base64
            tmp=self.teletextserver.getJson("upload", service_hash)
            print(tmp)
        tmp=self.teletextserver.getJson("unlock", service_names)
        #todo: remove transponders that only have "service_name" services
        return


            

#logging.basicConfig(level=0)
server=TVHeadendServer("teletext", "teletext", "http://192.168.5.5:9981/", "http://localhost:8888/", "wurst", "passwort")

#print(json.dumps(server.muxes, indent=True))
