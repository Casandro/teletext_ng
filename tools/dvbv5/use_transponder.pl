#!/usr/bin/perl

use strict;
use warnings;
use DBI;


my $worker=$ARGV[0];

my $task=$ARGV[1];

if ($task eq "GET") {
	my $dbh=DBI->connect("DBI:MariaDB:teletext",'root','');
	die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);
	
	my $q=$dbh->prepare("SELECT id FROM transponders WHERE in_use_by<0 OR in_use_by=? ORDER BY id");
	$q->execute($worker);
	my ($id)=$q->fetchrow_array();
	$dbh->do("UPDATE transponders set in_use_by=? WHERE id=? ORDER BY last_used", undef, $worker, $id);
	print $id;
} else {
	my $transponder=$ARGV[1];
	my $dbh=DBI->connect("DBI:MariaDB:teletext",'root','');
	die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);
	
	$dbh->do("UPDATE transponders set in_use_by=-1, last_used=NOW() WHERE id=?", undef, $transponder);
}
