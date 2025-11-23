#!/bin/python3

import os
import json
import time
import datetime
import gzip
import base64
import hashlib
import secrets
import html
import operator

from http.server import BaseHTTPRequestHandler, HTTPServer

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        teletext_server.writeList(self.wfile)
    def do_POST(self):
        #fixme do compression
        encoding=self.headers.get("Content-Encoding")
        print("Encoding: %s" % encoding)
        content_len = int(self.headers.get('Content-Length'))
        if encoding=="gzip":
            body_bytes=gzip.decompress(self.rfile.read(content_len))
        else:
            body_bytes=self.rfile.read(content_len)
        try:
            full_json=json.loads(body_bytes.decode("utf-8"))
            #print(json.dumps(full_json, indent=True)[:500])
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
        print("user: %s, endpoint: %s" % (user, endpoint))
        auth=self.authenticate(user, token, endpoint)
        if auth != True:
            self.send_response(407)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(auth), "utf-8"))
            return
        output=None
        if endpoint == "post_muxes":
            output=self.post_muxes(user, body)
        if endpoint == "get_mux":
            output=self.get_mux(user, body)
        if endpoint == "upload":
            output=self.upload(user, body)
        if endpoint == "status":
            output=teletext_server.status(user, body)
        if output is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("Wurst", "utf-8"))
        #print(json.dumps(output, indent=True)[:500])
        self.send_response(200)
        self.send_header("Content-Type", "text/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(output), "utf-8"))
    def post_muxes(self, user, body):
        return teletext_server.post_muxes(user, body)
    def get_mux(self, user, body):
        return teletext_server.get_mux(user, body)
    def upload(self, user, body):
        return teletext_server.upload(user,body)

    def authenticate(self, user, token, endpoint):
        if teletext_server.authenticate(user, token, endpoint):
            return True
        return False



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
        with open(self.path+".tmp", "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)
        if os.path.exists(self.path):
            os.rename(self.path, self.path+".backup")
        os.rename(self.path+".tmp", self.path)

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
        if key==None:
            raise ValueError("config set key=None")
            return
        self.data[key]=data
        self.save_file()
        self.modified=time.time()

    def delete(self, key):
        del self.data[key]
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
        if c in "-_":
            o=o+c
    return o


class MuxHandler:
    muxfile=None
    muxes={} # muxes["$orbital_%onid_$tsid_$polarisation"]=[mux]
    # mux["id"]="$orbital..."
    # mux["exemplar"]=latest mux from client
    # mux["texts"][pid]...
    translations={} # translations[user][uuid]=id 
    def __init__(self, muxfile):
        self.muxfile=muxfile
        self.load_from_file()
        self.legacy_translations=None
        if os.path.exists("translations.json"):
            with open("translations.json") as f:
                self.legacy_translations=json.load(f)
        return
    def load_from_file(self):
        if os.path.exists(self.muxfile):
            with open(self.muxfile, "r") as f:
                self.muxes=json.load(f)
    def save_to_file(self):
        with open(self.muxfile+".tmp", "w") as f:
            json.dump(self.muxes, f, indent=1)
        if os.path.exists(self.muxfile+".bak"):
            os.unlink(self.muxfile+".bak")
        if os.path.exists(self.muxfile):
            os.rename(self.muxfile, self.muxfile+".bak")
        os.rename(self.muxfile+".tmp", self.muxfile)
    def legacy_translate(self, mux, service):
        muxname=""
        if "delsys" in mux:
            muxname=muxname+mux["delsys"]+"-"
            position=mux["delsys"]
        if "frequency" in mux:
            muxname=muxname+str(mux["frequency"]);
        if "polarisation" in mux:
            muxname=muxname+mux["polarisation"]
        if "orbital" in mux:
            muxname=muxname+"-"+mux["orbital"]
            position=mux["orbital"]

        sname=""
        if "sid" in service:
            sname="SID-"+str(service['sid'])
        if "svcname" in service:
            sname=service["svcname"]
        srvname=sname.upper().replace(" HD","").replace(" ","").replace("/","").replace("$","").replace(":","_")
        if srvname+"_"+muxname in self.legacy_translations:
            x=self.legacy_translations[srvname+"_"+muxname]
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

    def get_key(self, mux):
        key_items=[]
        for k in ("delsys", "orbital", "onid", "tsid", "polarisation", "stream_id", "pls_code"):
            if k in mux:
                key_items.append(str(mux[k]))
        return "_".join(key_items)
    def find_mux_by_id(self, mux_id):
        sp=mux_id.split("_")
        key="_".join(sp[:-1])
        frq=float(sp[-1])*1000
        if key in self.muxes:
            mux_list=self.muxes[key]
            if len(mux_list)==1:
                return mux_list[0]
            for mux in mux_list:
                exemplar=mux["exemplar"]
                diff=abs(exemplar["frequency"]-frq)
                if diff<exemplar["symbolrate"]/1000*0.1:
                    return mux
        return None
        
    def find_or_create_mux(self, local_mux):
        key=self.get_key(local_mux)
        if not key in self.muxes:
            self.muxes[key]=[]
            mux={}
            mux["exemplar"]=local_mux
            mux["id"]=key+"_"+str(round(local_mux["frequency"]/1000))
            self.muxes[key].append(mux)
        muxes=self.muxes[key]
        if len(muxes)==1:
            return muxes[0]
        for mux in muxes:
            exemplar=mux["exemplar"]
            diff=abs(exemplar["frequency"]-local_mux["frequency"])
            if diff<exemplar["symbolrate"]/1000*0.1:
                return mux
        #Nothing found, attach mux
        mux={}
        mux["exemplar"]=local_mux
        mux["id"]="%s_%s"% (key,str(local_mux["frequency"]))
        self.muxes[key].append(mux)
        return mux
    def post_mux(self, lmux):
        mux=self.find_or_create_mux(lmux)
        self.update_mux(mux, local_mux=lmux)
        return mux
    def save_muxes(self):
        self.save_to_file()
        return True
    def update_mux(self, mux, local_mux=None):
        if not local_mux is None:
            mux["exemplar"]=local_mux
        if not "text_services" in mux:
            mux["text_services"]={}
        m=mux["exemplar"]
        for s in m["services"]:
            service=m["services"][s]
            for stream in service["stream"]:
                if stream["type"]=="TELETEXT":
                    pid=str(stream["pid"])
                    if not pid in mux["text_services"]:
                        mux["text_services"][pid]={}
                    ts=mux["text_services"][pid]
                    if "svcname" in service:
                        ts["svcname"]=service["svcname"]
                    if not "service_name" in ts:
                        sname=self.legacy_translate(local_mux, service)
                        if sname!="":
                            ts["service_name"]=sname
                        else:
                            if "svcname" in service:
                                sname=service["svcname"].upper().replace(" ","-").replace("/","").replace(".","").replace("-HD","") +"_"
                            ts["service_name"]="___"+mux["id"]+"_"+sname+str(pid)
        #Fixme, handle translation tables between local and global muxes
        return True
                    


class TeletextServer:
    def __init__(self, path):
        self.basic_config=ConfigFileHandler(path)
        var_directory=self.basic_config.get("var_dir")
        print("var_directory: %s" % var_directory)
        if var_directory is None:
            var_directory="/var/spool/teletext_server"
        self.users=ConfigFileHandler(var_directory+"/users.json")
        self.muxhandler=MuxHandler(var_directory+"/muxes.json")
        self.mux_translations=ConfigFileHandler(var_directory+"/mux_translations.json")
        self.text_services=ConfigFileHandler(var_directory+"/text_services.json")
        self.out_dir=self.basic_config.get("out_dir")
        if self.out_dir is None:
            print("Please set out_dir")
            return False


    def get_http_port(self):
        return self.basic_config.get("listen_port")

    def upload(self, user, body):
        local_mux=body["mux"]
        translations=self.mux_translations.get(user)
        mux_id=translations["local_to_global"][local_mux]
        print("upload mux_id: %s, local_mux: %s" %(mux_id, local_mux))
        capture_time=body["capture_time"]

        mux=self.muxhandler.find_mux_by_id(mux_id)
        if mux is None:
            return "ERROR"

        if "locked" in mux:
            del mux["locked"]
        mux["last_attempt"]=time.time()

        if not "captures" in mux:
            mux["captures"]=[]
        mux["captures"].append([capture_time, time.time()-capture_time, user])
        mux["captures"]=self.filter_captures(mux["captures"])

        #Keys when stored in JSON are always strings
        for pid in mux["text_services"]:
            pid_s=str(pid)
            text_service=mux["text_services"][pid_s]
            #Try to find pid in upload
            if pid_s in body["pids"]:
                print("pid %s in body" % pid_s)
                capture=body["pids"][pid_s]
                length=len(capture["content"])
                header=capture["header"]
                if not "captures" in text_service:
                    text_service["captures"]=[]
                text_service["captures"].append([capture_time, user, length, header])
                text_service["captures"]=self.filter_captures(text_service["captures"])
                service_name=text_service["service_name"]
                if service_name is None:
                    print("Service Name = None!!!")
                    continue
                ts=self.text_services.get(service_name)
                if ts is None:
                    ts={}
                if "locked" in ts:
                    del ts["locked"]
                ts["last_used"]=time.time()
                self.text_services.set(service_name, ts)
                path=self.out_dir+"/"+service_name.replace("/", "").replace("\\","").replace(" ","")
                if not os.path.isdir(path):
                    os.makedirs(path)
                filename=path+"/"+datetime.datetime.fromtimestamp(capture_time, datetime.UTC).isoformat(timespec="seconds")+"-0x"+"{:04x}".format(int(pid))+".zip"
                print(filename)
                with open(filename+".tmp", "wb") as f:
                    file_bin=base64.b64decode(capture["content"])
                    file_decompressed=gzip.decompress(file_bin)
                    f.write(file_decompressed)
                os.rename(filename+".tmp", filename)
            else:
                print("pid %s not in body" % pid)
                if not "captures" in text_service:
                    text_service["captures"]=[]
                text_service["captures"].append([capture_time, user, 0, None])
                text_service["captures"]=self.filter_captures(text_service["captures"])
        self.muxhandler.save_muxes()

        return "OK"

    def is_service_good(self, text_service):
        if text_service["service_name"]=="BLOCK":
            return False
        if not "captures" in text_service:
            return True 
        if len(text_service["captures"])<4:
            return True
        max_size=0
        size_sum=0
        cnt=0
        for captures in text_service["captures"]:
            date=captures[0]
            if date<time.time()-7*24*3600:
                continue
            size=captures[2]
            if size>max_size :
                max_size=size
            size_sum=size_sum+size
            cnt=cnt+1
        if max_size<1000:
            return False
        if max_size>10000:
            return True
        if avg_size>max_size/2:
            return True
        return False

    def filter_captures(self, captures):
        cutoff=time.time()-7*24*3600
        captures_new=[]
        for c in captures:
            if c[0]<cutoff:
                continue
            captures_new.append(c)
        return captures_new

    def get_oldest_service(self, mux):
        oldest=None
        if "locked" in mux and mux["locked"]>time.time():
            return False
        text_services=mux["text_services"]
        cnt=0
        for pid in text_services:
            ts=text_services[pid]
            if not self.is_service_good(ts):
                continue
            service_name=ts["service_name"]
            if service_name=="BLOCK":
                continue
            service_info=self.text_services.get(service_name)
            if service_info is None:
                service_info={}
            if "locked" in service_info and service_info["locked"]>time.time():
                continue
            if not "last_used" in service_info:
                return None
            if oldest is None or service_info["last_used"]<oldest:
                oldest = service_info["last_used"]
            cnt=cnt+1
        if cnt==0:
            return False
        return oldest


    def get_mux(self, user, body):
        translations=self.mux_translations.get(user)
        local_to_global=translations["local_to_global"]
        oldest=time.time()
        oldest_mux=None
        oldest_lmux=None
        for lmux in local_to_global:
            gmux=local_to_global[lmux]
            mux=self.muxhandler.find_mux_by_id(gmux)
            if mux is None:
                print("mux %s not found here" % (lmux))
                continue
            if "locked" in mux and mux["locked"]>=time.time():
                print("mux %s %s is locked" % (lmux, gmux))
                continue
            last=self.get_oldest_service(mux)
            if last==False:
                continue
            if last is None and not mux is None:
                oldest_mux=mux
                oldest_lmux=lmux
                print("last is none and not mux is none")
                break
            if last<oldest:
                oldest=last
                oldest_mux=mux
                oldest_lmux=lmux

        if oldest_mux is None:
            print("OLDEST_MUX is None!!!!")
            return False

        oldest_mux["locked"]=round(time.time()+8000)
        pids=[]
        service_names={}
        for x in oldest_mux["text_services"]:
            ts=oldest_mux["text_services"][x]
            service_name=ts["service_name"]
            if service_name is None:
                continue
            s=self.text_services.get(service_name)
            if s is None:
                s={}
            s["locked"]=time.time()+8000
            self.text_services.set(service_name, s)
            p=int(x)
            if not p in pids:
                pids.append(p)
                service_names[p]=service_name
        result={}
        result["mux"]=oldest_lmux
        result["pids"]=pids
        result["names"]=service_names
        return result

    def calc_auth(self, salt, user, token):
        h=hashlib.sha512(user.encode("UTF-8"))
        h.update(salt)
        h.update(token.encode("UTF-8"))
        return h.digest()

    def authenticate(self, user, token, endpoint):
        u=self.users.get(user)
        if u is None:
            u={}
            u["accepted"]=False
            salt=secrets.token_bytes(64)
            u["salt"]=base64.b64encode(salt).decode("ASCII")
            auth=self.calc_auth(salt, user, token)
            u["auth"]=base64.b64encode(auth).decode("ASCII")
            self.users.set(user, u)
            return False
        salt=base64.b64decode(u["salt"].encode("ASCII"))
        auth=base64.b64decode(u["auth"].encode("ASCII"))
        ia=self.calc_auth(salt, user, token)
        if ia==auth:
            return True
        return False

    def writeRow(self, wfile, row, header=False):
        line="<tr>"
        for c in row:
            s=html.escape(str(c))
            if header:
               line=line+"<th>%s</th>"%s
            else:
               line=line+"<td>%s</td>"%s
        line=line+"</tr>\r\n"
        wfile.write(line.encode("UTF-8"))

    def writeList(self, wfile):
        wfile.write(b"<html><header><title>Wurst</title></header>")
        wfile.write(b"<body>")
        wfile.write(b"<table>")
        mux_list=[]
        for sn in self.text_services.list():
            s=self.text_services.get(sn)
            lu=0
            if "last_used" in s:
                lu=s["last_used"]
            locked=False
            if "locked" in s:
                locked=s["locked"]
            if locked>time.time():
                locked=True
            mux_list.append([lu, sn, locked])

        for m in sorted(mux_list, key=operator.itemgetter(0)):
            lu=m[0]
            sn=m[1]
            locked=m[2]
            lu_string="never"
            if lu>0:
                lu_string=datetime.timedelta(seconds=(round((time.time()-lu))))
            self.writeRow(wfile, [sn, lu_string, locked])
        
        wfile.write(b"</table>")
        wfile.write(b"</body>")
        return
    def post_muxes(self, user, muxes):
        mux_translations={}
        mux_translations["local_to_global"]={}
        mux_translations["global_to_local"]={}
        for luuid in muxes:
            lmux=muxes[luuid]
            res=self.muxhandler.post_mux(lmux)
            mux_translations["local_to_global"][luuid]=res["id"]
            mux_translations["global_to_local"][res["id"]]=luuid
        self.muxhandler.save_muxes()
        self.mux_translations.set(user, mux_translations)
        return True
    def status(self, user, body):
        duration=body["duration"]
        muxes=body["muxes"]
        for mux in muxes:
            local_mux=mux
            translations=self.mux_translations.get(user)
            mux_id=translations["local_to_global"][local_mux]
            
            mux=self.muxhandler.find_mux_by_id(mux_id)
            if mux is None:
                continue
            mux["locked"]=time.time()+duration
        return True

teletext_server=TeletextServer("/etc/teletext_server.json")

with HTTPServer(('', teletext_server.get_http_port()), handler) as server:
    server.serve_forever()


