#!/usr/bin/python2.6

# Script to summarize previously generated KML data into a new KML file
#
# by eld 8/21/12
# eld 6/24/13:  updated for 2013
# eld 6/23/15:  updated for 2015

import sys, os, time
from lxml import etree
import genKMLstub, deployment_api, drifterdat_api

# for KML production
from pykml.factory import KML_ElementMaker as K
from pykml.factory import ATOM_ElementMaker as ATOM
from lxml.builder import E

# set contact information
KMLauthor = 'Elizabeth Dobbins'
homepage = 'http://www.ims.uaf.edu/artlab/'
NAMESPACE = './/{http://www.opengis.net/kml/2.2}'

# set trigger that separates final locations into separate file
SEPARATE_FINALS = True
final_title='Final drifter locations for 2015 Chukchi Sea deployments'
final_name='2015_final_locations'

def genFinalStub():
    # using information in the dictionary of deployment qualities, make KML
        
    # Start off with some background info
    root = K.kml(
            K.Document(
              ATOM.author(
                ATOM.name(KMLauthor)
              ),
              ATOM.link(href=homepage),
              K.name(final_title),
              K.description('To track the ultimate fate of all released drifters'),
            )
          )
    root.insert(0, etree.Comment('\nKML generated automatically by drifterSummaryKML.py\n'))
    doc = root.xpath('//default:Document', \
               namespaces={'gx': 'http://www.google.com/kml/ext/2.2',\
                           'atom': 'http://www.w3.org/2005/Atom',\
                           'default': 'http://www.opengis.net/kml/2.2'})
    
    # create and add the pieces of the stub
    doc[0].append(etree.Comment("\nStyle definition for drifter's positions\n"))
    doc[0].append(K.styleUrl('#drifter_info'))
    doc[0].append(genKMLstub.SurfaceStyle())
    return root

def genSummaryStub(Ddeploy):
    # Start off with some background info
    root = K.kml(
            K.Document(
              ATOM.author(
                ATOM.name(KMLauthor)
              ),
              ATOM.link(href=homepage),
              K.name(Ddeploy['name']),
              K.description(Ddeploy['purpose']),
            )
          )
    root.insert(0, etree.Comment('\nKML generated automatically by drifterSummaryKML.py\n'))
    doc = root.xpath('//default:Document', \
               namespaces={'gx': 'http://www.google.com/kml/ext/2.2',\
                           'atom': 'http://www.w3.org/2005/Atom',\
                           'default': 'http://www.opengis.net/kml/2.2'})
    
    # create and add the pieces of the stub
    doc[0].append(etree.Comment("\nStyle definition for drifter's positions\n"))
    doc[0].append(K.styleUrl('#drifter_info'))
    doc[0].append(genKMLstub.SurfaceStyle())
    doc[0].append(etree.Comment("\nStyle definition for drifter's trackline\n"))
    doc[0].append(genKMLstub.TrackStyle(Ddeploy))
    return root


def writeKML(drifterKML, id):
    # write out a KML file
    KMLfile = 'kml/' + id + '.kml'
    fp = open(KMLfile, 'w')
    fp.write(etree.tostring(drifterKML, pretty_print=True, xml_declaration=True))
    fp.close()


def main():
    # First read information about the set to summarize, then get data from each individual KML file.
    
    # Open the previously edited definitions file
    deffile = './setdef_2017.xml'         # file containing the definitions of sets of drifters
    defsXML = etree.XML(open(deffile, 'r').read())
    
    # create a summary file if all the final locations to be saved in one KML
    if SEPARATE_FINALS:
        finalKML = genFinalStub()

    # For each deployment, create a summary KML file and write it out
    for setdef in defsXML.xpath('set'):
        
        # fake a little deployment dictionary to pass info around
        deploy = deployment_api.Deployment()
        deploy['id'] = setdef.findtext('name')
        deploy['name'] = setdef.findtext('name')
        deploy['color'] = setdef.findtext('color')
        deploy['purpose'] = setdef.findtext('description')
        print deploy['id']
        
        # create an output KML stub
        outKML = genSummaryStub(deploy)
        
        ids =  setdef.findall('id')
        #ids =  [setdef.find('id')]   # TESTING (only first id)
        
        # reset the arrays that are tallying current postitions
        lats = []
        lons = []
        dtimes = []
        
        for drifterid in ids:
            print drifterid.text
            
            # read the KML of the individual drifter
            infile = './kml/' + drifterid.text  + '.kml'
            inKML = etree.XML(open(infile, 'r').read())
            
            # Assume that the trackline will be written into the summary
            # Won't be if it is a final location that is being written to another file
            SAVE_TRACK = True
            
            # loop through all the Placemarks in the KML - need to specify namespace :(
            for placemark in inKML.findall(NAMESPACE+"Placemark"):
                pname = placemark.findtext(NAMESPACE+"name")
                
                # find the deployment and/or current locations and add it to the summary KML
                if pname.startswith('Deployment'):
                    # save the placemark
                    outKML.Document.append(placemark)
                elif pname.startswith('Final'):
                    if SEPARATE_FINALS:
                        # save the placemark
                        finalKML.Document.append(placemark)
                        SAVE_TRACK = False
                    else:
                        # save the placemark
                        outKML.Document.append(placemark)
                    
                elif pname.startswith('Current'):
                    # save the placemark
                    outKML.Document.append(placemark)
                    
                    # now get the coords of the current location
                    # parse out the coordinates
                    coords = placemark.findtext(NAMESPACE+"coordinates")
                    lons.append( float(coords.split(',')[0]) )
                    lats.append( float(coords.split(',')[1]) )
                    # parse out the "Time of Last Fix:"
                    # Warning!  Superhack!!  If format of the description changes this will be broken
                    descr = placemark.findtext(NAMESPACE+"description")
                    where = descr.find('Time of Last Fix:')
                    dtimes.append( time.strptime(descr[where+22:where+41], "%Y-%m-%d %H:%M:%S") )
            
                # get the trackline and add it to the summary KML with a more specific name
                elif pname == 'Trackline' and SAVE_TRACK:
                    # save the placemark
                    pname = pname + ' for Drifter ' + drifterid.text
                    placemark.find(NAMESPACE+"name").text = pname
                    
                    # Shorten coordinate string to last few days
                    ncoords = 5*24  # 5 days assuming hourly sampling
                    linestring = placemark.find(NAMESPACE+"LineString")
                    coords = linestring.find(NAMESPACE+"coordinates").text
                    if coords is not None:
                        scoords = coords.split("\n")
                        ncoord = min(len(scoords), ncoords)
                        newcoords = scoords[0]
                        for c in scoords[1:ncoords]:
                            newcoords = newcoords + "\n          " + c
                        linestring.find(NAMESPACE+"coordinates").text = newcoords                            
                            
                    outKML.Document.append(placemark)
        
        # get the average current location (center of mass), put it in an event structure, and add it to the KML
        # if all the drifters have grounded, there won't be one
        if len(lats) > 1:
            com = drifterdat_api.Position()
            com['latitude'] = float(sum(lats)) / len(lats)
            com['longitude'] = float(sum(lons)) / len(lons)
            com['instrument'] = 'Current Center of Mass for ' + deploy['id']
            com['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S", min(dtimes))
            com.report()
            comKML = com.genKMLPoint(1)
            # check: print etree.tostring(comKML, pretty_print=True, xml_declaration=False)
            # finetune a couple of KML issues
            comKML[0].text = 'Center of ' + deploy['id']  # this should set the name to a unique value
            outKML.Document.append(comKML)
       
        # write out the summary KML
        writeKML(outKML, deploy['id'])
            
    if SEPARATE_FINALS:
        writeKML(finalKML, final_name)


if __name__ == '__main__':
  main()
