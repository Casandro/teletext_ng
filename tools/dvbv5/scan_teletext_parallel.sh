#!/bin/bash


adapter=$1

if [ -n "$adapter" ]
then
	echo "Adapter $adapter"
else
	echo "No Adapter given"
	exit
fi


channels=`mktemp /tmp/channels.XXXXXX.channels`

OUTDIR=data

SCRIPTDIR=`realpath .`
TS_TELETEXT=`realpath ../../src/ts_teletext`



$SCRIPTDIR/dvbv5-transponders_from_sql.pl > $channels
for cnt in {0..3}
do
	mux=`$SCRIPTDIR/use_transponder.pl $adapter GET`
	echo "Going forward with Transponder $mux $return_code"
	
	blockpids=`echo "select blockpids from transponder where id=$mux" | mysql -uteletext -pteletext teletext`

	mkdir -p $OUTDIR/$mux
	rm -r $OUTDIR/done

	DIR=$OUTDIR/$mux
	FIFO=$DIR/fifo
	rm -r $FIFO
	mkfifo $FIFO
	LOCKFILE=$DIR/lock
	rm -r $LOCKFILE
	PREFIX=$DIR/`date -u -Iseconds`-
	
	start=`date +%s.%N` 
	dvbv5-zap -t 7200 -c $channels -w-1 -a$adapter -W 250 -P -o $FIFO "$mux" &
	zappid=$!
	sleep 0.5
       	$TS_TELETEXT --ts --stop -l$LOCKFILE -p$PREFIX -b$blockpids $FIFO &
	tspid=$!

	sleep 0.5

	res=0
	echo "Waiting for lock file"	
	tm=0;
	while [ ! -f $LOCKFILE ] 
	do
		sleep 0.25
		let tm=tm+1
		if (( tm > 50 ))
		then
			echo "Timeout!"
			res=555
			break
		fi
	done

	echo $res $tm
	
	if (( res == 0 ))
	then
		wait -n $tspid
		return_code=$?
		$SCRIPTDIR/use_transponder.pl $adapter $mux
	else
		echo "Timeout! killing $tspid and $zappid"
		return_code=555
		$SCRIPTDIR/use_transponder.pl $adapter ERROR
		kill $tspid
		kill $zappid
	fi
	stop=`date +%s.%N`
	echo "Finished code $return_code"
	duration=`echo $stop-$start | bc` 
	echo "insert into transponder_stats (transponder, result, duration, time, worker) VALUES ($mux, $return_code, $duration, NOW(),$adapter);" | mysql -uteletext -pteletext teletext
	echo "Vorheriger Transponder: $mux"

done
rm $channels
