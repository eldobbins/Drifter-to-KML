#!/bin/sh
#
# A snippet to process a microstar drifter data file downloaded via v2 of PacificGyre's API (post Dec 2011).
# i.e. using a command like:
# wget --quiet -O SFOS-I-0001_v2.csv "http://api.pacificgyre.com/pgapi/getData.aspx?userName=SFOS&password=*****&format=CSV&deviceNames=SFOS-I-0001&startDate=08/20/2011&commentCharacters=%&delimiter=,"
#
# It removes lines that have gpsQuality not equal to 3.
# First argument is the input file name.
# Second argument is the cleaned up output file name.
#
# ELD
# 7/27/2012
#

    awk '{
        split($0,arr,",")
        if(arr[7] == 3 || arr[7] == "" || arr[7] == "gpsQuality") { print $0 }
    }' ${1} > ${2}
