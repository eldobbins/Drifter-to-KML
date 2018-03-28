# Drifter-to-KML

Python code (mostly) to download drifter data using the PacificGyre API and then exact position information and reformat it as KML.  The KML was then referenced using the Google Maps API on a webpage to display track-lines on a publicly accessible map.

Drifters to process are listed in the XML file, ordinarily in a separate directory where the downloaded data will be stored.  The XML was updated by hand as drifters were deployed and failed.

A secondary process extracted KML code from a group of drifters and placed it into a single KML file so multiple tracks could be displayed using only 1 KML file.  The setdef*.xml files defined the groups of drifters.

This code was used with several different drifter types with differently formatted data files.  As new types of drifters were added, code was added to drifterdat_api.py to accommodate them.  Internally, a consistent structure passes data between the different subroutines.

This code was executed by calling drifterKMLgen.sh via cron hourly.