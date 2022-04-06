#!/usr/bin/perl

use strict;
use warnings;
use DBI;




my $dbh=DBI->connect("DBI:MariaDB:teletext",'root','');
die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);

my $find_transponder=$dbh->prepare("SELECT id FROM transponders WHERE sat_number=? AND frequency=? AND polarization=?");
my $create_transponder=$dbh->prepare("INSERT INTO transponders (sat_number, delivery_system, lnb, frequency, polarization, symbol_rate, modulation, pilot, inner_fec, inversion, rolloff, stream_id) values (?,?,?,?,?,?,?,?,?,?,?,?)");

sub printservice {
	my (%hash)=@_;
	if (! defined $hash{"SAT_NUMBER"}) {
		$hash{"SAT_NUMBER"}=1;
	}
	$find_transponder->execute($hash{"SAT_NUMBER"}, $hash{"FREQUENCY"}, $hash{"POLARIZATION"});
	my ($tid)=$find_transponder->fetchrow_array();
	if (defined $tid) {
		print $tid, "\n";
	} else {
		$create_transponder->execute(
			$hash{"SAT_NUMBER"}, $hash{"DELIVERY_SYSTEM"}, $hash{"LNB"}, $hash{"FREQUENCY"},
			$hash{"POLARIZATION"}, $hash{"SYMBOL_RATE"}, $hash{"MODULATION"}, $hash{"PILOT"}, $hash{"INNER_FEC"},
			$hash{"INVERSION"}, $hash{"ROLLOFF"}, $hash{"STREAM_ID"});
	}
}


my %service_hash;
foreach my $line ( <STDIN> ) {
	chomp( $line );
	if (length($line)<1) {
		#	print %service_hash, "=======\n";
		printservice(%service_hash);
	} elsif ( substr($line, 0, 1) eq '[') {
		$service_hash{"SERVICE_NAME"}=substr($line, 1, -1);
		%service_hash=();
	} else {
		my $kv=substr($line, 1);
		my @sp=split('=', $kv);
		my $key=$sp[0];
		$key =~ s/^\s+|\s+$//g;
		my $value=$sp[1];
		$value =~ s/^\s+|\s+$//g;
		#		print $key.'-'.$value."\n";
		$service_hash{$key}=$value;
	}
}

