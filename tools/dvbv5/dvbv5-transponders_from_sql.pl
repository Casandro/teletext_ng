#!/usr/bin/perl

use strict;
use warnings;
use DBI;




my $dbh=DBI->connect("DBI:MariaDB:teletext",'root','');
die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);

my $get_transponders=$dbh->prepare("SELECT id, sat_number, delivery_system, lnb, frequency, polarization, symbol_rate, modulation, pilot, inner_fec, inversion, rolloff, stream_id FROM transponders ORDER BY rand()");

$get_transponders->execute();

while (my ($id, $sat_number, $delivery_system, $lnb, $frequency, $polarization, $symbol_rate, $modulation, $pilot, $inner_fec, $inversion, $rolloff, $stream_id)  = $get_transponders->fetchrow_array() ) {
	print "[",$id,"]\n";
	if (defined $sat_number) {
		print "\t SAT_NUMBER = ", $sat_number, "\n";
	}
	if (defined $delivery_system) {
		print "\t DELIVERY_SYSTEM = ", $delivery_system, "\n";
	}
	if (defined $lnb) {
		print "\t LNB = ", $lnb, "\n";
	}
	if (defined $frequency) {
		print "\t FREQUENCY = ", $frequency, "\n";
	}
	if (defined $symbol_rate) {
		print "\t SYMBOL_RATE = ", $symbol_rate, "\n";
	}
	if (defined $polarization) {
		print "\t POLARIZATION = ", $polarization, "\n";
	}
	if (defined $modulation) {
		print "\t MODULATION = ", $modulation, "\n";
	}
	if (defined $pilot) {
		print "\t PILOT = ", $pilot, "\n";
	}
	if (defined $inner_fec) {
		print "\t INNER_FEC = ", $inner_fec, "\n";
	}
	if (defined $inversion) {
		print "\t INVERSION = ", $inversion, "\n";
	}
	if (defined $rolloff) {
		print "\t ROLLOFF = ", $rolloff, "\n";
	}
	if (defined $stream_id) {
		print "\t STREAM_ID = ", $stream_id, "\n";
	}

	print "\n";
}
