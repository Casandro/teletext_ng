#!/bin/bash


adapter=$1

if [ -n "$adapter" ]
then
	echo "Adapter $adapter"
else
	echo "No Adapter given"
	exit
fi


channels=`mktemp /tmp/XXXXXX.channels`

OUTDIR=data


for true
do
./dvbv5-transponders_from_sql.pl > $channels
for cnt in {0..99}
do
	sleep 10
	mux=`./use_transponder.pl $adapter GET`
	echo "Transponder: $mux"
	#|| ./use_transponder.pl $adapter $mux; echo "Transponder $mux didn't lock"; continue
	echo "Going forward with Transponder $mux"
	mkdir -p $OUTDIR/$mux
	dvbv5-zap -t 3600 -c $channels -w-1 -a$adapter -W 250 -P -o - "$mux" | ../../src/ts_teletext --ts --stop
	return_code=$?
	if (( return_code != 0 ))
	then
		echo "Tuning failed for $mux"
	fi
	echo "Vorheriger Transponder: $mux"
	dt=`date -u -Iseconds`
	for x in *.tta
	do
		if [ -e $x ] 
		then
			echo $x
			mv $x $OUTDIR/$mux/$dt-$x
		fi
	done
	./tta_to_services.pl 
	./use_transponder.pl $adapter $mux
	if [ -f move_to_server.sh ] 
	then
		./move_to_server.sh
	fi
done
rm $channels
done
