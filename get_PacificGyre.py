#!/usr/bin/python2.6
#
# Function to download groups of drifters via the Pacific Gype api.  We have many different
# login accounts and many separate projects, so those combinations need to be defined at the
# beginning.  An account can have several different projects (tags) associated with it, but
# not visa versa because the same deployments.xml file is used to define all the drifters
# associated with a project, and deployments.xml doesn't specify the account info.
#
# Because (as of 2012) a single drifter can be redeployed, only the start date is used to
# confine the limits of the download.  Make sure the earliest start date is first in the
# deployments.xml file. (Hack)
#
# ELD
# 9/6/12
#

from lxml import etree
import os, sys, time, subprocess, shutil

# Define the accounts from which to download
accounts = []
#accounts.append({ 'tag': 'test_microstar', 'username':'SFOS', 'password’:’*****’})  # for testing
#accounts.append({ 'tag': 'BOEM2012-1', 'username':'SDSFOS', 'password':'*****'})
#accounts.append({ 'tag': 'NSB_microstar_2012', 'username':'NSBW', 'password’:’*****’})
#accounts.append({ 'tag': 'Greenland2012', 'username':'SFOS', 'password':'*****'})
#accounts.append({ 'tag': 'BOEM2012-2', 'username':'SFOS', 'password':'*****'})
#accounts.append({ 'tag': 'NSBW2013', 'username':'NSBW', 'password':'*****'})
#accounts.append({ 'tag': 'Greenland2013', 'username':'SFOS', 'password':'*****'})
#accounts.append({ 'tag': 'BOEM2013', 'username':'SFOS', 'password':'*****'})
#accounts.append({ 'tag': 'Greenland2014', 'username':'SFOS', 'password':'*****'})
#accounts.append({ 'tag': 'NSBW2014', 'username':'NSBW', 'password':'*****'})
#accounts.append({ 'tag': 'BOEM2014', 'username':'SFOS', 'password’:’******’})
#accounts.append({ 'tag': 'IceTracker2015', 'username':'SFOS', 'password':'*****'})
#accounts.append({ 'tag': 'Kotzebue2015', 'username':'SDSFOS', 'password':'*****'})
#accounts.append({ 'tag': 'BOEM2015', 'username':'SFOS', 'password':'*****'})
accounts.append({ 'tag': 'IceTracker2017', 'username':'SFOS', 'password':'*****'})

def main():

    # For each set of deployments
    for account in accounts:
        tag = account['tag']
        doneids = []  # initialize list that tracks what files have already been downloaded

        # Identify and load the file containing the deployment definitions
        depfile = '../' + tag + '/deployments.xml'
        if not os.path.isfile(depfile):
            sys.exit('Cannot find deployment definitions file %s ' % depfile)
        deployments = etree.XML(open(depfile, 'r').read())
    
        # for each deployment described in the file
        for d in deployments.xpath('Deployment'):
            # get relevant info from deployment definitions file
            drifterid = d.findtext('drifter')
            starttime = time.strptime(d.findtext('start'), "%Y-%m-%d %H:%M:%S")
            startDate = time.strftime('%m/%d/%Y', starttime)  # should be:08/17/2011
            
            if drifterid not in doneids:
            
                # build the wget command
                command = ["wget"]
                downname = drifterid + '_orig.csv'
                apicmd = 'https://api.pacificgyre.com/pgapi/getData.aspx?userName=' + account['username'] + \
                     '&password=' + account['password'] + '&format=CSV&deviceNames='\
                      + drifterid +'&startDate=' + startDate + '&commentCharacters=%&delimiter=,'
                args = ["--quiet", "-O", downname, apicmd]
                command.extend(args)
                #print command
                
                print ('Downloading drifter %s for %s' % (drifterid, tag) )
                subprocess.call(command)
        
                # Now clean the file by removing records with low GPS quality using local shell script
                if os.path.isfile(downname):
                    cleanname = drifterid + '.csv'
                    command = ["./clean_microstar.sh"]
                    args = [downname, cleanname]
                    command.extend(args)
                    subprocess.call(command)
                    
                    # copy final file to the distribution directory
                    # need different name because some drifters deployed in different years
                    # and using the same name clobbers the older year.
                    # disabled distribution of NSBW data 8/27/14 cause Leandra asked us not to
                    if not tag.startswith('NSB'):
                        disdir = '/var/www/html/artlab/data/csv/drifters/'
                        distname = disdir + drifterid + '_' + tag + '.csv'
                        if os.path.exists(disdir):
                            shutil.copy2(cleanname, distname)
                    
                    # and move both files to the storage
                    os.rename(downname, '../' + tag + '/orig/' + downname)
                    os.rename(cleanname, '../' + tag + '/' + cleanname )
                else:
                   sys.exit('Download of %s failed.  Please, fix the problem' % downname )
                   
                doneids.append(drifterid)

    return

if __name__ == '__main__':
  main()
