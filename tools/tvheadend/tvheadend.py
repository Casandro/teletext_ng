#!/usr/bin/python3 

import os
import time
import requests
from requests.auth import HTTPDigestAuth
import json
import datetime

outdir="outdir"

base_url="http://127.0.0.1:9981/"
base_url_auth="http://teletext:teletext@127.0.0.1:9981/"

url=base_url+"api/raw/export?class=dvb_mux"

try:
   with open('translations.json') as t_file:
       translations=json.load(t_file)
except:
    translations=json.loads('{"blurb": "blurb"}')

try:
    with open('blockpids.json') as t_file:
        blockpids=json.load(t_file)
except:
    blockpids={}

req=requests.get(url, auth=HTTPDigestAuth('teletext', 'teletext'))
req.encoding="UTF-8"

muxes=json.loads(req.text)

all_mux_pids={}
for mux in muxes:
    mux_pids=[]
    mux_uuid=mux["uuid"]

    if mux['enabled']!=0:
        for service in mux['services']:
            req=requests.get(base_url+"api/raw/export?uuid="+service, auth=HTTPDigestAuth('teletext', 'teletext'))
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
                        srvname=translations[srvname]
                    except:
                        translations[srvname]=""
                    mux_pids.append([srvname,stream['pid']]);
                    pids.append(stream['pid'])
                    if mux_uuid in blockpids:
                        print(blockpids[mux_uuid])
                        if stream['pid'] in blockpids[mux["uuid"]]:
                            pids.remove(stream['pid'])
                            mux_pids.remove([srvname,stream['pid']]);
        if len(mux_pids)>0:
            all_mux_pids[mux["uuid"]]=mux_pids
            pids=""
            for stream in mux_pids:
                if len(pids)>0:
                    pids=pids+","
                pids=pids+str(stream[1]);
            url=base_url_auth+"stream/mux/"+mux['uuid']+"?pids="+pids
            print(url)
            out_tmp=outdir+"/"+mux['uuid']
            os.makedirs(out_tmp, exist_ok=True)
            date_prefix=datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
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
    with open('translations.json','w') as t_file:
        json.dump(translations,fp=t_file,indent=4, sort_keys=True)

with open('all_mux_pids.json','w') as t_file:
    json.dump(all_mux_pids,fp=t_file,indent=4, sort_keys=True)
#print(muxes)
#tree

#.getroot()

#for child in root:
 #   chname=child[1].text.strip().replace(" ","_").replace("/","_").replace("$","")
  #  print(chname)
#    os.system("wget -o /dev/null -O - http://192.168.5.12:8001/"+child[0].text+" | ../src/ts_teletext --ts --stop")
 #   with os.scandir(".") as it:
#        for entry in it:
#            if entry.name.startswith("0x") and entry.is_file:
#                os.rename(entry.name,outdir+"/"+chname+" "+time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())+"-"+entry.name);
#    os.system("cp "+outdir+"/* /daten/archiv/teletext/enigma/");
#    os.system("rsync --remove-source-files -av "+outdir+"/* teletext@teletext-submit.clarke-3.de:/daten_server/teletext/in/enigma/");
