#!/usr/bin/python3 

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

no_orbital=None
if "NO_ORBITAL" in os.environ:
    no_orbital=os.environ["NO_ORBITAL"]

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

ts_teletext="../../src/ts_teletext"
if not os.path.exists(ts_teletext):
    ts_teletext="ts_teletext"
if "TS_TELETEXT" in os.environ:
    ts_teletext=os.environ["TS_TELETEXT"]

statusfile="/tmp/"+str(randint(100,999))
if "STATUSFILE" in os.environ:
    statusfile=os.environ["STATUSFILE"]


limit=None
if "LIMIT" in os.environ:
    limit=int(os.environ["LIMIT"])

sort_sat=0
if "SORTSATS" in os.environ:
    sort_sat=int(os.environ["SORTSATS"])

rsync_target=None
if "RSYNC_TARGET" in os.environ:
    rsync_target=os.environ["RSYNC_TARGET"]

rsync_remove=0
if "RSYNC_REMOVE" in os.environ:
    rsync_remove=1


timeout=20
if "TIMEOUT" in os.environ:
    timeout=int(os.environ["TIMEOUT"])

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
                    log("Removed stale lock for "+ f.name+ str(age))

def probe_lock(muxname):
    clean_locks()
    lockfile=lockdir+"/"+muxname+".lock"
    return os.path.exists(lockfile)

def get_lock(muxname):
    clean_locks()
    try:
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
    except:
        return False
    return False

def remove_lock(muxname):
    try:
        os.remove(lockdir+"/"+muxname+".lock")
    except:
        return


def set_last_used(muxname):
    t=int(time.time())
    lockfile=lockdir+"/"+muxname+".last_used"
    f=open(lockfile, "w")
    f.write(str(t))
    f.close()

def get_last_used(muxname):
    lockfile=lockdir+"/"+muxname+".last_used"
    if not os.path.exists(lockfile):
        return 0
    f=open(lockfile, "r")
    t=f.read()
    f.close()
    try:
        return float(t)
    except:
        os.remove(lockfile)
        return 1e10

def use_mux(mux):
    if mux['enabled']==0:
        return False
    if orbital is not None:
        if 'delsys' in mux:
            if mux["delsys"]=="DVB-T2":
                return False
        if 'orbital' in mux:
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
    if translations_changes>0:
        with open('translations.json','w') as t_file:
            json.dump(translations,fp=t_file,indent=4, sort_keys=True)
        translations_changes=0

def translate(srvname,position,muxname):
    global translations
    global translations_changes
    if srvname=="BLOCK":
        return "BLOCK"
    if srvname=="___BLOCK":
        return "BLOCK"
    if srvname=="______BLOCK":
        return "BLOCK"
    if srvname+"_"+muxname in translations:
        x=translations[srvname+"_"+muxname]
        if len(x)>1:
            return x
    if srvname+"_"+position in translations:
        x=translations[srvname+"_"+position]
        if len(x)>1:
            return x
    if srvname in translations:
        x=translations[srvname]
        if len(x)>1:
            return x
    translations[srvname+"_"+muxname]=""
    translations_changes=translations_changes+1
    return "___"+srvname+"_"+muxname

#Delete empty translation
def delete_translation(srvname,position,muxname):
    global translations
    global translations_changes
    tr=translate(srvname,position,muxname)
    if tr=="BLOCK":
        return
    if not tr.startswith("___"):
        return
    key=srvname+"_"+position
    if key in translations:
        del translations[key]
    key=srvname+"_"+muxname
    if key in translations:
        del translations[key]

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

def update_last_updates():
    global muxes
    global muxes_to_remove
    log_start("Update last updates cnt="+str(len(muxes)))
    cnt=0
    for mux in muxes:
        oldest_service=time.time()+3600
        for text in mux["text_services"]:
            if probe_lock(text[0]):
                continue
            sdate=get_last_used(text[0])
            if (sdate<oldest_service):
                oldest_service=sdate
        muxdate=oldest_service #Disable mux date for a while get_last_used(mux["uuid"])
        if (muxdate>oldest_service):
            #Mux was recieved after oldest service
            last_update=muxdate
        else:
            #services were received later than the mux
            last_update=oldest_service
        index=muxes.index(mux)
        if "last_update" in muxes[index]:
            if muxes[index]["last_update"]<last_update:
                muxes_to_remove.append(mux)
                log("Mux "+mux["mux_name"]+ " updated => removing")
        muxes[muxes.index(mux)]["last_update"]=last_update
        cnt=cnt+1
    log_end(str(cnt)+" updates")

def format_last_used(last_used):
    if last_used==0:
        return "never"
    return str(format_delta(time.time()-last_used))+" ago"


def format_delta(delta):
    a=abs(delta) 
    if a>60:
        return str(datetime.timedelta(seconds=int(a)))
    if a>1:
        return "{:0.5}".format(delta)+"s"
    if a>0.001:
        return "{:0.5}".format(delta*1000)+"ms"
    return "{:0.5}".format(delta*1000000)+"µs"


log_time_stack=[]

def log_indent():
    global log_time_stack
    l=len(log_time_stack)
    return "│ "*l

def log_start(text):
    global log_time_stack
    indent=log_indent()
    log_time_stack.append(time.time())
    print(indent+"┌"+text)

def log(text):
    global log_time_stack
    indent=log_indent()
    print(indent+" "+text)

def log_end(text):
    global log_time_stack
    d=time.time()-log_time_stack.pop()
    indent=log_indent()
    if text=="":
        text="done"
    print(indent+"└▶"+format_delta(d)+" "+text);


def dump_muxes(m):
    log_start("summing up inputs")
    si={}
    for mux in m:
        input=mux["switch_input"]
        if input in si:
            si[input]=si[input]+1;
        else:
            si[input]=1
    lines=[]
    for h in si:
        lines.append("{:10} {:4} ".format(h,si[h]))
    lines_sorted=sorted(lines)
    for l in lines_sorted:
        log(l)
    log_end("")
    log_start("summing up orbitals")
    si={}
    va={}
    for mux in m:
        if not "orbital" in mux:
            continue
        input=mux["orbital"]
        if input in si:
            si[input]=si[input]+1;
            va[input]=va[input]+mux["value"]
        else:
            si[input]=1
            va[input]=mux["value"]
    lines=[]
    cnt_sum=0
    val_sum=0
    for h in si:
        cnt_sum=cnt_sum+si[h]
        val_sum=val_sum+va[h]
    for h in si:
        lines.append("{:10} {:4} {:7.5}".format(h,si[h],round(va[h]*10)/10)+" "+str(round(si[h]/cnt_sum*1000)/10)+"% "+str(round(va[h]/val_sum*1000)/10)+"%")
    lines_sorted=sorted(lines)
    for l in lines_sorted:
        log(l)
    log_end("")


base_url="http://"+tvheadend_ip+":"+tvheadend_port+"/"
base_url_auth="http://"+tvheadend_user+":"+tvheadend_pass+"@"+tvheadend_ip+":"+tvheadend_port+"/"

log_start("Loading muxes from tvheadend");
url=base_url+"api/raw/export?class=dvb_mux"
req=requests.get(url, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
req.encoding="UTF-8"

if req.status_code != 200:
    print("Couldn't get multiplex list. Maybe user has insufficient rights. Code: ", req.status_code)
    exit()

muxes=json.loads(req.text)
log_end(str(len(muxes))+" muxes loaded")


log_start("loading and hashing services")
log_start("Loading services from tvheadend");
url=base_url+"api/raw/export?class=service"
req=requests.get(url, auth=HTTPDigestAuth(tvheadend_user, tvheadend_pass))
req.encoding="UTF-8"

if req.status_code != 200:
    print("Couldn't get service list. Maybe user has insufficient rights. Code: ", req.status_code)
    exit()

services=json.loads(req.text)
log_end(str(len(services))+" services")
log_start("moving to hashmap")
service_hash={}
for service in services:
    muxname=service["uuid"]
    service_hash[muxname]=service
log_end("")
log_end("")

#annotate_and_filter_muxes
mux_filtered=[]
load_translations()
log_start("filter through "+str(len(muxes))+ " multiplexes")
total_services=0
disappeared_services=0
services_left=0
for mux in muxes:
    if "orbital" in mux and (not orbital is None):
        if not mux["orbital"] in orbital.split(","):
            continue
    if "orbital" in mux and (not no_orbital is None):
        if mux["orbital"] in no_orbital.split(","):
            continue
    if (not orbital is None):
        if mux["delsys"]=="DVB-T2":
            continue
    mux_name=""
    position=""
    switch_input=""
    if "delsys" in mux:
        mux_name=mux_name+mux["delsys"]+"-"
        position=mux["delsys"]
    if "frequency" in mux:
        mux_name=mux_name+str(mux["frequency"]);
        if mux["delsys"].startswith("DVB-T"):
            switch_input="T"
        elif mux["frequency"]<11700000:
            switch_input="Lo"
        else:
            switch_input="Hi"
    if "polarisation" in mux:
        mux_name=mux_name+mux["polarisation"]
        switch_input=switch_input+"-"+mux["polarisation"]
    if "orbital" in mux:
        mux_name=mux_name+"-"+mux["orbital"]
        position=mux["orbital"]
        switch_input=mux["orbital"]+"-"+switch_input
    mux["position"]=position
    mux["mux_name"]=mux_name
    mux["switch_input"]=switch_input
    if not "scan_last" in mux:
        continue
    mux_scan_last=mux["scan_last"]
    scnt=0
    text_services=[]
    pid_list={}
    if "services" in mux and len(mux["services"])>0:
        for suuid in mux["services"]:
            total_services=total_services+1
            service=service_hash[suuid]
            if not "last_seen" in service:
                log(mux_name+" Service "+suuid+" never seen -> ignoring");
                continue
            sname=suuid
            if "svcname" in service:
                sname=service["svcname"]
            last_seen=service["last_seen"]
            if last_seen+3600<mux_scan_last and last_seen!=0:
                disappeared_services=disappeared_services+1
                continue
            last_seen_age=int(time.time())-last_seen
            if last_seen_age>(24*2)*3600:
                disappeared_services=disappeared_services+1
                continue 
            tcnt=0;
            tstreams=[]
            for stream in service["stream"]:
                if stream['type']=="TELETEXT":
                    if stream["pid"] in pid_list:
                        continue
                    tstreams.append(stream["pid"])
                    tcnt=tcnt+1
            if len(tstreams)>0:
                sname=service["uuid"]
                if ('sid' in service):
                    sname="SID-"+str(service['sid'])
                if ('svcname' in service):
                    sname=service['svcname']
                osrvname=sname.upper().replace(" HD","").replace(" ","").replace("/","").replace("$","").replace(":","_")
                #Look up service name
                srvname=translate(osrvname,position,mux_name)
                if srvname!="BLOCK":
                    for x in tstreams:
                        text_services.append([srvname,x])
                        pid_list[x]=srvname
                    scnt=scnt+1
                services_left=services_left+1
    if len(text_services)>0:
        mux["text_services"]=text_services
        #log(mux_name+str(mux["text_services"]))
        mux_filtered.append(mux)
save_translations()
muxes=mux_filtered
log_end(str(len(muxes))+" muxes left; "+str(services_left)+" out of "+str(total_services)+" services remaining; "+str(disappeared_services)+" services disappeared")

log_start("Evaluating Muxes")
log_start("Finding transponders for each mux")
service_muxes={}
for mux in muxes:
    mux["value"]=0
    for text_service in mux["text_services"]:
        service_name=text_service[0]
        if service_name in service_muxes:
            if not (mux in service_muxes[service_name]): 
                service_muxes[service_name].append(mux)
        else:
            service_muxes[service_name]=[]
            service_muxes[service_name].append(mux)
log_end("")
log_start("Evaluate Muxes")
for service in service_muxes:
    cnt=len(service_muxes[service])
    if cnt==0:
        continue
    v=1/cnt;
    for m in service_muxes[service]:
        m["value"]=m["value"]+v;
log_end("")
log_start("Printing muxes and their evaluations")
f=open("/tmp/mux_values.txt","w")
for m in muxes:
    n=""
    for s in m["text_services"]:
        n=n+" "+s[0]
    log("{:0.5}".format(m["value"])+"\t"+m["mux_name"]+"\t"+n)
    f.write("{:0.5}".format(m["value"])+"\t"+m["mux_name"]+"\t"+n+"\n")
f.close();
log_end("")
log_end("")

dump_muxes(muxes)

if statusfile is None:
    sfile=""
else:
    sfile="-s"+statusfile

muxes_to_remove=[]
log_start("Randomly removing less valuable muxes")
cnt=0
for m in muxes:
    if m["value"]<random.random()*0.25:
        muxes_to_remove.append(m)
        cnt=cnt+1
log_end(str(cnt)+" muxes marked for deletion")

while len(muxes)>0:

    update_last_updates()
    
    log_start("removing muxes from work list")
    for mux in muxes_to_remove:
        if mux in muxes:
            log(mux["mux_name"]+" {:0.5}".format(mux["value"]))
            muxes.remove(mux)
    muxes_to_remove=[]
    log_end("")

    temp_mux_list=sorted(muxes, key=lambda d:d["last_update"]-d["value"]*120)
    if sort_sat!=0:
        muxes=sorted(temp_mux_list, key=lambda d:pos_to_num(d[2]))
    else:
        muxes=temp_mux_list


    log_start("processing "+str(len(muxes))+" muxes")
    for mux in muxes:
        time.sleep(1)
        mux_uuid=mux["uuid"]
        log_start(mux["mux_name"]+" last update: "+format_last_used(mux["last_update"])+" value: "+"{:0.5}".format(mux["value"]))
        if no_stream==0:
            if not get_lock(mux_uuid):
                log_end("Could not get lock for "+mux["mux_name"]+" ("+mux_uuid+")")
                muxes_to_remove.append(mux)
                continue
        log_start("Checking service locks")
        service_names={}
        for text_service in mux["text_services"]:
            service_names[text_service[0]]=0
        for s in service_names:
            if get_lock(s):
                service_names[s]=1
                log(s+" OK")
            else:
                service_names[s]=0
                log(s+" Can't get lock => Ignoring")
        log_end("")
        log_start("listing text services of mux "+mux["mux_name"])
        maxlen=0 
        for text_service in mux["text_services"]:
            l=len(text_service[0])
            if l>maxlen:
                maxlen=l;
        not_in_use_cnt=0
        for text_service in mux["text_services"]:
            name=text_service[0]
            l=len(name)
            spaces=maxlen+1-l
            pid=text_service[1]
            if service_names[name]==1:
                log(name+("…"*spaces)+("{:4}".format(pid))+" 0x"+("{:04x}".format(pid))+ " last update: "+format_last_used(get_last_used(name)))
                not_in_use_cnt=not_in_use_cnt+1
            else:
                log(name+("…"*spaces)+("{:4}".format(pid))+" 0x"+("{:04x}".format(pid))+ " last update: "+format_last_used(get_last_used(name))+ " in use elsewhere")
        log_end("")
        out_tmp=tmpdir+"/"+mux_uuid
        os.makedirs(out_tmp, exist_ok=True)
        date_prefix=datetime.datetime.now().utcnow().isoformat(timespec="seconds")+"+00:00"
        pids=[]
        for text_service in mux["text_services"]:
            name=text_service[0]
            pids.append(text_service[1])
        spids=",".join(map(str,pids))
        url=base_url_auth+"stream/mux/"+mux["uuid"]+"?pids=0,1,"+spids
        log_start("Handling multiplex streaming url: "+url)
        filecount=0
        if no_stream==0 and (len(pids)>0) and (not_in_use_cnt>0):
            log_start("Starting to stream from mux")
            line_indent=log_indent()+ " "
            os.system("timeout 7200 wget -o /dev/null -O - --read-timeout="+str(timeout)+" --tries=1 "+url+" | "+ts_teletext+" --ts --stop "+sfile+" '-P"+line_indent+"' -p"+out_tmp+"/"+date_prefix+"-")
            log_end("")
            #Sort files
            log_start("sort files")
            files=os.listdir(out_tmp)
            for text_service in mux["text_services"]:
                name=text_service[0]
                pid=text_service[1]
                pid_suffix="-0x"+"{:04x}".format(pid)+".zip"
                for f in files:
                    if f.endswith(pid_suffix):
                        os.makedirs(outdir+"/"+name, exist_ok=True)
                        log(f+" => "+outdir+"/"+name+"/"+name+"/"+f)
                        shutil.move(out_tmp+"/"+f, outdir+"/"+name+"/"+f)
                        files.remove(f)
                        set_last_used(name)
                        filecount=filecount+1
            log_end(str(filecount)+" files moved")
        remove_lock(mux["uuid"])
        for s in service_names:
            if service_names[s]==1:
                remove_lock(s)
        if filecount>0:
            set_last_used(mux["uuid"])
            if not limit is None:
                limit=limit-1
                if limit <= 0:
                    print("Ran into limit, exiting", limit)
                    exit()
        log_end("")
        muxes_to_remove.append(mux)
        log_end("")
        if filecount>0:
            if not rsync_target is None:
                log_start("rsync to "+rsync_target)
                cmd="rsync -rv "
                if rsync_remove!=0:
                    cmd=cmd+" --remove-source-files "
                cmd=cmd+outdir+"/* "+rsync_target+' | sed "s/^/'+log_indent()+' /"'
                log(cmd)
                os.system(cmd)
                log_end("")
            break
    log_end("")

