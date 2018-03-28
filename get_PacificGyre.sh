#!/bin/sh
#
# As was used for Greenland2011.  Has now been superceeded by get_PacificGyre.py
#
#  ELD
#  7/27/2012
#


cd /home/dobbins/drifters/test_microstar

# API as of Dec 2011 (includes salinity sensors)
# Use this to get the command:  http://api.pacificgyre.com/pgapi/

# brute
# wget --quiet -O SFOS-I-0001_v2.csv "http://api.pacificgyre.com/pgapi/getData.aspx?userName=SFOS&password=*****&format=CSV&deviceNames=SFOS-I-0001&startDate=08/20/2011&commentCharacters=%&delimiter=,"
# wget --quiet -O SFOS-I-0002_v2.csv "http://api.pacificgyre.com/pgapi/getData.aspx?userName=SFOS&password=*****&format=CSV&deviceNames=SFOS-I-0002&startDate=08/17/2011&commentCharacters=%&delimiter=,"

# fancy with removal of bad points
drifterids="SFOS-I-0001 SFOS-I-0002"
for drifterid in $drifterids
do
    wget --quiet -O ${drifterid}_orig.csv "http://api.pacificgyre.com/pgapi/getData.aspx?userName=SFOS&password=*****&format=CSV&deviceNames=${drifterid}&startDate=08/17/2011&enddate=12/31/2012%2023:59&commentCharacters=%&delimiter=,"
    awk '{
        split($0,arr,",")
        if(arr[7] == 3 || arr[7] == "gpsQuality") { print $0 }
    }' ${drifterid}_orig.csv > tmp.csv
    mv tmp.csv ${drifterid}.csv
done





cp *.csv /var/www/html/artlab/data/csv/drifters

