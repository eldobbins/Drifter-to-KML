#!/usr/bin/python2.6

# Functions to add info on a drifter's location to a KML tree
#
# by eld 6/21/11
# ELD 7/25/12 : move Microstar line handling to drifterdat_api.py
#

from lxml import etree
from pykml.factory import KML_ElementMaker as K
from pykml.parser import parse
from lxml.builder import E
import drifterdat_api
import os, time


def Track(coords):
    # make trackline KML from a string of coordinates
    trackline = K.Placemark(
                  K.name("Trackline"),
                  K.styleUrl("#trackline"),
                  K.LineString(
                    K.tesselate(1),
                    K.altitudeMode('clampToGround'),
                    K.coordinates(coords)
                  )
                )
    return trackline
    # check
    #print etree.tostring(trackline, pretty_print=True)


def readStub(stubname):
    # read in the drifter KML stub, and return the root element
    # this is for testing.
    fid = open(stubname,'r')
    drifterKML = parse(fid).getroot()
    fid.close()
    return drifterKML


def dat2KML(drifterKML, Ddeploy):
    # take an existing KML structure and add points based on data gleaned from the
    # drifter data file.  Makes a trackline from all the locations
    # but only saves position points occasionally to avoid clutter.
    # Also adds deployment and current/final location information.
    # Ddeploy : the deployment dictionary object
    
    # Indentify the (unpopulated) position dictionary object that provides the method for reading the data
    event = Ddeploy['event']

    # Identify the data file based on the deployment
    datfile = Ddeploy['datafile']
    if datfile is None:
        message = 'Warning.  Could not find a data file for %s' % self.Ddeployment['id']
        print message
        return drifterKML

    # initializing some 
    blnk = '          '
    coords = ''
    nexttime = 0
    lstime = 0
    lastcoord = '%f,%f,0' % (0, 0) # I'd like to get the coordinates from the Deployment
    dtime = time.mktime( time.strptime(Ddeploy['startstr'], "%Y-%m-%d %H:%M:%S") )
    if Ddeploy['endstr'] is None:
        # there is no endtime yet, so set to something enormously large
        etime = time.mktime( time.strptime("2020-01-01 00:00:00", "%Y-%m-%d %H:%M:%S") )        
    else:
        etime = time.mktime( time.strptime(Ddeploy['endstr'], "%Y-%m-%d %H:%M:%S") )
   
    # Placemark so they don't overlap, but xpath can't seem to deal with a Placemark tag

    # For each line in the datafile, grab coords for trackline.  If needed, make endpoint placemarks
    file = open(datfile,'r')
    while True:
        line = file.readline()
        if not line: break
        event.populate(line)

        # check the line had the instrument id (iSPHERE doesn't)
        if event['instrument'] == event['badflag']:
            event['instrument'] = str(Ddeploy['id'])

        # check the line had complete data
        if event['latitude'] == event['badflag'] or \
           event['longitude'] == event['badflag']:
            print 'Coordinate unavailable'
        else:
            # translate the timestring in the file to a struc_time tuple
            timestamp = time.strptime(event['timestamp'],"%Y-%m-%d %H:%M:%S")
            # translate to seconds since the epoch
            fltime = time.mktime(timestamp)

            # logic to skip parts of file that aren't between start and end times
            if fltime < dtime and not Ddeploy['newestLast']: break     # don't read any more lines
            if fltime > etime and Ddeploy['newestLast']: break      # don't read any more lines
            if fltime > dtime and fltime < etime:

                # if this is the first line, add either a deployment or current/final placemark
                if lstime == 0:
                    if Ddeploy['newestLast']:
                        if Ddeploy['latitude'] is None and Ddeploy['longitude'] is None:
                            # probably because there are no lat,lon in the DrifterStatus file, so create them
                            # from the current point
                            Ddeploy['latitude'] =  str( event['latitude'] )
                            Ddeploy['longitude'] =  str( event['longitude'] )
                            placemark = Ddeploy.genKMLPoint()
                            drifterKML.Document.append(etree.Comment("\nDeployment Placemark\n"))
                            drifterKML.Document.append(placemark)
                    else:
                        placemark = Ddeploy.genKMLPoint(event)
                        drifterKML.Document.append(etree.Comment("\nMost Recent Placemark\n"))
                        drifterKML.Document.append(placemark)
                    lstime = fltime
                else:
                    # add daily points into their folder
                    if abs(fltime - lstime) > 24*60*60:
                        pointKML = event.genKMLPoint(1)
                        # Leandra asked if these could be remove so try temporarily (9/27/12)
			#drifterKML.Document.Folder.append(pointKML)
                        lstime = fltime
    
                # gather the coordinates for trackline
                coord = '%f,%f,0' % (event['longitude'], event['latitude'])
                # Check that the lat,lon are different from previous, and after deployment.
                # Then save it to the end of a string of coordinates
                if coord != lastcoord:
                    coords = coords + '\n' + blnk + coord
                    lastcoord = coord

    # with the last record, add either a deployment or current/final placemark
    if Ddeploy['newestLast']:
        placemark = Ddeploy.genKMLPoint(event)
        drifterKML.Document.append(etree.Comment("\nMost Recent Placemark\n"))
        drifterKML.Document.append(placemark)
    else:
        placemark = Ddeploy.genKMLPoint()
        drifterKML.Document.append(etree.Comment("\nDeployment Placemark\n"))
        drifterKML.Document.append(placemark)

    # create the trackline KML from the accumulated coordinates
    trackKML = Track(coords)
    
    # add the trackline to the end of the KML tree
    drifterKML.Document.append(trackKML)

    file.close()
    return drifterKML
   
def main():
    # testing some of the routines in this module
    
    # location and name of a drifter .dat file
    datfile = './cleandata.dat'
    
    # read in the drifter KML stub
    stubKML = readStub('./D93653.kml')
    # add data from the log files
    drifterKML = dat2KML(stubKML, datfile)
    
    # write out the complete KML
    fp = open('drifter.kml', 'w')
    fp.write(etree.tostring(drifterKML, pretty_print=True, xml_declaration=True))
    fp.close()


if __name__ == '__main__':
  main()  

