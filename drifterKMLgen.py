#!/usr/bin/python2.6

# Script to process each drifter deployment.
#
# by eld 9/13/11
#

import sys, os
from lxml import etree
import deployment_api, drifterdat_api
# for KML production
import drifterdat2kml, genKMLstub



def makeKML(Ddeploy):
    # Write a single KML file that describes the entire deployment.
    # Generate the "stub" of the KML from information in the deployment dictionary
    # then call another function to add a trackline to it from its data file.
    
    # Set-up and generate basic stub of KML
    setEvent(Ddeploy)
    setDatafile(Ddeploy)
    setContacts(Ddeploy)
    Ddeploy.report()
    stubKML = genKMLstub.genStub(Ddeploy)
    
    # add the tracklines, etc, from the data file
    deploymentKML = drifterdat2kml.dat2KML(stubKML, Ddeploy)

    # write out the complete KML
    writeKML(deploymentKML, Ddeploy['id'])
    return deploymentKML


def writeKML(drifterKML, id):
    # write out a KML file
    KMLfile = 'kml/' + id + '.kml'
    fp = open(KMLfile, 'w')
    fp.write(etree.tostring(drifterKML, pretty_print=True, xml_declaration=True))
    fp.close()


def setEvent(Ddeploy):
    # create the object that includes the method for how to read event (i.e. position) data
    if Ddeploy['tag'] == 'Bering2009' or  Ddeploy['tag'] == 'Chukchi2011':
        Ddeploy['event'] = drifterdat_api.PositionDavis()
    elif Ddeploy['tag'] == 'Greenland2011':
        Ddeploy['event'] = drifterdat_api.PositionMicrostar()
    elif Ddeploy['tag'] == 'NSB_iSPHERE_2012':
        Ddeploy['event'] = drifterdat_api.PositioniSPHERE()
    else:
        Ddeploy['event'] = drifterdat_api.PositionMicrostarV2()


def setDatafile(Ddeploy):
    # Each deployment has a single datafile associated with it, so figure out
    # what it is.  When add a new deployment tag, will have to update this.
    if Ddeploy['tag'] == 'Bering2009':
        # there is only one for testing
        datfile = '../2009/cleandata.dat'
    elif Ddeploy['tag'] == 'Chukchi2011':
        # Could be D files for GPS positions, or A for Argos positions
        # Would rather use D if available because they have less scatter, but
        # they may not be available.
        path = '../' + Ddeploy['tag'] +'/'
        datfile = path + 'D' + Ddeploy['id'] + '.dat'
        if not os.path.isfile(datfile):
            datfile = path + 'A' + Ddeploy['id'] + '.dat'
        if not os.path.isfile(datfile):
            datfile = None
    else:
        path = '../' + Ddeploy['tag'] +'/'
        datfile = path + Ddeploy['drifter'] + '.csv'
    #else:
    #    sys.exit("Don't know where to look for data files.  Please update drifterKMLgen.py")
    
    Ddeploy['datafile'] = datfile


def setContacts(Ddeploy):
    # set all possible contact information
    contact1 = '<a href="https://www.sfos.uaf.edu/directory/faculty/weingartner/">Tom Weingartner</a>'
    contact2 = '<a href="https://www.sfos.uaf.edu/directory/faculty/danielson/">Seth Danielson</a>'
    contact3 = '<a href="https://www.sfos.uaf.edu/directory/faculty/winsor/">Peter Winsor</a>'
    contact4 = '<a href="http://www.north-slope.org/departments/wildlife-management">North Slope Borough, Department of Wildlife Management</a>'
    contact5 = '<a href="http://ine.uaf.edu/people/researchers/jeremy-kasper/">Jeremy Kasper</a>'
    
    contacts = ''
    # Use different contacts for different missions
    if Ddeploy['tag'] == 'Greenland2011' or Ddeploy['tag'] == 'test_microstar' or Ddeploy['tag'] == 'Greenland2012' or \
       Ddeploy['tag'] == 'Greenland2013' or Ddeploy['tag'] == 'Greenland2014' or Ddeploy['tag'] == 'BOEM2014' or \
       Ddeploy['tag'] == 'BOEM2015':
        contacts = contact3
    elif Ddeploy['tag'] == 'Chukchi2011' or Ddeploy['tag'] == 'BOEM2012-1' or Ddeploy['tag'] == 'BOEM2012-13':
        contacts =  contact1 + '<br>\n\
                    ' + contact2
    elif Ddeploy['tag'] == 'BOEM2012-2' or Ddeploy['tag'] == 'BOEM2013':
        contacts =  contact3 + '<br>\n\
                    ' + contact1
    elif Ddeploy['tag'] == 'NSB_iSPHERE_2012' or Ddeploy['tag'] == 'NSB_microstar_2012' or Ddeploy['tag'] == 'NSBW2013' or \
         Ddeploy['tag'] == 'NSBW2014' :
        contacts =  contact1 + '<br>\n\
                    ' + contact2 + '<br>\n\
                    ' + contact4
    elif Ddeploy['tag'] == 'IceTracker2015' or Ddeploy['tag'] == 'IceTracker2017':
        contacts =  contact5 + '<br>\n\
                    ' + contact3
    elif Ddeploy['tag'] == 'Kotzebue2015':
        contacts =  contact2
    Ddeploy['contacts'] =  contacts


def controlXML(tag):
    # This routine is to process the deployments described by an XML file, such as the
    # Microstar type drifter from Pacific Gyre that
    # Peter deployed in Greenland.
    
    # Info about the drifters is collected from a dowloaded data file, and
    # stored in a .xml format
    depfile = '../' + tag + '/deployments.xml'         # file containing the deployment definitions
    deployments = etree.XML(open(depfile, 'r').read())

    # For each deployment, create a KML file and write it out
    for d in deployments.xpath('Deployment'):
        deploy = deployment_api.Deployment()
        status = d.findtext('status')
        if status == 'OK' or status == 'done' or status == 'Done':
            id = d.findtext('id')
            deploy.populate(depfile, id)
            # create the KML
            drifterKML = makeKML(deploy)


def controlTXT(tag):
    # This is a routine to process the Davis type drifters, whose data are distributed
    # by Seth.
    
    # Info about all the drifters is collected in the DrifterStatus file.
    # Not all drifters described in that file have actually been deployed yet.
    filename = '../' + tag + '/DrifterStatus.txt'
    file = open(filename,'r')
    line = file.readline()  # first line is a header

    # Each line in the file describes a drifter deployment.  Examine all of them
    while True:
        line = file.readline()
        if not line: break
        fields = line.split(',')
        id = fields[0].strip()
    
        # Only process if data has actually been collected
        diw = fields[5].strip()
        if diw == 'NaN': diw = None
        else: diw = float(diw)
        if diw > 1:
            deploy = deployment_api.DeploymentFromTXT()
            deploy.populate(filename, id)
            deploy['tag'] = tag
            # create the KML
            drifterKML = makeKML(deploy)
        else:
            msg = ('Deployment %s not processed because there is not enough data' % id)
            print msg

    file.close()    


def main():
    print 'starting ...'

    # first process the deployments that are described by XML files
    # 2012:  tags = ['NSB_iSPHERE_2012', 'Greenland2012', 'NSB_microstar_2012', 'BOEM2012-1', 'BOEM2012-2']
    # early 2013:  tags = ['BOEM2012-1', 'BOEM2012-13', 'NSBW2013', 'Greenland2013']
    # late 2013:   tags = ['NSBW2013', 'Greenland2013', 'BOEM2013']
    # early 2014:  tags = ['Greenland2014', 'NSBW2014']
    # early 2015:  tags = ['BOEM2014', 'NSBW2014', 'IceTracker2015']
    # 2016:        tags = ['BOEM2015', 'IceTracker2015', 'Kotzebue2015']
    # early 2017:  tags = ['IceTracker2015', 'IceTracker2017']
    tags = ['IceTracker2017']
    for tag in tags:
        controlXML(tag)

    # next process the deployments that are described by DrifterStatus files
    #tags = ['Chukchi2011']
    #for tag in tags:
    #    controlTXT(tag)


if __name__ == '__main__':
  main()
