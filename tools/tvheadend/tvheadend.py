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

def set_last_used(muxname):
    lockfile=lockdir+"/"+muxname+".last_used"
    f=open(lockfile, "w")
    f.write(str(time.time()))
    f.close()

def get_last_used_age(muxname):
    lockfile=lockdir+"/"+muxname+".last_used"
    if not os.path.exists(lockfile):
        return 1e10
    f=open(lockfile, "r")
    t=f.read()
    f.close()
    try:
        return time.time()-float(t)
    except:
        os.remove(lockfile)
        return 1e10

def use_mux(mux):
    if mux['enabled']==0:
        return False
    if orbital is not None:
        if 'orbital' not in mux:
            if mux["orbital"]!=orbital:
                return False
    return True

translations_changes=0
translations=None

def load_translations():
    global translations
    global translations_changes
    try:
       with open('translations.json') as t_file:
           translations=json.load(t_file)
    except:
        translations=json.loads('{"blurb": "blurb"}')
    translations_changes=0
    return translations

def save_translations():
    global translations
    global translations_changes
    print("save_translations", translations_changes)
    if translations_changes>0:
        with open('translations.json','w') as t_file:
            json.dump(translations,fp=t_file,indent=4, sort_keys=True)
        translations_changes=0

def translate(srvname,position):
    global translations
    global translations_changes
    if srvname+"_"+position in translations:
        x=translations[srvname+"_"+position]
        if len(x)>1:
            return x
    if srvname in translations:
        x=translations[srvname]
        if len(x)>1:
            return x
    translations[srvname+"_"+position]=""
    translations_changes=translations_changes+1

    return "___"+srvname

def pos_to_num(pos):
    if pos.startswith("DVB"):
        return 0
    if pos.endswith("E"):
        s=str.rstrip(pos,"E")
        return float(s)
    if pos.endswith("W"):
        s=str.rstrip(pos,"W")
        return -float(s)
    return 0

base_url="http://"+tvheadend_ip+":"+tvheadend_port+"/"
base_url_auth="http://"+tvheadend_user+":"+tvheadend_pass+"@"+tvheadend_ip+":"+tvheadend_port+"/"

try:
    with open('blockpids.json') as t_file:
        blockpids=json.load(t_file)
except:
    blockpids={}

url=base_url+"api/raw/export?class=dvb_mux"
req=requests.get(url, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
req.encoding="UTF-8"

if req.status_code != 200:
    print("Couldn't get multiplex list. Maybe user has insufficient rights. Code: ", req.status_code)
    exit()

muxes=json.loads(req.text)

filtered_mux_list=[]

for mux in muxes:
    mux_uuid=mux["uuid"]
    if not use_mux(mux):
        continue
    age=get_last_used_age(mux_uuid)
    position=mux["delsys"]
    if "orbital" in mux:
        position=mux["orbital"]
    if orbital is not None:
        if not position in orbital.split(","):
            continue
    filtered_mux_list.append([mux_uuid,age,position])

temp_mux_list=sorted(filtered_mux_list, key=lambda d:d[1],reverse=True)
sorted_mux_list=sorted(temp_mux_list, key=lambda d:pos_to_num(d[2]))


all_mux_pids={}
for fmux in sorted_mux_list:
    fmuxname=fmux[0]
    print("Multiplex:", fmuxname, "age:", fmux[1], "position:", fmux[2])
    clean_locks()
    #Check for lock
    if not get_lock(fmuxname):
        print("Couldn't get lock")
        continue
    req=requests.get(base_url+"api/raw/export?uuid="+fmuxname, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
    mux=json.loads(req.text)[0]
    mux_uuid=mux["uuid"]
    if mux_uuid!=fmuxname:
        print("Didn't return correct mux", mux_uuid, fmuxname)
        exit()
    
    set_last_used(mux_uuid)

    load_translations()

    mux_pids=[] #Used to build service list in the end and to find the names for the outgoing directories
    pids=[] #Used to determine PIDs to ask tvheadend for
    for service in mux['services']:
        req=requests.get(base_url+"api/raw/export?uuid="+service, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
        channel=json.loads(req.text)
        srvname=service
        if ('svcname' in channel[0]):
            srvname=channel[0]['svcname']
        srvname=srvname.upper().replace(" HD","").replace(" ","").replace("/","").replace("$","").replace(":","_")
        for stream in channel[0]['stream']:
            if stream['type']=="TELETEXT":
                #Look up service name
                srvname=translate(srvname,fmux[2])
                if not stream['pid'] in pids:
                    pids.append(stream['pid'])
                mux_pids.append([srvname,stream['pid']]);
                if mux_uuid in blockpids:
                    if stream['pid'] in blockpids[mux["uuid"]]:
                        pids.remove(stream['pid'])
                        mux_pids.remove([srvname,stream['pid']]);
    save_translations()
    
    if len(pids)>0:
        all_mux_pids[mux["uuid"]+'-'+fmux[2]]=mux_pids
        url=base_url_auth+"stream/mux/"+mux_uuid+"?pids="+",".join(map(str,pids))
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


