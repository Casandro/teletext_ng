#!/bin/bash

now=$(date +%s)

display_age() {
	fn=$1
	dt=$(stat -c %Y $fn)
	let age=$now-$dt
	echo $age
}


for x in $(ls -r --sort=time lock/*.*.last_used)
do
	tn=$(basename $x .last_used)
	age=$(display_age $x)
	let hour=age/3600
	let minute=(age/60)%60
	let second=age%60
	printf "%02d:%02d:%02d %s" $hour $minute $second $tn
	if [ -f lock/$tn.lock ]
	then
		echo -n " in use "
	fi
	echo ""
#	echo $age $tn
done
