#!/usr/bin/python3 

import xml.etree.ElementTree as ET
import os
import time
import requests

outdir="outdir"

req=requests.get("http://192.168.5.12/web/getservices?sRef=1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.SD.tv\" ORDER BY bouquet")
req.encoding="UTF-8"

#request.get(URL, auth=('user','pass'))


#tree=ET.parse("test.xml")
tree=ET.fromstring(req.text)

root=tree

#.getroot()

for child in root:
    chname=child[1].text.strip().replace(" ","_").replace("/","_").replace("$","")
    print(chname)
    os.system("wget -o /dev/null -O - http://192.168.5.12:8001/"+child[0].text+" | ../src/ts_teletext --ts --stop")
    with os.scandir(".") as it:
        for entry in it:
            if entry.name.startswith("0x") and entry.is_file:
                os.rename(entry.name,outdir+"/"+chname+" "+time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())+"-"+entry.name);
    os.system("cp "+outdir+"/* /daten/archiv/teletext/enigma/");
    os.system("rsync --remove-source-files -av "+outdir+"/* teletext@teletext-submit.clarke-3.de:/daten_server/teletext/in/enigma/");
