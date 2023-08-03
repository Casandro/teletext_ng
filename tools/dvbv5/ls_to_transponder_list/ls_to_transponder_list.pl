#!/usr/bin/perl

use String::Util 'trim';

my $tnum=0;

my $state=0;

foreach $line (<STDIN>) {
	if ($line =~ /^\s*│([^│]+)│([^│├]+)([├|│]).*$/) {
		my $links=trim($1);
		my $rechts=trim($2);
		if (($state==0) && (($links ne "")||($rechts ne ""))) {
			$tnum=$tnum+1;
			print "[".$tnum."]\n";
			$state=1;
		}

		if ($links =~ /^([0-9]{4,5}) (V|H)$/) {
			print "\tFREQUENCY = ".$1."000\n";
			my $pol=$2;
			if ($pol eq "H") {
				print "\tPOLARIZATION = HORIZONTAL\n";
			}
			if ($pol eq"V") {
				print "\tPOLARIZATION = VERTICAL\n";
			}

		}

		if ($rechts=~ /^([0-9]{3,5})$/) {
			print "\tSYMBOL_RATE = ".$1."000\n";
		}
		if ($rechts=~ /^(DVB-S2?)$/) {
			my $ds=$1;
			if ($ds eq "DVB-S") {
				print "\tDELIVERY_SYSTEM = DVBS\n";
			}
			my $ds=$1;
			if ($ds eq "DVB-S2") {
				print "\tDELIVERY_SYSTEM = DVBS2\n";
			}
		}
		if ($rechts=~ /^(QPSK|8PSK|16APSK)$/) {
			my $mod=$1;
			if ($mod eq "QPSK") {
				print "\tMODULATION = QPSK\n";
			}
			if ($mod eq "8PSK") {
				print "\tMODULATION = PSK/8\n";
			}
		}
		if ($rechts=~ /^([0-9]\/[0-9])$/) {
			print "\tINNER_FEC = ".$1."\n";
		}
	} else {
		$state=0;
	}
}
