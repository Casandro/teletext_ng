#!/usr/bin/perl

use strict;
use warnings;
use DBI;


my $worker=$ARGV[0];

my $task=$ARGV[1];

my $dbh=DBI->connect("DBI:MariaDB:teletext",'teletext','teletext');
die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);
if ($task eq "GET") {

	
	my $q=$dbh->prepare("SELECT id FROM transponders WHERE (in_use_by<0 OR in_use_by=?) AND weight > RAND()*90 AND weight>0 ORDER BY date_add(last_used, INTERVAL RAND()*3600 SECOND) LIMIT 1"); 
	$q->execute($worker);
	my ($id)=$q->fetchrow_array();
	$dbh->do("UPDATE transponders set in_use_by=? WHERE id=?", undef, $worker, $id);
	print $id;
} if ($task eq "ERROR") {
	$dbh->do("UPDATE transponders set in_use_by=-1, weight=weight-10 WHERE in_use_by=?", undef, $worker);
	
}else {
	$dbh->do("UPDATE transponders set in_use_by=-1, last_used=NOW() WHERE in_use_by=?", undef, $worker);
}
