#!/bin/bash

BIN_NAME="teletext_capture_client.py"
DIR_NAME="/usr/local/bin/"

CONF_DIR=/etc/teletext_ng

mkdir -p $CONF_DIR

mv $DIR_NAME/$BIN_NAME $DIR_NAME/$BIN_NAME-old

set -e

cp teletext_capture_client@.service /etc/systemd/system/

cp $BIN_NAME $DIR_NAME/$BIN_NAME
chmod a+x $DIR_NAME/$BIN_NAME


for fn in configs/*.conf
do
	bn=$(basename $fn .conf)
	echo $fn $bn
	cp $fn $CONF_DIR/$bn.conf
	systemctl enable teletext_capture_client@$bn
done
systemctl daemon-reload



for fn in configs/*.conf
do
	bn=$(basename $fn .conf)
	echo sudo systemctl start teletext_capture_client@$bn
done
