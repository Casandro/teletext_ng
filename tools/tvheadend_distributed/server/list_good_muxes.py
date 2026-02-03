#!/usr/bin/python3
import json
import datetime
import time

def get_mux_quality(mux):
    if not "text_services" in mux:
        return 0
    teletext_services=mux["text_services"]
    if len(teletext_services)==0:
        return 0
    cnt=0
    for pid in teletext_services:
        service=teletext_services[pid]
        if service["service_name"]=="BLOCK":
            continue
        if not "captures" in service:
            cnt=cnt+1
            continue
        max_size=None
        for c in service["captures"]:
            size=c[2]
            if max_size is None or size>max_size:
                max_size=size
        if max_size>1000:
            cnt=cnt+1
    return cnt

def fillup(s, l, align):
    if align=="l":
        return s+"─"*(l-len(s))
    if align=="r":
        return "─"*(l-len(s)-1)+s+"─"

def printfilled(s, l, align="l", start=False, end=False):
    if start:
        print("├", end="")
    fs=fillup(str(s),l, align)
    print("─"+fs, end="")
    if end:
        print("┤", end="")
    else:
        print("┼", end="")

with open("/var/spool/teletext_server/muxes.json") as f:
    data=json.load(f)

orbitals={}

for mux_ in data:
    for mux in data[mux_]:
        mux_id=mux["id"]
        orbital=mux_id.split("_")[1]
        if not orbital in orbitals:
            orbitals[orbital]=[]
        orbitals[orbital].append(mux)




for orbit in orbitals:
    print("orbit: %s" % orbit)
    orbit_muxes=orbitals[orbit]
    for mux in orbit_muxes:
        if not "text_services" in mux:
            continue
        time_min=0
        time_max=0
        time_sum=0
        time_cnt=0
        if "captures" in mux:
            for c in mux["captures"]:
                t=c[1]
                if t<time_min:
                    time_min=t
                if t>time_max:
                    time_max=t
                time_sum=time_sum+t
                time_cnt=time_cnt+1
        if time_cnt>0:
            time_avg=time_sum/time_cnt
        else:
            time_avg=0

        if len(mux["text_services"])==0:
            continue

        text_services=mux["text_services"]
        cnt=get_mux_quality(mux)
        if cnt<=0:
            continue
        print("  %s %s-(%s)-%s" %(mux["id"], round(time_min), round(time_avg), round(time_max)))
        for pid in text_services:
            ts=text_services[pid]
            print("   %s %s" % (pid, ts["service_name"] ))
            if "captures" in ts:
                for c in ts["captures"]:
                    if c[2]==0:
                        continue
                    print("      ", end="")
                    dt=datetime.datetime.utcfromtimestamp(c[0]).isoformat(timespec="seconds")
                    printfilled(dt,20, start=True)
                    printfilled(c[1],20)
                    printfilled(c[2],7, align="r")
                    printfilled(c[3],33, end=True)
                        
                    print()

