#!/usr/bin/env perl
use strict;
use warnings;

=pod

=head1 NAME

SRAmetadb_edit_lat_long.pl -- editing latitude and longitude values in SRAmetadb

=head1 VERSION

This is version 0.0.1

=head1 USAGE

    SRAmetadb_edit_lat_long.pl [options]

=head1 REQUIRED ARGUMENTS

=item -db <db> | -database <db>

SRAmetadb file (from SRAdb R package)

=head1 OPTIONS

=over

=item -sql <sql>

sql statement to get lat-long values.


Default: sql.default

=for Euclid:
sql.type: string
sql.default: 'SELECT sample_accession, latitude_and_longitude, latitude, longitude from efetch'


=item --debug [<log_level>]

Set the log level. Default is log_level.default but if you provide --debug,
then it is log_level.opt_default.

=for Euclid:
    log_level.type:        int
    log_level.default:     0
    log_level.opt_default: 1

=item --quiet

=item --version

=item --usage

=item --help

=item --man

Print the usual program information

=back

=head1 DESCRIPTION

Add/update a 'efetch' table
in the SRAmetaDb from R package SRAdb.

This table contains all info returned from
queries with esearch and efetch with
SRA biosample accessions.

The accessions are pulled from the SRAmetadb
database using the '-sql' flag.

=head1 AUTHOR

Nick Youngblut (ndy2@cornell.edu)

=head1 BUGS

There are undoubtedly serious bugs lurking somewhere in this code.
Bug reports and other feedback are most welcome.

=head1 COPYRIGHT

Copyright 2010, 2011
This software is licensed under the terms of the GPLv3

=cut


#--- modules ---#
use Data::Dumper;
use Getopt::Euclid;
use DBI;
use Text::ParseWords;
use Regexp::Common;
use Text::Unidecode;
use Encode;
use List::MoreUtils qw/none/;

#--- I/O error ---#


#--- MAIN ---#
# db connect
my $dbh = connect2db( $ARGV{-db} );

# getting all sample accessions from db
my $entries_r = get_db_entries($dbh, \%ARGV);


# edit latitude and longitude
## trying to get all entries in to lat and long fields
foreach my $samp_acc (keys %$entries_r){
  edit_lat_long($entries_r->{$samp_acc});
}


# closing 
$dbh->commit or die $dbh->err;
$dbh->disconnect or die $dbh->err;



#--- Subroutines ---#

=head2 edit_lat_long

Top-level subroutine for editing lat-long.
Trying to parse human semi-readable lat-long.
Lat-long can include unicode.

=cut

sub edit_lat_long{
  my $entry_r = shift or die "Provide hashref of entry\n";
  my $argv_r = shift;

  # determine what to do based on attributes defined
  my ($latitude, $longitude);
  ## if lat,long defined
  if(defined $entry_r->{latitude_and_longitude} and
     ! defined $entry_r->{latitude} and
     ! defined $entry_r->{longitude} ){

    # splitting
    ## adding comma after 'N' or 'S' designation
    $entry_r->{latitude_and_longitude} =~ s/( +[NS](outh|orth)*) +(\d+)/$1, $2/;
    my @lat_long = split /\s*[,_\/]+\s*/, $entry_r->{latitude_and_longitude}, 2;
    if( scalar @lat_long == 2 ){
      $latitude = interpret_lat_long(
				     $lat_long[0], 
				     dir => 'latitude'
				    );
      $longitude = interpret_lat_long(
				      $lat_long[1], 
				      dir => 'longitude'
				     );      
    }
    else{
      printf STDERR "ERROR: lat-long split did not work for %s\n",
	 $entry_r->{latitude_and_longitude};
      die $!;
    }
  }
  ## if lat-and-long defined
  elsif(defined $entry_r->{latitude} or
     defined $entry_r->{longitude} ){

    # getting lat-long from just lat or long
    ($latitude,$longitude) = find_lat_or_long( $entry_r->{latitude}, 
					       'longitude')
      unless defined $entry_r->{longitude};

    ($latitude,$longitude) = find_lat_or_long( $entry_r->{longitude}, 
					       'latitude')
      unless defined $entry_r->{latitude};

    # interpreting lat or long
    $latitude = interpret_lat_long( 
				   $entry_r->{latitude},
				   dir => 'latitude'
				  );
    $longitude = interpret_lat_long(  
				    $entry_r->{longitude}, 
				    dir => 'longitude'
				   );    
  }
  ## none defined
  elsif( none{ defined $entry_r->{$_} } 
	 qw/latitude_and_longitude latitude longitude/){
    
  }
  ## else ?
  else{
    print Dumper $entry_r;
    die "Internal ERROR!\n";
  }
  
}


=head2 interpret_lat_long

Interpreting lat and long.
Many contain unicode and many need to
be converted from DMS format to decimal.

=cut 

sub interpret_lat_long{
  my $value = shift or die $! "Provide latitude or longitude value\n";
  my $kwargs = @_;


  # is decimal?
  ## just real number?
  if($value =~ /.*?($RE{num}{real})\s*/){
    return $1;
  }

  ## decimal with direction?
  if($value =~ /.*?($RE{num}{real})\s*([NSEWnsew])/){
    my ($dec, $dir) = ($1, $2);
    $1 *= -1 if $dir =~ /[SWsw]/;
    return $dec;
  }


  # is DMS format?
  ## DMS with spacing or acii character?
  if($value =~ /\p{L}\p{M}*/){
    
  }

  ## DMS with unicode?


}

=head2 DMS_to_decimal

converting lat-long from degree-min-sec to decimal

=cut

sub DMS_to_decimal{
  my $degrees = shift or die "Provide degrees\n";
  my $minutes = shift;
  $minutes = 0 unless defined $minutes;
  my $seconds = shift;
  $seconds = 0 unless defined $seconds;
  my $direction = shift;
  $direction = 'N' unless defined $direction;


  # calc decimal
  my $decimal = $degrees + ($minutes / 60) + ($seconds / 3600);

  $decimal *= -1 if $direction =~ /^\s*[SWsw]\s*$/;

  #print Dumper $decimal; exit;
  return $decimal;
}


=head2 find_lat_or_long

Either lat or long missing.
Checking for missing value defined value.

=cut

sub find_lat_or_long{
  my $present = shift or die "Provide defined lat or long\n";
  my $missing = shift or die "Provide missing: latitude or longitude\n";
  
  my ($latitude, $longitude);
  if( $missing eq 'latitude' ){
    if( $present =~ /^\s*\([NS]:[EW]\) +(-*[\d.]+):+(-*[\d.]+)/ ){
      $latitude = $1;
      $longitude = $2;
    }
    else{
      die "Dont know how to parse: '$present'\n";
    }
  }
  elsif( $missing eq 'longitude' ){
      die "Dont know how to parse: '$present'\n";
  }
  else{
    die "ERROR: cannot determine missing variable: '$missing'\n";
  }

  return $latitude, $longitude;
}




=head2 get_db_entries

Getting entries from SRAmetadb

=cut

sub get_db_entries{
  my $dbh = shift or die "Provide dbh\n";
  my $argv_r = shift;


#  print Dumper $argv_r->{-sql};

  # getting column names
  my $sth = $dbh->prepare( $argv_r->{-sql} ) or die $dbh->err;

  # checking column names
  my $col_names = $sth->{NAME_lc_hash};
  die "ERROR: 'sample_accession' must be returned by sql\n"
    unless grep /sample_accession/, keys %$col_names; 
  die "ERROR: 'latitude_and_longitude', 'latitude', or 'longitude' must be returned by sql\n"
    unless grep /(latitude_and_longitude|latitude|longitude)/, keys %$col_names; 


  # query
  $sth->execute() or die $dbh->err;
  
  # get columns
  my $ret = $sth->fetchall_hashref('sample_accession') or die $dbh->err;


  # status
  printf STDERR "Number of entries returned from query: %i\n\n",
    scalar keys %$ret;


  return $ret;
}


=head2 connect2db

connecting to sqlite db

=cut 

sub connect2db{
# connecting to CLdb
# $db_file = database file
  my $db_file = shift or die "Provide db file name\n";
  
  my %attr = (RaiseError => 0, PrintError=>0, AutoCommit=>0);
  my $dbh = DBI->connect("dbi:SQLite:dbname=$db_file", '','', \%attr)
                or die " Can't connect to $db_file!\n";
  
  return $dbh;
}


