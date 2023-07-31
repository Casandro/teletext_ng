#!/bin/bash


adapter=$1

if [ -n "$adapter" ]
then
	echo "Adapter $adapter"
else
	echo "No Adapter given"
	exit
fi

while true
do
	(./scan_teletext_parallel.sh $adapter)
	echo $!
done
