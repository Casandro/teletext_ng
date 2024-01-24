#!/usr/bin/python3 

import os
import time
import requests
from requests.auth import HTTPDigestAuth
import json
import datetime
import time
import random


tvheadend_ip="127.0.0.1"
tvheadend_port="9981"
tvheadend_user="teletext"
tvheadend_pass="teletext"

if "TVHEADEND_IP" in os.environ:
    tvheadend_ip=os.environ["TVHEADEND_IP"]

if "TVHEADEND_PORT" in os.environ:
    tvheadend_port=os.environ["TVHEADEND_PORT"]

if "TVHEADEND_USER" in os.environ:
    tvheadend_user=os.environ["TVHEADEND_USER"]

if "TVHEADEND_PASS" in os.environ:
    tvheadend_pass=os.environ["TVHEADEND_PASS"]

orbital=None
if "ORBITAL" in os.environ:
    orbital=os.environ["ORBITAL"]

no_stream=0
if "NO_STREAM" in os.environ:
    no_stream=1

outdir="outdir"
if "OUTDIR" in os.environ:
    outdir=os.environ["OUTDIR"]

tmpdir="/tmp/"
if "TMPDIR" in os.environ:
    tmpdir=os.environ["TMPDIR"]

lockdir="lock"
if "LOCKDIR" in os.environ:
    lockdir=os.environ["LOCKDIR"]
os.makedirs(lockdir, exist_ok=True)


def clean_locks():
    with os.scandir(lockdir) as it:
        for f in it:
            if f.is_file():
                if not f.path.endswith(".lock"):
                    continue
                mtime=f.stat().st_mtime
                age=time.time()-mtime
                if age>7200:
                    os.remove(f.path)
                    print("Removed statle lock for", f.name, age)

def get_lock(muxname):
    clean_locks()
    lockfile=lockdir+"/"+muxname+".lock"
    if os.path.exists(lockfile):
        return False
    rnd=str(random.randrange(999999999))
    f=open(lockfile, "w")
    f.write(rnd)
    f.close()
    f=open(lockfile, "r")
    rd=f.read()
    f.close()
    if rnd==rd:
        return True
    return False

def remove_lock(muxname):
    os.remove(lockdir+"/"+muxname+".lock")


base_url="http://"+tvheadend_ip+":"+tvheadend_port+"/"
base_url_auth="http://"+tvheadend_user+":"+tvheadend_pass+"@"+tvheadend_ip+":"+tvheadend_port+"/"

url=base_url+"api/raw/export?class=dvb_mux"


try:
    with open('blockpids.json') as t_file:
        blockpids=json.load(t_file)
except:
    blockpids={}

req=requests.get(url, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
req.encoding="UTF-8"

if req.status_code != 200:
    print("Couldn't get multiplex list. Maybe user has insufficient rights. Code: ", req.status_code)
    exit()

muxes=json.loads(req.text)

all_mux_pids={}
for mux in muxes:
    mux_pids=[]
    mux_uuid=mux["uuid"]
    clean_locks()

    #Check if mux is enabled
    if mux['enabled']==0:
        continue
    #Check for lock
    if not get_lock(mux_uuid):
        continue
    #Check for correct orbital
    if orbital is not None:
        if 'orbital' not in mux:
            continue
        if mux["orbital"]!=orbital:
            continue
    try:
       with open('translations.json') as t_file:
           translations=json.load(t_file)
    except:
        translations=json.loads('{"blurb": "blurb"}')

    changes=0
    for service in mux['services']:
        req=requests.get(base_url+"api/raw/export?uuid="+service, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
        channel=json.loads(req.text)
        srvname=service
        if ('svcname' in channel[0]):
            srvname=channel[0]['svcname']
        srvname=srvname.upper().replace(" HD","").replace(" ","").replace("/","").replace("$","").replace(":","_")
        pids=[]
        for stream in channel[0]['stream']:
            if stream['type']=="TELETEXT":
                #Look up service name
                try:
                    srvname_=translations[srvname]
                    if len(srvname_)>3:
                        srvname=srvname_
                except:
                    translations[srvname]=""
                    changes=changes+1
                    srvname="___"+srvname
                if len(srvname)<2:
                    srvname="___"+service
                mux_pids.append([srvname,stream['pid']]);
                pids.append(stream['pid'])
                if mux_uuid in blockpids:
                    print(blockpids[mux_uuid])
                    if stream['pid'] in blockpids[mux["uuid"]]:
                        pids.remove(stream['pid'])
                        mux_pids.remove([srvname,stream['pid']]);
    if changes>0:
        with open('translations.json','w') as t_file:
            json.dump(translations,fp=t_file,indent=4, sort_keys=True)
    if len(mux_pids)>0:
        all_mux_pids[mux["uuid"]]=mux_pids
        pids=""
        for stream in mux_pids:
            if len(pids)>0:
                pids=pids+","
            pids=pids+str(stream[1]);
        url=base_url_auth+"stream/mux/"+mux_uuid+"?pids="+pids
        print(url)
        if no_stream == 0:
            out_tmp=tmpdir+"/"+mux_uuid
            os.makedirs(out_tmp, exist_ok=True)
            date_prefix=datetime.datetime.now().utcnow().isoformat(timespec="seconds")+"+00:00"
            os.system("timeout 7200 wget -o /dev/null -O - "+url+" | ../../src/ts_teletext --ts --stop -p"+out_tmp+"/"+date_prefix+"-")
            files=os.listdir(out_tmp)
            for service in mux_pids:
                name=service[0]
                os.makedirs(outdir+"/"+name, exist_ok=True)
                pid=service[1]
                pid_suffix="-0x"+"{:04x}".format(pid)+".zip"
                for f in files:
                    if f.endswith(pid_suffix):
                        os.rename(out_tmp+"/"+f, outdir+"/"+name+"/"+f)
                        files.remove(f)
    remove_lock(mux_uuid)

with open('all_mux_pids.json','w') as t_file:
    json.dump(all_mux_pids,fp=t_file,indent=4, sort_keys=True)


