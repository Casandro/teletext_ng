#!/bin/bash

set -e

mkdir -p /var/spool/lock_service/

cp lock_service.py /usr/local/bin/

cp lock_service.service /etc/systemd/system

systemctl daemon-reload
systemctl enable lock_service
systemctl start lock_service
