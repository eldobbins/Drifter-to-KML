#!/usr/bin/python2.6

# Script to create a dictionary to hold deployment info
# and some functions to manipulate it.
#
# by eld 6/21/11
# ELD 7/25/12 : make XML the default and split text parsing into an inheriting class.
#

import time, shutil
from lxml import etree
from pykml.factory import KML_ElementMaker as K
from lxml.builder import E


class Deployment:
    
    def __init__(self):
        # Use a dictionary to track important information about the drifter
        # deployments performed by UAF.   Initialize entries.
        self.Ddeployment = {'id' : None,
            'drifter' : '',
            'name' : '',
            'startstr' : '0000-00-00 00:00:00',
            'endstr' : '0000-00-00 00:00:00',
            'latitude' : None,
            'longitude' : None,
            'area' : '',
            'purpose' : '',
            'status' : '',
            'tag' : '',
            'color' : 'FFFFFFFF',
            'newestLast' : False,   # Davis = new data at end;  Microstar = new data at top
            'datafile' : '',        # this depends on variety of tags, so set it in drifterKMLgen.py
            'contacts' : '',         # this depends on variety of tags, so set it in drifterKMLgen.py
            'event' : 'None'        # this depends on variety of tags, so set it in drifterKMLgen.py
           }


    def __getitem__(self,keyname):
        # return the value associated with the provided key string
        return self.Ddeployment[keyname]      


    def __setitem__(self, keyname, value):
        # sets the value of the key
        self.Ddeployment[keyname] = value   


    def populate(self, filename, id):
        # populate the dictionary with information from the deployment file that
        # matches the desired id.
        # self : the deployment object
        # filename : the file that contains info about the deployments (XML)
        # id : the id of the drifter for which info is needed
        # Note: default is to use XML file.  If using DrifterStatus.txt, there is an inherited method below.
        
        # this file contains info about how deployments are defined.  Load XML
        deployments = etree.XML(open(filename, 'r').read())
      
        # loop through entries to find a match
        for d in deployments.xpath('Deployment'):
          if id == d.findtext('id'):
              self.Ddeployment['id'] = id
              self.Ddeployment['drifter'] = d.findtext('drifter')
              self.Ddeployment['name'] = d.findtext('name')
              self.Ddeployment['startstr'] = d.findtext('start')
              self.Ddeployment['endstr'] = d.findtext('end')
              self.Ddeployment['latitude'] = d.findtext('latitude')
              self.Ddeployment['longitude'] = d.findtext('longitude')
              self.Ddeployment['area'] = d.findtext('area')
              self.Ddeployment['purpose'] = d.findtext('purpose')
              self.Ddeployment['tag'] = d.findtext('tag')
              self.Ddeployment['status'] = d.findtext('status')
              self.Ddeployment['color'] = d.findtext('color')


    def report(self):
        # quickie check of deployment's information
        message = 'Deployment "%s" using %s was from %s to %s' % (
                    self.Ddeployment['id'], 
                    self.Ddeployment['drifter'], 
                    self.Ddeployment['startstr'], 
                    self.Ddeployment['endstr'])
        print message


    def genKMLPoint(self, event=None):
        # makes a KML marker for either a deployment, current, or final location.  If
        # an argument is passed it is assumed to 
        # be the current/final location, and if they are missing, the deployment location is used.
        # event  :  an optional drifterdat postion dictionary object.  
        
        # set-up either deployment or current or final by toggling off of event and status
        dtime = self.Ddeployment['startstr']
        if event == None:
            lat = self.Ddeployment['latitude']
            lon = self.Ddeployment['longitude']
            time = dtime
            keyword = 'Deployment'
            if self.Ddeployment['tag'].find('IceTracker'):
                # Ice Trackers not moving much and full-sized markers block current location pins
                icon = 'http://maps.google.com/mapfiles/kml/paddle/grn-blank_maps.png'
            else:
                icon = 'http://maps.google.com/mapfiles/kml/shapes/open-diamond.png'
        else:
            lat = str( event['latitude'] )
            lon = str( event['longitude'] )
            time = str( event['timestamp'] )
            # Mark currently functioning drifters with green thumbtacks, and failed
            # drifters with red dots.
            if self.Ddeployment['status'] == 'OK':
                keyword = 'Current'
                icon = 'http://maps.google.com/mapfiles/kml/paddle/ltblu-blank_maps.png'
            else:
                keyword = 'Final'
                icon = 'http://maps.google.com/mapfiles/kml/pal4/icon49.png'

        # set common variables to be inserted into KML
        contacts = self.Ddeployment['contacts']
        name = keyword + ' Location of Drifter ' + self.Ddeployment['drifter']
        cstr = lon + ',' + lat + ',5'
        snippet = keyword + ' location of the drifter'
        
        # prep the description
        destxt = '\n\
                    <b>Area:</b>  ' + self.Ddeployment['area'] + '<br \>\n\
                    <b>Purpose:</b>  ' + self.Ddeployment['purpose'] + '<br \>\n\
                    <b>Time Deployed:</b>    ' + dtime + ' <br \>\n\
                    <b>Contact:</b>  <br \>\n\
                    ' + contacts + '<br \>\n\
                    <p>\n'
        if keyword is not 'Deployment':
            destxt = destxt + '\
                    <b>' + keyword + ' Latitude:</b>  ' + lat + ' <br \>\n\
                    <b>' + keyword + ' Longitude:</b> ' + lon + ' <br \>\n\
                    <b>Time of Last Fix:</b> ' + time + ' <br \>\n\
                    '
        description = etree.Element('description')
        description.text = etree.CDATA(destxt)
    
        # build the KML
        leaf = E.Placemark(
                        E.name(name),
                        E.snippet(snippet),
                        description,
                        E.styleUrl('#drifter_info'),
                        E.Style(
                            E.IconStyle(
                                E.Icon(
                                    E.href(icon)
                                )
                            )
                        ),
                        E.Point(
                            E.coordinates(cstr)
                        )
                    )
        
        return leaf


class DeploymentFromTXT(Deployment):
    # Inherits most methods from class Deployment, but has specific methods to get deployment
    # information from an text file with a specific format ('DrifterStatus.txt').

    def populate(self, filename, id):
        # populate the dictionary with information from the deployment file that
        # matches the desired id.
        # self : the deployment object
        # filename : the file that contains info about the deployments (txt)
        # id : the id of the drifter for which info is needed
        
        #  The Davis drifters have newest data appended to the end, so track that 
        self.Ddeployment['newestLast'] = True
        
        # this is Seth's status file downloaded with the 2011 Chukchi Sea drifters
        file = open(filename,'r')
        line = file.readline()  # first line is a header
        while True:
          line = file.readline()
          if not line: break
          fields = line.split(',')
          if fields[0].strip() == id:
              self.Ddeployment['id'] = id
              self.Ddeployment['drifter'] = fields[0].strip()[-3:]
              # dates are different format so standardize them
              timestamp = time.strptime(fields[3].strip(), '%d-%b-%Y %H:%M:%S')
              self.Ddeployment['startstr'] = time.strftime('%Y-%m-%d %H:%M:%S', timestamp)
              timestamp = time.strptime(fields[2].strip(), '%d-%b-%Y %H:%M:%S')
              self.Ddeployment['endstr'] = time.strftime('%Y-%m-%d %H:%M:%S', timestamp)
              self.Ddeployment['status'] = fields[6].strip()
              # hardcode this stuff
              #self.Ddeployment['latitude'] = There aren't lon,lat in the DrifterStatus file
              #self.Ddeployment['longitude'] = There aren't lon,lat in the DrifterStatus file
              self.Ddeployment['name'] = 'Drifter #' + id + ', Aug. 2011'
              self.Ddeployment['area'] = 'Chukchi Sea'
              self.Ddeployment['purpose'] = 'To measure current shear in \
the upper ocean and its relation to seasonal changes in stratification and winds.'
              self.Ddeployment['color'] = 'FFFFFFFF'
              break

        file.close()
 
    
def main():
  # filename = 'deployments.xml'
  filename = '../Chukchi2011/DrifterStatus.txt'
  id = '107071'

  # test population of deployment info
  dep1 = DeploymentFromTXT()
  dep1.populate(filename, id)
  dep1['tag'] = 'Chukchi2011'
  if dep1['id'] == None:
      print 'Deployment "%s" not found' % id
  else:
      dep1.report()

  # test copying log files
  #logbase = '../'                     # base of where the original log files are 
  #dep1.getlogs(logbase)
  
  # test making KML
  drifterKML = dep1.makeKML()
  print etree.tostring(drifterKML, pretty_print=True)
  
if __name__ == '__main__':
  main()  
