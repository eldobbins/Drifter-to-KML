#!/bin/sh

cd /home/dobbins/drifters/dft2KML
./drifterKMLgen.py > output.txt

# generate the summary files too 
./drifterSummaryKML.py >> output.txt

# Put the KML files in the web server area so can wget them
cp kml/*.kml /var/www/html/artlab/data/kml/drifters

