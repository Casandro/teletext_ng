#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use File::Copy;


my $dbh=DBI->connect("DBI:MariaDB:teletext",'root','');
die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);

my $find_service=$dbh->prepare("SELECT id FROM text_service WHERE transponder=? AND pid=?");
my $create_service=$dbh->prepare("INSERT INTO text_service (transponder, pid, header) values (?,?,?)");

my $find_service_name=$dbh->prepare("SELECT service_name FROM text_service WHERE id=?");

my $ddir="data";
my $dest="data_sorted";

mkdir $dest;

opendir(my $transponderdir,  $ddir);

while (readdir $transponderdir) {
	my $transponder=$_;
	opendir (my $sdir, $ddir."/".$transponder);
	while (readdir $sdir) {
		my $service=$_;
		if ($service=~/(0x[0-9a-fA-f]{4})\.tta$/) {
			my $filename=$ddir."/".$transponder."/".$service;
			my $pid=hex($1);
			printf "$transponder $pid\n";
			$find_service->execute($transponder, $pid) or die "Error during find_service";
			(my $id)=$find_service->fetchrow_array();
			if (defined $id) {
			} else {

				my $header=`dd if=$filename bs=1 skip=4096  2> /dev/null | ../get_name`;
				chomp($header);
				$create_service->execute($transponder, $pid, $header);
				$id=$create_service->{mysql_insertid};
			}

			$find_service_name->execute($id);
			(my $service_name) = $find_service_name->fetchrow_array();

			if (defined $service_name) {
				mkdir $dest."/".$service_name;
				move($filename, $dest."/".$service_name);
				print $id."    ".$filename."     ".$service_name."\n";
			}

		}
	}
	closedir($sdir);
}

closedir($transponderdir);
