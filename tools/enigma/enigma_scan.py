#!/usr/bin/python3 

import xml.etree.ElementTree as ET
import os
import time
import requests

outdir="outdir"

req=requests.get("http://192.168.5.12/web/getservices?sRef=1:7:1:0:0:0:0:0:0:0:")
req.encoding="UTF-8"

#request.get(URL, auth=('user','pass'))


#tree=ET.parse("test.xml")
tree=ET.fromstring(req.text)

root=tree

#.getroot()

for child in root:
    chname=child[0].text.strip().replace(":","_")
    chout=outdir+"/"+chname+"/";
    print(child[1].text+" to "+chout)
    if not os.path.isdir(chout):
        os.system("mkdir -p "+chout);
        os.system("(timeout 6 wget -o /dev/null --read-timeout 5 -O - http://192.168.5.12:8001/"+child[0].text+") | ../../src/ts_teletext --ts --stop -p"+chout)
#    with os.scandir(".") as it:
#        for entry in it:
#            if entry.name.startswith("0x") and entry.is_file:
#                os.rename(entry.name,outdir+"/"+chname+" "+time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())+"-"+entry.name);
#    os.system("cp "+outdir+"/* /daten/archiv/teletext/enigma/");
#    os.system("rsync --remove-source-files -av "+outdir+"/* teletext@teletext-submit.clarke-3.de:/daten_server/teletext/in/enigma/");
