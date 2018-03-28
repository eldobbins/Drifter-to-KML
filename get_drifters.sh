#!/bin/sh
#
#  Single script to call other scripts that get the drifters
#  Not actually used in production.  Added these lines to
#  ~/bin/1hour_processing.sh
#
#  ELD
#  8/07/2012
#


cd /home/dobbins/drifters/dft2KML


./get_PacificGyre.py > download_output.txt

#./get_iSPHERE.py >> download_output.txt  disabled 6/26/2013.

# little hack to copy a few 2012 drifters into a 2013 directory
#\cp ../BOEM2012-1/UAFSFOS-SVP-0005.csv ../BOEM2012-13
#\cp ../BOEM2012-1/UAFSFOS-SVP-0006.csv ../BOEM2012-13
#\cp ../BOEM2012-1/UAFSFOS-SVP-0009.csv ../BOEM2012-13
#\cp ../BOEM2012-1/UAFSFOS-SVP-0011.csv ../BOEM2012-13

