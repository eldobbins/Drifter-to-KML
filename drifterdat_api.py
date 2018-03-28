#!/usr/bin/python2.6

# Script to parse a line of a drifter data file, and store the contents in a
# dictionary, and make KML out of it.
#
# In raw data file, some lon,lat data are noisy, and there are many duplicate values.
# dft_proc2.m filters these out and writes columns 1:11 to a new data file (cleandata.dat)
#
# by eld 6/21/11
# ELD 7/25/12 : split line parsing into inheriting classes.
#

import time

from lxml import etree
from pykml.factory import KML_ElementMaker as K
from lxml.builder import E


class Position:

    def __init__(self):
      # Use a dictionary to track important information about the drifter's surfacing 
      # event.  Initialize entries and add abadflag to track if it was populated 
      # with reasonable data.
      self.Devent= {'instrument' : '',
          'timestamp' : '0000-00-00 00:00:00',
          'year' : 0,
          'latitude' : -999,
          'longitude' : -999,
          'voltage' : 0,
          'sst' : 0, 
          'badflag' : -999 }


    def __getitem__(self,keyname):
      # return the value associated with the provided key string
      return self.Devent[keyname]      


    def __setitem__(self, keyname, value):
        # sets the value of the key
        self.Devent[keyname] = value   


    def report(self):
      message = 'Drifter %s was at %f N, %f E at %s with voltage=%f and SST=%f' % (
                    self.Devent['instrument'], 
                    self.Devent['latitude'], 
                    self.Devent['longitude'], 
                    self.Devent['timestamp'], 
                    self.Devent['voltage'], 
                    self.Devent['sst'])
      print message


    def reportXML(self):
      eventXML = etree.Element('event')
      xml_to_add = [ 
          {'mtag': 'event_type', 'text': 'at surface' },
          {'mtag': 'instrument', 'text': self.Devent['instrument'] },
          {'mtag': 'latitude', 'text': self.Devent['latitude'] },
          {'mtag': 'longitude', 'text': self.Devent['longitude'] },
          {'mtag': 'timestamp', 'text': self.Devent['timestamp'] },
          {'mtag': 'voltage', 'text': self.Devent['voltage'] },
          {'mtag': 'SST', 'text': self.Devent['sst'] } ]
      addXMLdata(eventXML, xml_to_add)
      
      print etree.tostring(eventXML, pretty_print=True, xml_declaration=True)


    def genKMLPoint(self, DONAME=0):
      gtime = time.strptime(self.Devent['timestamp'], "%Y-%m-%d %H:%M:%S")
      # only want data label if at the beginning of a day, so test here
      if DONAME:
        name = time.strftime("%b-%d", gtime)
      else:
        name = " "

      # prep the description contents
      # using ElementMaker because pykml doesn't seem to do CDATA
      description = etree.Element('description')
      description.text = etree.CDATA('\
                     \n\t<h2>Drifter Position</h2>\
                     \n\t<p>\
                     \n\t<b>Instrument:</b> %s <br>\
                     \n\t<b>Time:</b> %s GMT<br>\
                     \n\t<b>Latitude:</b> %10.6f<br>\
                     \n\t<b>Longitude:</b> %10.6f<br>\
                     \n\t<p>\
                     \n\t<b>SST:</b> %10.2f<br>\
                     \n\t<b>Voltage:</b> %10.2f<br>\n\t'\
                     % (self.Devent['instrument'],\
                       self.Devent['timestamp'],\
                       self.Devent['latitude'],\
                       self.Devent['longitude'],\
                       self.Devent['sst'],\
                       self.Devent['voltage']\
                       ))

      timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", gtime)
      coords = str(self.Devent['longitude']) + ',' + str(self.Devent['latitude'])

      leaf = E.Placemark(
             E.name(name),
             description,
             E.TimeStamp(
               E.when(timestamp)
             ),
             E.styleUrl('#drifter_info'),
             E.Point(
               E.coordinates(coords)
             )
           )
      return leaf


class PositionDavis(Position):
    # Inherits most methods from class Position, but has specific methods to parse
    # a data line from a Davis type drifter data file.
    # The fields in the data file are as follows for 2009:
    #  1  Drifter serial number
    #  2  Year
    #  3  Month
    #  4  Day
    #  5  Hour
    #  6  Minute
    #  7  Second
    #  8  Longitude
    #  9  Latitude
    #  10 SST
    #  11 Battery Voltage
    #  12 ?
    #  13 GPS Good?
    #  14 age (many records have same date stamp because of how the data is sent via
    #    the satellite.  Age helps tell when it was actually collected)

    def populate(self, line):
      # All drifter locations in a single file, but parse 1 line at a time, and
      # add the data to the event structure.
      # The line must be in this specific format, space delimited:
      #     id year month day hour minute second lon lat [ sst voltage ]
      
      fields = line.split()
      
      self.Devent['instrument'] = fields[0].rstrip()
      self.Devent['latitude'] = float( fields[8].rstrip() )
      self.Devent['longitude'] = float( fields[7].rstrip() )
      self.Devent['year'] = float( fields[1].rstrip() )
      year = str( int ( float( fields[1].rstrip() ) ) )
      if year == '2009':
        # for some reason, this year the longitude was around the other direction
        self.Devent['longitude'] = -1* float( fields[7].rstrip() )

      month = str( int ( float( fields[2].rstrip() ) ) ).zfill(2)
      day = str( int ( float( fields[3].rstrip() ) ) ).zfill(2)
      hour = str( int ( float( fields[4].rstrip() ) ) ).zfill(2)
      minute = str( int ( float( fields[5].rstrip() ) ) ).zfill(2)
      second = str( int ( float( fields[6].rstrip() ) ) ).zfill(2)
      date = year + '-' + month + '-' + day + ' '
      time = hour + ':' + minute + ':' + second
      self.Devent['timestamp'] = date + time

      if len(fields) == 11:
        self.Devent['sst'] = float( fields[9].rstrip() )
        self.Devent['voltage'] = float( fields[10].rstrip() )
      else:
        self.Devent['sst'] = self.Devent['badflag']
        self.Devent['voltage'] = self.Devent['badflag']


class PositioniSPHERE(Position):
    # Inherits most methods from class Position, but has specific methods to parse
    # a data line from a MetOcean iSPHERE drifter data file downloaded via ftp.joubeh.com.

    def populate(self, line):
      # The line must be in this specific format, comma delimited:
      #     Received Date(GMT),Sent Date(GMT),Data Date(GMT),LATITUDE,LONGITUDE,FMTID,YEAR,MONTH,DAY,HOUR,MIN,SST,VBAT,GPS_DELAY,GPS_SN,TTFF,SBDTIME,Hex Data
      #       0                   1             2                3        4       5     6    7    8   9    10  11  12  ... 

      fields = line.split(',')
      if fields[0] == 'Received Date(GMT)':
        # this is the header line, so don't do anything
        return

      self.Devent['instrument'] = self.Devent['badflag']	#  Ack!  not included in the file?
      self.Devent['latitude'] = float( fields[3].rstrip() )
      self.Devent['longitude'] = float( fields[4].rstrip() )
      self.Devent['sst'] = float( fields[11].rstrip() )
      self.Devent['voltage'] = float( fields[12].rstrip() )
      self.Devent['timestamp'] = fields[2].rstrip()
      self.Devent['year'] = fields[6].rstrip()


class PositionMicrostarV2(Position):
    # Inherits most methods from class Position, but has specific methods to parse
    # a data line from a PacificGyre Microstar drifter data file downloaded via their API.
    # Handles data from the post- Dec. 2011 version of the API i.e.
    # wget --quiet -O SFOS-I-0001_v2.csv "http://api.pacificgyre.com/pgapi/getData.aspx?userName=SFOS&password=*****&format=CSV&deviceNames=SFOS-I-0001&startDate=08/20/2011&commentCharacters=%&delimiter=,"

    def populate(self, line):
      # The line must be in this specific format, comma delimited:
      #     CommID deviceName DateTime("%m/%d/%Y %H:%M:%S AM/PM")  GPSLat GPSLon submerged quality battery SST   ...
      #       0          1           2                              3        4       5       6       7      8  

      fields = line.split(',')
      if fields[0] == 'CommID':
        # this is the header line, so don't do anything
        return

      self.Devent['instrument'] = fields[1].rstrip()
      self.Devent['latitude'] = float( fields[3].rstrip() )
      self.Devent['longitude'] = float( fields[4].rstrip() )
      if fields[8].rstrip() != '':
        self.Devent['sst'] = float( fields[8].rstrip() )
      self.Devent['voltage'] = float( fields[7].rstrip() )

      date = time.strptime(fields[2].strip('"'), "%m/%d/%Y %I:%M:%S %p")
      self.Devent['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S', date)
      self.Devent['year'] = time.strftime('%Y', date)


class PositionMicrostar(Position):
    # Inherits most methods from class Position, but has specific methods to parse
    # a data line from a PacificGyre Microstar drifter data file downloaded via their API.
    # Handles data from the pre- Dec. 2011 version of the API i.e.
    # wget --quiet -O ${drifterid}.csv "http://api.pacificgyre.com/api/Getdata.aspx?devicelist=${drifterid}&startdate=8/17/2011%2000:00&enddate=12/31/2012%2023:59&uid=SFOS&pwd=******r&reportstyleid=1&reportid=3"

    def populate(self, line):
      # The line must be in this specific format, comma delimited:
      #     deviceName DateTime("%Y-%m-%d %H:%M:%S") time ? quality GPSLat GPSLon SST battery submerged ?
      #       0          1                            2   3  4       5       6    7    8  

      fields = line.split(',')
      self.Devent['instrument'] = fields[0].rstrip()
      self.Devent['timestamp'] = fields[1].rstrip()
      self.Devent['latitude'] = float( fields[5].rstrip() )
      self.Devent['longitude'] = float( fields[6].rstrip() )
      self.Devent['sst'] = float( fields[7].rstrip() )
      self.Devent['voltage'] = float( fields[8].rstrip() )

      date = time.strptime(fields[1].strip('"'), "%Y-%m-%d %H:%M:%S")
      self.Devent['year'] = date[0]


class PositionMicrostarManual(Position):
    # Inherits most methods from class Position, but has specific methods to parse
    # a data line from a PacificGyre Microstar drifter data file downloaded manually via their web interface.
    # Don't expect to use this so the code is not functional.  Just wanted a record

    def populate(self, line):
      # The line must be in this specific format, comma delimited:
      #     deviceName DateTime("%Y-%m-%d %H:%M:%S") time ? quality GPSLat GPSLon SST battery submerged ?
      #       0          1                            2   3  4       5       6    7    8  

      fields = line.split(',')
      # if downloaded manually via PG's web interface
      #date = time.strptime(fields[0].strip('"'), "%m/%d/%Y %I:%M:%S %p")
      #id = fields[10].strip('="')
      # if downloaded manually via PG's web interface
      ##import re
      #lat = fields[1].strip('="')
      ##print re.compile("(\W)").split(lat)  # to see what is in lat
      #lat = lat.split('\xb0')            # split using code for the degree sign
      #lm = float( lat[1].strip("'N") )   # minutes
      #latitude = float(lat[0]) + lm/60           # combine into decimal degrees
      #if lat[1].endswith('S'):
      #    latitude = -1*latitude
      #lon = fields[2].strip('="')
      ##print re.compile("(\W)").split(lon)  # to see what is in lat
      #lon = lon.split('\xb0')            # split using code for the degree sign
      #lm = float( lon[1].strip("'W") )   # minutes
      #longitude = float(lon[0]) + lm/60                  # combine into decimal degrees
      #if lon[1].endswith('W'):
      #    longitude = -1*longitude
      #newline = newline + ' ' + str(longitude) + ' ' + str(latitude)
      # if downloaded manually via PG's web interface
      #newline = newline + ' ' + fields[6] + ' ' + fields[5]
  

def main():
  YEAR = 2011   # 2009 or 2011, because files were different formats
  path = '../' + str(YEAR) + '/'
  if YEAR == 2009:
    filename = path + 'cleandata.dat'
  elif YEAR == 2011:
    filename = path + 'D107071.dat'
  
  file = open(filename,'r')
  event1 = Position()
  while True:
      line = file.readline()
      if not line: break
      event1.populate(line)
      event1.report()

  event1.reportXML()
  placemark = event1.genKMLPoint(1)
  print etree.tostring(placemark, pretty_print=True, xml_declaration=False)


if __name__ == '__main__':
  main()  
