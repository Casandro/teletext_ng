#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use File::Copy;


my $dbh=DBI->connect("DBI:MariaDB:teletext",'teletext','teletext');
die "failed to connect to MySQL database:DBI->errstr()" unless($dbh);

my $find_service=$dbh->prepare("SELECT id FROM text_service WHERE transponder=? AND pid=?");
my $create_service=$dbh->prepare("INSERT INTO text_service (transponder, pid, header) values (?,?,?)");
my $update_service=$dbh->prepare("UPDATE text_service SET last_used=NOW() where id=?");
my $update_header=$dbh->prepare("UPDATE text_service SET header=? where id=?");

my $find_service_name=$dbh->prepare("SELECT service_name FROM text_service WHERE id=?");

my $ddir="data";
my $dest="data_sorted";

mkdir $dest;

opendir(my $transponderdir,  $ddir);

while (readdir $transponderdir) {
	my $transponder=$_;
	my $lockfile=$ddir."/".$transponder."/lock";
	unless ( -e $lockfile ) {
		opendir (my $sdir, $ddir."/".$transponder);
		while (readdir $sdir) {
			my $service=$_;
			if ($service=~/(0x[0-9a-fA-f]{4})\.tta$/) {
				my $filename=$ddir."/".$transponder."/".$service;
				my $pid=hex($1);
				$find_service->execute($transponder, $pid) or die "Error during find_service";
				(my $id)=$find_service->fetchrow_array();
				if (defined $id) {
				} else {
					my $header=`dd if=$filename bs=1 skip=4096  2> /dev/null | ../get_name`;
					chomp($header);
					$create_service->execute($transponder, $pid, $header);
					continue
				}

				$find_service_name->execute($id);
				(my $service_name) = $find_service_name->fetchrow_array();

				if (defined $service_name) {
					mkdir $dest."/".$service_name;
					my $ret=move($filename, $dest."/".$service_name);
					print $id."    ".$filename."     ".$service_name." ".$ret."\n";
					if ($ret==1) {
						$update_service->execute($id);
					}
				} else {
					my $header=`dd if=$filename bs=1 skip=4096  2> /dev/null | ../get_name`;
					chomp($header);
					$update_header->execute($header,$id);
				}

			}
		}
		closedir($sdir);
	}
}

closedir($transponderdir);
