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
import subprocess
import logging


class TVHeadend:
    cache_mtime=None
    cache_flush=None
    def __init__(self, username, password, path):
        self.username=username
        self.password=password
        self.path=path
        self.cachefile="/tmp/tvheadend_teletext.cache"
        self.cache={}
        self.loadCache()
    def getJson(self, path):
        logging.debug("getJson")
        req=requests.get(self.path+"/"+path, auth=HTTPDigestAuth(self.username, self.password))
        req.encoding="utf-8"
        if req.status_code!=200:
            raise Exception("status_code: %s, text:%s" % (req_status_code, req.text))
        return json.loads(req.text)
    def loadCache(self):
        if not os.path.exists(self.cachefile):
            return
        if (not (self.cache_mtime is None)) and (self.cache_mtime <= os.path.getmtime(self.cachefile)):
            return
        print("loadCache actual load %s %s"%(self.cache_mtime, os.path.getmtime(self.cachefile)))
        with open(self.cachefile) as f:
            self.cache=json.load(f)
        self.cache_mtime=os.path.getmtime(self.cachefile)
    def saveCache(self, force=True):
        if self.cache_flush is None or self.cache_flush > time.time():
            return
        print("save Cache %s %s" %(self.cache_flush,time.time()))
        with open(self.cachefile, "w") as f:
            json.dump(self.cache, f)
        self.cache_mtime=time.time()
        self.cache_flush=None
    def getObject(self, uuid):
        return self.getJson("raw/export?uuid=%s" % uuid)
    def getMultiplex(self, uuid, last_scan):
        self.loadCache()
        if not (self.cache is None) and uuid in self.cache:
            mux=self.cache[uuid]
            if "time" in mux and mux["time"]>=last_scan:
                return mux["data"]
        mux=self.getObject(uuid)
        tmp={}
        tmp["time"]=last_scan
        tmp["data"]=mux
        self.cache[uuid]=tmp
        if self.cache_flush is None:
            self.cache_flush=time.time()+10
        self.saveCache()
        return mux


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
    def __init__(self, tvh_user, tvh_password, tvh_path, tts_path, tts_user, tts_token):
        self.tvheadend=TVHeadend(tvh_user, tvh_password, tvh_path)
        self.teletextserver=TeletextServer(tts_path, tts_user, tts_token)
        self.update_services()
        self.update_oldest_changed()
#        print(json.dumps(self.muxes, indent=True))
    def update_services(self):
        muxes_raw=self.tvheadend.getJson("raw/export?class=dvb_mux")
        self.muxes={}
        for mux in muxes_raw:
            if (not "scan_last" in mux) or mux["scan_last"] == 0:
                continue
            last_scan=mux["scan_last"]
            text_services={}
            for s in mux["services"]:
                service_raw=self.tvheadend.getMultiplex(s, last_scan)
                for service in service_raw:
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
        self.tvheadend.saveCache(force=True)
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

    def update_oldest_changed(self):
        for mux_id in self.muxes:
            mux=self.muxes[mux_id]
            tmp=self.teletextserver.getJson("oldest_service", mux["service_names"])
            mux["oldest_changed"]=tmp

            

#logging.basicConfig(level=0)
server=TVHeadendServer("teletext", "teletext", "http://192.168.5.5:9981/api", "http://localhost:8888/", "wurst", "passwort")

#print(json.dumps(server.muxes, indent=True))
