#!/bin/bash



channels=`mktemp /tmp/XXXXXX.channels`

OUTDIR=data

while true
do

./dvbv5-transponders_from_sql.pl > $channels
grep "^\[[0-9]*\]" $channels | sort -R | while IFS= read -r line; do
	mux=`echo $line | tr -d "[]"`
	echo "Transponder: $mux"
	mkdir -p $OUTDIR/$mux
	date >> $OUTDIR/$mux/log
	dvbv5-zap -t 3600 -c $channels -w-1 -a0 -W 250 -f1 -P -o - "$mux" | ../../src/ts_teletext --ts --stop #| tee -a $OUTDIR/$mux/log
	echo "Vorheriger Transponder: $mux"
	dt=`date -u -Iseconds`
	date >> $OUTDIR/$mux/log
	echo >> $OUTDIR/$mux/log
	for x in *.tta
	do
		if [ -e $x ] 
		then
			echo $x
			mv $x $OUTDIR/$mux/$dt-$x
		fi
	done
	./tta_to_services.pl &
	if [ -f move_to_server.sh ] 
	then
		./move_to_server.sh
	fi
done
sleep 10
done
rm $channels
