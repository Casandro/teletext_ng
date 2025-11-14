#!/bin/python3

import os
import json
import time
import datetime
import gzip
import base64

from http.server import BaseHTTPRequestHandler, HTTPServer

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Wurst", "utf-8"))
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        body_bytes=self.rfile.read(content_len)
        try:
            full_json=json.loads(body_bytes.decode("utf-8"))
            print(json.dumps(full_json, indent=True)[:500])
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("%s" % e, "utf-8"))
            return
        token=full_json["token"]
        user=full_json["user"]
        endpoint=full_json["endpoint"]
        body=full_json["body"]
        output=None
        if endpoint == "translate":
            output=self.translations(body)
        if endpoint == "oldest_service":
            output=self.oldest_service(body)
        if endpoint == "upload":
            output=self.upload(body)
        if endpoint in ("lock", "unlock"):
            output=self.lock_unlock(body, endpoint)
        if output is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("Wurst", "utf-8"))
        print(json.dumps(output, indent=True)[:500])
        self.send_response(200)
        self.send_header("Content-Type", "text/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(output), "utf-8"))
    def translations(self, services):
        names={}
        global teletext_server
        for sn in services:
            names[sn]=teletext_server.getServiceName(services[sn])
        return names
    def oldest_service(self, services):
        global teletext_server
        output={}
        for uuid in services:
            service=services[uuid]
            r=teletext_server.getOldestServiceAge(service)
            output[uuid]=r
        return output
    def upload(self, body):
        r=teletext_server.upload(body["service"], body["time"], body["pid"], body["content"])
        return r
    def lock_unlock(self, body, endpoint):
        cnt=0
        for service in body:
            if teletext_server.lockUnlockService(service, endpoint):
                cnt=cnt+1
        if cnt==0: #Locking didn't work
            return "Could not lock"
        return "OK"



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


def clean_string(s):
    o=""
    for c in s.upper():
        if c==" ":
            continue
        if c.isalnum():
            o=o+c
    return o


class TeletextServer:
    def __init__(self, path):
        basic_config=ConfigFileHandler(path)
        var_directory=basic_config.get("var_dir")
        print("var_directory: %s" % var_directory)
        if var_directory is None:
            var_directory="/var/spool/teletext_server"
        self.translations=ConfigFileHandler(var_directory+"/translations.json")
        self.service_locks=ConfigFileHandler(var_directory+"/locks.json")
        self.users=ConfigFileHandler(var_directory+"/users.json")
        self.out_dir=basic_config.get("out_dir")
        with open('translations.json') as t_file:
           self.legacy_translations=json.load(t_file)
    def lockUnlockService(self, service_name, endpoint):
        print("lockUnlockService %s %s" %( service_name, endpoint))
        s=self.service_locks.get(service_name)
        if s is None:
            s={}
            s["locked"]=False
            s["last_used"]=None
        if endpoint=="lock":
            if "locked" in s and s["locked"]:
                return False
            s["locked"]=True
            s["locked_until"]=time.time()+8000
        else: #Unlock
            s["locked"]=False
            s["locked_until"]=0
        self.service_locks.set(service_name, s)
        return True
    def getOldestServiceAge(self, service_names):
        oldest_time=time.time()
        for name in service_names:
            s=self.service_locks.get(name)
            # If the service is unknown, asume it never was used
            if s is None:
                return 0;
            if "locked_until" in s and not (s["locked_until"] is None) and s["locked_until"]<time.time():
                s["locked"]=False
                s["locked_until"]=0
                self.service_locks.set(name, s)
            if "locked" in s and s["locked"]:
                continue
            if "last_used" in s and not (s["last_used"] is None):
                if s["last_used"] < oldest_time:
                    oldest_time=s["last_used"]
        return oldest_time

    def upload(self, service, dumptime, pid, content):
        path=self.out_dir+"/"+service.replace("/", "").replace("\\","").replace(" ","")
        if not os.path.isdir(path):
            os.makedirs(path)
        filename=path+"/"+datetime.datetime.fromtimestamp(dumptime, datetime.UTC).isoformat(timespec="seconds")+"-0x"+"{:04x}".format(pid)+".zip"
        print(filename)
        with open(filename, "wb") as f:
            f.write(gzip.decompress(base64.b64decode(content)))
        self.lockUnlockService(service, "unlock")
        s=self.service_locks.get(service)
        s["last_used"]=time.time()

        return "OK"

    def getLegacyServiceName(self, service):
        mux_name=""
        orbital=""
        if "delsys" in service:
            mux_name=mux_name+service["delsys"]+"-"
            position=service["delsys"]
        if "frequency" in service:
            mux_name=mux_name+str(service["frequency"]);
        if "polarisation" in service:
            mux_name=mux_name+service["polarisation"]
        if "orbital" in service:
            mux_name=mux_name+"-"+service["orbital"]
            position=service["orbital"]
        sname=""
        if ('sid' in service):
            sname="SID-"+str(service['sid'])
        if ('svcname' in service):
            sname=service['svcname']
        srvname=sname.upper().replace(" HD","").replace(" ","").replace("/","").replace("$","").replace(":","_")
        if srvname+"_"+mux_name in self.legacy_translations:
            x=self.legacy_translations[srvname+"_"+mux_name]
            if len(x)>1:
                return x
        if srvname+"_"+position in self.legacy_translations:
            x=self.legacy_translations[srvname+"_"+position]
            if len(x)>1:
                return x
        if srvname in self.legacy_translations:
            x=self.legacy_translations[srvname]
            if len(x)>1:
                return x
        return None

    def getBogusServiceName(self, service):
        name_parts=[]
        for x in ("svcname", "provider", "pid", "polarisation", "orbital" ):
            if x in service:
                name_parts.append(clean_string(str(service[x])))
        return "___"+"-".join(name_parts)
    def getServiceHash(self, service):
        name_parts=[]
        for x in ("provider", "svcname", "frequency", "polarisation", "orbital", "pid"):
            if x in service:
                name_parts.append(clean_string(str(service[x])))
        return "-".join(name_parts)

    def getServiceName(self, service):
        for s_id in self.translations.list():
            s=self.translations.get(s_id)
            sn=s["service_name"]
            accept=True
            for prop in service:
                if not prop in s:
                    continue
                if prop == "svcname":
                    if s["svcname"].upper().replace(" HD", "")==service["svcname"].upper().replace(" HD", ""):
                        continue
                if prop == "frequency" and "symbolrate" in service:
                    diff=abs(s["frequency"]-service["frequency"])
                    if diff>service["symbolrate"]/1000*0.1:
                        accept=False
                        continue
                if s[prop]!=service[prop]:
                    accept=False
                    break
            if accept:
                if sn=="":
                    print("getServiceName got empty %s" % service)
                return sn
        name=self.getLegacyServiceName(service)
        if name=="BLOCK":
            return name
        if name is None or name=="":
            name=self.getBogusServiceName(service)
        if name=="":
            print("getService name got empty at the end %s" %service)
        del service["last_seen"]
        if name!="":
            service["service_name"]=name
            self.translations.set(self.getServiceHash(service), service)
        return name


teletext_server=TeletextServer("conf/teletext_server.conf")

with HTTPServer(('', 8888), handler) as server:
    server.serve_forever()


