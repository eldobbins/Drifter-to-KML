#!/usr/bin/python2.6

# Generate the basic KML needed to describe a drifter deployment.
#
# by eld 4/8/11
#

from lxml import etree
from pykml.factory import KML_ElementMaker as K
from pykml.factory import ATOM_ElementMaker as ATOM
from lxml.builder import E
import deployment_api, drifterdat_api, drifterdat2kml
import time

checkNone = (lambda x, y: x if x is not None else y)

# set contact information
KMLauthor = 'Elizabeth Dobbins'
homepage = 'http://www.ims.uaf.edu/artlab/'


def Camera(Ddeploy):
    # generate the camera tree
    
    # If XML had lat,lon for deployment location, use that.  Otherwise, use generic
    lat = str( checkNone( Ddeploy['latitude'], 71.61020799525069) )
    lon = str( checkNone( Ddeploy['longitude'], -161.9384752350831) )
    camera = K.Camera(
                K.longitude(lon),
                K.latitude(lat),
                K.altitude("500000"),
                K.heading("0"),
                K.tilt("0"),
                K.roll("0"),
                K.altitudeMode("absolute"),
             )
    return camera
    
def SurfaceStyle():
    # create the style for placemarks marking drifter surfacing events. 
    # using ElementMaker because pykml doesn't seem to do attributes, or CDATA
    
    # prep the balloon contents
    balloon = etree.Element('text')
    balloon.text = etree.CDATA('\n\
                    <table width="300"><tr><td>\n\
                    <h2>$[name]</h2>\n\
                    <p>\n\
                    $[description]\n\
                    </td></tr></table>\n\t\t')
    
    # make the style.  Note use double quotes in attribute definition (id) or hash will disappear
    style = E.Style(
                E.IconStyle(
                    E.Icon(E.href('http://maps.google.com/mapfiles/kml/pal4/icon25.png'))
                ),
                E.BalloonStyle(
                    balloon
                ),
                {"id" : "drifter_info"}
            )
    return style
    
def TrackStyle(Ddeploy):
    # create the style for the drifter's trackline. 
    # using ElementMaker because pykml doesn't seem to do attributes
    # make the style - no balloon, white line, no labels
    style = E.Style(
                E.LabelStyle(
                    E.scale('0.0')
                ),
                E.LineStyle(
                    E.color(Ddeploy['color']),
                    E.colorMode('normal'),
                    E.width('2.0')
                ),
                E.BalloonStyle(
                    E.displaymode('hide')
                ),
                {"id" : "trackline"}
            )
    return style

def Folder(Ddeploy):
    # Make a folder to put the drifter's points into
    # Note: for now the deployment Placemark is going in here, but it may move out
    # later.
    folder = K.Folder(
                K.name('Drifter positions'),
                K.description('Drifter positions at roughly daily intervals'),
                K.Style(
                    K.ListStyle(
                        K.listItemType('checkHideChildren')
                    )
                )
            )
    return folder
    

def genStub(Ddeploy):
    # using information in the dictionary of deployment qualities, make KML
    
    timestamp = time.strptime(Ddeploy['startstr'], '%Y-%m-%d %H:%M:%S')
    date = time.strftime('%b. %Y', timestamp)
    description = 'The trackline for the %s deployment of %s' % (
                    Ddeploy['area'], 
                    Ddeploy['name'])
    #print description
    
    # Start off with some background info
    root = K.kml(
            K.Document(
              ATOM.author(
                ATOM.name(KMLauthor)
              ),
              ATOM.link(href=homepage),
              K.name(Ddeploy['name']),
              K.description(description),
            )
          )
    root.insert(0, etree.Comment('\nKML generated automatically by genKMLstub.py\n'))
    doc = root.xpath('//default:Document', \
               namespaces={'gx': 'http://www.google.com/kml/ext/2.2',\
                           'atom': 'http://www.w3.org/2005/Atom',\
                           'default': 'http://www.opengis.net/kml/2.2'})
    
    # create and add the pieces of the stub
    doc[0].append(etree.Comment("\nStyle definition for drifter's positions\n"))
    doc[0].append(K.styleUrl('#drifter_info'))
    doc[0].append(SurfaceStyle())
    doc[0].append(etree.Comment("\nStyle definition for drifter's trackline\n"))
    doc[0].append(TrackStyle(Ddeploy))
    doc[0].append(etree.Comment("\nEach drifter position has data associated with it.  To display that\n\
data, need separate placemarks for each.  Contain in a Folder for\n\
cleanliness.\n"))
    doc[0].append(Folder(Ddeploy))
    return root
   

def main():
    # test genstub
    
    # first with locally defined dictionary
    Ddeployment = {'id' : 'test',
            'drifter' : 'tester',
            'name' : 'This is a testy tester',
            'startstr' : '0000-00-00 00:00:00',
            'endstr' : '0000-00-00 00:00:00',
            'latitude' : None,
            'longitude' : None,
            'area' : 'nowhere',
            'purpose' :'testing',
           }
    drifterKML = genStub(Ddeployment)    
    #print etree.tostring(drifterKML, pretty_print=True)
    
    # test with reading
    filename = 'deployments.xml'
    id = 'D93653'
    Ddeployment = deployment_api.Deployment()
    Ddeployment.populate(filename, id)
    drifterKML = genStub(Ddeployment)
    
    # output it
    print etree.tostring(drifterKML, pretty_print=True)
    #KMLfile = id + '.kml'
    #fp = open(KMLfile, 'w')
    #fp.write(etree.tostring(drifterKML, pretty_print=True, xml_declaration=True))
    #fp.close()  


if __name__ == '__main__':
  main()  

   
