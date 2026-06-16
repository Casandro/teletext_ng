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
import sqlite3
import random

from http.server import BaseHTTPRequestHandler, HTTPServer

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        teletext_server.writeList(self.wfile)
    def do_POST(self):
        #fixme do compression
        encoding=self.headers.get("Content-Encoding")
        #print("Encoding: %s" % encoding)
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

# This object manages the correlation between multiplexes of different interfaces
class MuxManager:
    def __init__(self, dbfile):
        self.con=sqlite3.connect(dbfile)
        return
    def lookup_muxid(self, cmux, user, local_uuid="", global_uuid=None):
        print("lookup_muxid: %s %s %s" %(user, local_uuid, global_uuid))
        mux_id=self.lookup_muxid_(cmux)
        if not global_uuid is None:
            cur=self.con.cursor()
            cur.execute("UPDATE multiplexes SET global_id=? WHERE mux_id=?", [global_uuid, mux_id])
            self.con.commit()
        print("lookup_muxid: user: %s  %s<=>%s" %(user, local_uuid, mux_id))
        self.update_services(mux_id, cmux)
        return mux_id
    def lookup_muxid_(self, cmux):
        mdata={}
        for f in ("frequency", "delsys", "orbital", "polarisation", "tsid", "onid", "symbolrate"):
            if f in cmux:
                if f=="symbolrate":
                    mdata[f]=float(cmux[f])/1000
                else:
                    mdata[f]=cmux[f]
            else:
                mdata[f]=0
        if "bandwidth" in cmux:
            mdata["symbolrate"]=8000000 #Shortcut for DVB-T(2)/C
        cur=self.con.cursor()
        res=cur.execute("SELECT mux_id, abs(frequency-?) AS diff FROM multiplexes WHERE delsys=? AND orbital=? AND polarisation=? AND tsid=? AND onid=? AND diff<srate/10 ORDER BY diff",
                        [mdata["frequency"], mdata["delsys"], mdata["orbital"], mdata["polarisation"], mdata["tsid"], mdata["onid"]])
        data=res.fetchall()
        if len(data)>0:
            return data[0][0]
        cur.execute("INSERT INTO multiplexes (frequency, srate, delsys, orbital, polarisation, tsid, onid) values (?,?,?,?,?,?,?)",
                    [mdata["frequency"], mdata["symbolrate"], mdata["delsys"], mdata["orbital"], mdata["polarisation"], mdata["tsid"], mdata["onid"]])
        new_id=cur.lastrowid
        #FIXME!!!# Add services if they don't exist
        # update_service_mapping for all pids with teletext        
        self.con.commit()
        return new_id
    def lookup_service(self, mux_id, pid):
        print("lookup_service %s %s" % (mux_id, pid))
        mux_id_int=int(mux_id)
        pid_int=int(pid)
        cur=self.con.cursor()
        res=cur.execute("SELECT service_name from service_mapper where mux_id=? and pid=?", [mux_id_int, pid_int])
        data=res.fetchall()
        if len(data)>0:
            return data[0][0]
        return "___%s_%s" % (mux_id, pid)
    def update_services(self, mux_id, cmux):
        if not "services" in cmux:
            print("Mux %s has no services" %mux_id)
            return
        for sn in cmux["services"]:
            service=cmux["services"][sn]
            if not "stream" in service:
                continue
            svcname=""
            if "svcname" in service:
                svcname = service["svcname"]
            for stream in service["stream"]:
                if "type" in stream and stream["type"]=="TELETEXT":
                    print("Found pid %si for %s" % (stream["pid"], svcname))
                    self.update_service_mapping(mux_id, stream["pid"], None, None, None, svcname) 

    def set_service_mapping(self, mux_id, pid, service_name, svcname, header=None, size=0):
        mux_id_int=int(mux_id)
        pid_int=int(pid)
        cur=self.con.cursor()
        if header is None:
            cur.execute("insert into service_mapper (mux_id, pid, service_name, svcname) values (?,?,?,? ) on conflict(mux_id,pid) do update set service_name=?, svcname=?", 
                        [mux_id_int, pid_int, service_name, svcname, service_name, svcname])
        else:
            last_capture=time.time()
            cur.execute("insert into service_mapper (mux_id, pid, service_name, last_capture, last_size, last_header, svcname) values (?,?,?,?,?,?) on conflict(mux_id,pid) do update set service_name=?, svcname=?, last_capture=?, last_size=?, last_header=?", 
                        [mux_id_int, pid_int, service_name, svcname, last_capture, size, header,
                         service_name, svcname, last_capture, size, header])
        new_id=cur.lastrowid
        self.con.commit()
        return new_id
    def update_service_mapping(self, mux_id, pid, capture_time, header, size, svcname=""):
        print("update_service_mapping %s %s %s %s %s" % (mux_id, pid, capture_time, header, size))
        if mux_id is None:
            return
        if pid is None:
            return
        mux_id_int=int(mux_id)
        pid_int=int(pid)
        cur=self.con.cursor()
        res=cur.execute("select sm_id from service_mapper where mux_id=? and pid=?", [mux_id_int, pid_int])
        data=res.fetchall()
        if len(data)==0: #No entry yet
            if capture_time is None:
                print("New service %s mux_id: %s, pid: %s" % (svcname, mux_id, pid))
                cur.execute("insert into service_mapper (mux_id, pid, service_name, svcname) values (?,?,?,?)", 
                            [mux_id_int, pid_int, "___%s_%s" % (mux_id_int, pid_int), svcname])
            else:
                cur.execute("insert into service_mapper (mux_id, pid, last_capture, last_size, last_header, service_name, svcname) values (?,?,?,?,?,?,?)", 
                            [mux_id_int, pid_int, capture_time, size, header, "___%s_%s" % (mux_id_int, pid_int), svcname])
        else: #Update entry
            if not capture_time is None:
                cur.execute("update service_mapper set last_capture=?, last_size=?, last_header=? WHERE mux_id=? AND pid=?",  
                            [capture_time, size, header, mux_id_int, pid_int])
        self.con.commit()
    def lock_multiplex(self, mux_id, user, timeout):
        print("lock_multiplex user: %s, mux_id: %s" % (user, mux_id))
        mux_id_int=int(mux_id)
        lock_end=round(time.time()+timeout)
        cur=self.con.cursor()
        cur.execute("INSERT INTO mux_locks (mux_id, user_name, locked_until) values (?,?,?) ON CONFLICT (mux_id) DO UPDATE SET user_name=?, locked_until=?",[mux_id_int, user, lock_end, user, lock_end])
        cur.execute("UPDATE multiplexes SET last_seen=? where mux_id=?", [round(time.time()), mux_id_int])
        self.con.commit()
    def lock_multiplex_update(self, user, lmux, timeout):
        #print("lock_multiplex_update user: %s, lmux: %s" % (user, lmux))
        lock_end=round(time.time()+timeout)
        cur=self.con.cursor()
        cur.execute("UPDATE mux_locks SET locked_until=? where mux_id=(select mux_id from mux_cor where user_name=? AND local_uuid=?)", [lock_end,user, lmux])
        cur.execute("DELETE from mux_locks where locked_until<?", [round(time.time())])
        self.con.commit()
    def unlock_multiplex(self, mux_id):
        print("unlock_multiples: %s" % (mux_id))
        mux_id_int=int(mux_id)
        cur=self.con.cursor()
        cur.execute("DELETE FROM mux_locks WHERE mux_id=?",[mux_id_int])
        cur.execute("UPDATE multiplexes SET last_seen=? where mux_id=?", [time.time(), mux_id_int])
        self.con.commit()

    def get_muxid_from_luuid(self, user, luuid):
        cur=self.con.cursor()
        res=cur.execute("SELECT mux_id FROM mux_cor WHERE user_name=? AND local_uuid=?", [user, luuid])
        data=res.fetchall()
        if len(data)>0:
            return data[0][0]
        else:
            return None

    def get_luuid_from_muxid(self, user, mux_id):
        cur=self.con.cursor()
        res=cur.execute("SELECT local_uuid FROM mux_cor WHERE user_name=? AND mux_id=?", [user, mux_id])
        data=res.fetchall()
        if len(data)>0:
            return data[0][0]
        else:
            return None
    def get_muxid_from_guuid(self, user, guuid):
        cur=self.con.cursor()
        res=cur.execute("SELECT mux_id from multiplexes WHERE global_id=?", [guuid])
        data=res.fetchall()
        if len(data)>0:
            return data[0][0]
        else:
            return None
    def update_muxes_for_user(self, user, muxes):
        update_id="%s-%s" % (time.asctime(), random.randint(0,99999999))
        cur=self.con.cursor()
        for mux in muxes:
            mux_id=self.lookup_muxid(muxes[mux], user, local_uuid="", global_uuid=None)
            mux_uuid=mux
            res=cur.execute("SELECT corr_id FROM mux_cor WHERE mux_id=? AND user_name=?", [mux_id, mux_uuid])
            data=res.fetchall()
            if len(data)>0:
                cur.execute("UPDATE mux_cor SET local_uuid=?, update_id=?", [mux_uuid, update_id])
            else:
                cur.execute("INSERT INTO mux_cor (mux_id, user_name, local_uuid, update_id) VALUES (?, ?, ?, ?)", [mux_id, user, mux_uuid, update_id])
            self.con.commit()
        cur.execute("DELETE FROM mux_cor WHERE user_name=? AND update_id!=?", [user, update_id])
        self.con.commit()

    def get_mux(self, user):
        print("get_mux: %s" %(user))
        cur=self.con.cursor()
        res=cur.execute("""WITH unlocked_service_mapper AS (
    SELECT sm.*
    FROM service_mapper AS sm
    WHERE sm.service_name <> 'BLOCK'
      AND NOT EXISTS (
          SELECT 1
          FROM mux_locks AS ml
          WHERE ml.mux_id = sm.mux_id
            AND ml.locked_until > unixepoch()
      )
),
service_latest AS (
    SELECT
        service_name,
        MAX(COALESCE(last_capture, 0)) AS last_capture_global
    FROM unlocked_service_mapper
    GROUP BY service_name
),
mux_order AS (
    SELECT
        sm.mux_id,
        MIN(sl.last_capture_global) AS smallest_service_capture
    FROM unlocked_service_mapper AS sm
    JOIN service_latest AS sl
      ON sl.service_name = sm.service_name
    GROUP BY sm.mux_id
)
SELECT
    mo.mux_id,
    mo.smallest_service_capture,
    COALESCE(mx.last_seen, 0) AS mux_last_seen,
    CASE
        WHEN COALESCE(mx.last_seen, 0) > mo.smallest_service_capture
        THEN COALESCE(mx.last_seen, 0)
        ELSE mo.smallest_service_capture
    END AS effective_capture
FROM mux_order AS mo
JOIN multiplexes AS mx
  ON mx.mux_id = mo.mux_id
WHERE mo.mux_id IN (SELECT mux_id FROM mux_cor WHERE user_name=? )    
ORDER BY
    effective_capture ASC;
    """, [user])




        data=res.fetchall()
        if len(data)>0:
            return data[0][0]
        else:
            return None





class TeletextServer:
    current_muxes={}
    def __init__(self, path):
        self.basic_config=ConfigFileHandler(path)
        self.min_intervall=self.basic_config.get("min_intervall")
        var_directory=self.basic_config.get("var_dir")
        print("var_directory: %s" % var_directory)
        if var_directory is None:
            var_directory="/var/spool/teletext_server"
        self.users=ConfigFileHandler(var_directory+"/users.json")
        self.muxmanager=MuxManager("db/db.sqlite")
        self.out_dir=self.basic_config.get("out_dir")
        if self.out_dir is None:
            print("Please set out_dir")
            return False


    def get_http_port(self):
        return self.basic_config.get("listen_port")

    def upload(self, user, body):
        local_mux=body["mux"]
        capture_time=body["capture_time"]

        mux_id=self.muxmanager.get_muxid_from_luuid(user, local_mux)
        if mux_id is None:
            print("Mux %s not found, rejecting" %(local_mux))
            return "BAD"
        print("mux_id: %s"%(mux_id))
        self.muxmanager.unlock_multiplex(mux_id)
        for pid in body["pids"]:
            capture=body["pids"][pid]
            svcname=""
            if "svcnames" in body:
                if pid in body["svcnames"]:
                    svcname=body["svcnames"][pid]
                    print("svcname: %s" % (svcname))
            self.muxmanager.update_service_mapping(mux_id, pid, capture_time, capture["header"], len(capture["content"]), svcname)
            service_name=self.muxmanager.lookup_service(mux_id, pid)
            print("New mux lookup %s %s => %s" % (mux_id, pid, service_name))
        
            capture=body["pids"][pid]
            length=len(capture["content"])

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
        return "OK"

    def get_mux(self, user, body):
        mux_id=self.muxmanager.get_mux(user)
        if mux_id is None:
            return "BAD"

        luuid=self.muxmanager.get_luuid_from_muxid(user, mux_id)
        if luuid is None:
            return "BAD"

        print("Found Mux: %s => %s" % (mux_id, luuid))
        result={}
        result["mux"]=luuid

        result["mux_id"]=mux_id
        self.muxmanager.lock_multiplex(mux_id, user, 60)
        print("got mux %s" % mux_id)
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

        for m in sorted(mux_list, key=operator.itemgetter(0)):
            lu=m[0]
            sn=m[1]
            locked=m[2]
            header=m[3]
            lu_string="never"
            if lu>0:
                lu_string=datetime.timedelta(seconds=(round((time.time()-lu))))
            self.writeRow(wfile, [sn, lu_string, locked, header])
        
        wfile.write(b"</table>")
        wfile.write(b"<pre>")
        wfile.write(self.list_all_muxes().encode("UTF-8"))
        wfile.write(b"</pre>")
        wfile.write(b"</body>")
        return
    def post_muxes(self, user, muxes):
        self.muxmanager.update_muxes_for_user(user, muxes)
        for luuid in muxes:
            lmux=muxes[luuid]
            self.muxmanager.lookup_muxid(lmux, user, luuid)
        return True
    def status(self, user, body):
        print("Status: %s" % body)
        duration=body["duration"]
        muxes=body["muxes"]
        gmuxes=[]
        for mux in muxes:
            local_mux=mux
            self.muxmanager.lock_multiplex_update(user, local_mux, duration)
        return True
    def progress_bar(self, fraction, width=70):
        if (fraction>1):
            fraction=1
        w=round(width*fraction*8)
        cw=int(w/8)
        cp=w%8
        blocks=" ▏▎▍▌▋▊▉"
        return "━"+(("█"*(cw-1)))+blocks[cp]+("."*(width-cw))+"━"
    def list_current_mux(self, user, mux):
        lines=[]
        lines.append("Mux: %s User: %s" % (mux["id"], user))
        if "last_attempt" in mux and "captures" in mux and len(mux["captures"])>0:
            max_time=0
            for c in mux["captures"]:
                if c[1]>max_time:
                    max_time=c[1]
            start=mux["last_attempt"]
            end=start+max_time
            if max_time>1:
                fraction=(time.time()-start)/max_time
                lines.append("  " +(self.progress_bar(fraction)))
        if "text_services" in mux:
            ts=mux["text_services"]
            services=[]
            for s in ts:
                sn=ts[s]["service_name"]
                if not sn in services:
                    services.append(str(sn))
            lines.append("    "+(",".join(services)))
        lines.append("")
        return "\r\n".join(lines)
    def list_all_muxes(self):
        mux_list=[]
        for user in self.current_muxes:
            user_muxes=self.current_muxes[user]
            for mux in user_muxes:
                max_time=0
                if "captures" in mux:
                    for c in mux["captures"]:
                        if c[1]>max_time:
                            max_time=c[1]
                start=mux["last_attempt"]
                end=start+max_time
                if max_time>1:
                    fraction=(time.time()-start)/max_time
                else:
                    fraction=0
                mux_list.append([fraction, user, mux])
        mux_sorted=sorted(mux_list)
        s=""
        for m in mux_sorted:
            s=s+self.list_current_mux(m[1], m[2])
        return s



teletext_server=TeletextServer("/etc/teletext_server.json")

with HTTPServer(('', teletext_server.get_http_port()), handler) as server:
    server.serve_forever()


