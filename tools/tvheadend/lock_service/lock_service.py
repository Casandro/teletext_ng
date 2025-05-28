#!/usr/bin/env python3
import pathlib
from fastapi import FastAPI, Response, BackgroundTasks
from pydantic import BaseModel
import threading
import uvicorn
import os
import time
import sched
import json
import datetime
import base64

app = FastAPI()

service_lock={}
service_last_used={}
service_header={}

#Read settings
config={}
config["local_port"]=8888

def store_locks():
    with open('service_locks.json','w') as t_file:
        json.dump(service_lock,fp=t_file,indent=4, sort_keys=True)

def store_last_used():
    with open('service_last_used.json','w') as t_file:
        json.dump(service_last_used,fp=t_file,indent=4, sort_keys=True)

def store_header():
    with open('service_header.json','w') as t_file:
        json.dump(service_header,fp=t_file,indent=4, sort_keys=True)

def load_service():
    global service_lock
    global service_last_used
    global service_header

    try:
        with open('service_locks.json') as t_file:
           service_lock=json.load(t_file)
    except:
        service_lock={}
    try:
        with open('service_last_used.json') as t_file:
           service_last_used=json.load(t_file)
    except:
        service_last_used={}
    try:
        with open('service_header.json') as t_file:
           service_header=json.load(t_file)
    except:
        service_header={}

def is_service_locked(service):
    if not service in service_lock:
        return False
    if service_lock[service]>time.time():
        return True
    service_lock.pop(service)
    return False

def format_delta(delta):
    a=abs(delta) 
    if a>60:
        return str(datetime.timedelta(seconds=int(a)))
    if a>1:
        return "{:0.5}".format(delta)+"s"
    if a>0.001:
        return "{:0.5}".format(delta*1000)+"ms"
    return "{:0.5}".format(delta*1000000)+"µs"

def service_decode(cservice):
    if cservice.find(".")>=0:
        return cservice
    return base64.b64decode(cservice).decode("UTF-8")

@app.get("/")
async def read_root():
    data="<html><head><title>Status</title></head><body>"
#    data=data+"<table><tr><th>Name</th><th>Alter</th></tr>"
#    for x in service_lock:
#        data=data+"<tr><td>%s</td><td>%s</td></tr>"%(x, service_lock[x])
#    data=data+"</table>"
    last_used_sorted=dict(sorted(service_last_used.items(), key=lambda item: item[1], reverse=False))
    data=data+"<table><tr><th>service</th><th>age</th><th>header</th></tr>"
    for x in last_used_sorted:
        age_str=str(format_delta(time.time()-last_used_sorted[x]))
        if is_service_locked(x):
            age_str=age_str+ " in use"
        header="no header"
        if x in service_header:
            sheader=service_header[x]
            header="<tt>"+sheader.rstrip()+"</tt>"
        data=data+"<tr><td>%s</td><td>%s</td><td>%s</td></tr>"%(x, age_str, header)
    data=data+"</table>"
    data=data+"</body></html>"
    return Response(content=data, media_type="text/html;charset=utf-8")

@app.post("/set_last_used")
async def set_last_used(service: str):
    service=service_decode(service)
    service_last_used[service]=time.time()
    store_last_used()
    if service in service_lock:
        service_lock.pop(service)
        store_locks()
    return Response(content="OK", media_type="text/plain;charset=utf-8")

@app.get("/get_last_used")
async def get_last_used(service: str):
    service=service_decode(service)
    if service in service_last_used:
        data="%s" % service_last_used[service]
    else:
        data="0"
    return Response(content=data, media_type="text/plain;charset=utf-8")

@app.post("/set_lock")
async def set_lock(service: str):
    service=service_decode(service)
    if is_service_locked(service):
        return Response(content="Still Locked", status_code=400, media_type="text/plain;charset=utf-8")
    service_lock[service]=time.time()+7200
    store_locks()
    return Response(content="OK", media_type="text/plain;charset=utf-8")

@app.post("/release_lock")
async def release_lock(service: str):
    service=service_decode(service)
    if service in service_lock:
        service_lock.pop(service)
        store_locks()
    return Response(content="OK", media_type="text/plain;charset=utf-8")


@app.post("/set_header")
async def set_header_post(service: str, header:str):
    service=service_decode(service)
    header=base64.b64decode(header).decode("UTF-8")
    service_header[service]=header;
    store_header()
    return Response(content="OK", media_type="text/plain;charset=utf-8")

@app.get("/set_header")
async def set_header_get(service: str, header:str):
    service=service_decode(service)
    header=base64.b64decode(header).decode("UTF-8")
    service_header[service]=header;
    store_header()
    return Response(content="OK", media_type="text/plain;charset=utf-8")


@app.on_event("startup")
def startup_event():
    print("startup_event")
    threading.Thread(target=check_status, daemon=True).start()


def check_status():
    print("check_status starting", flush=True)
    while main_thread.is_alive():
        try:
            time.sleep(100)
        except:
            print("Exception raised, continuing", flush=True)

def main():
    load_service()
    global main_thread, end_program
    main_thread=threading.current_thread()
    uvicorn.run(app, port=8888, host="0.0.0.0", log_level="info")    
    print("Ending program")
    end_program=1


if __name__ == "__main__":
    main()

