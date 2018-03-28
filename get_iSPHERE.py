#!/usr/bin/python2.6
#
#  A script to download iSPHERE drifter data files from the company (Joubeh) who processed the
#  data packets sent via Iridium.  The data are stored on their ftp server, each day and instrument
#  in a separate file.
#
#  Since there are 26 drifters, that's going to ge a lot of files, so this routine checks to see
#  if the file was already downloaded before fetching it.  It also groups the files in subdirectories
#  by instrument id to keep things tidy.  Then it concatinates all the individual .csv files of
#  an instrument into a single file that can be processed into a KML file.
#
#  ELD
#  7/30/2012
#

from lxml import etree
import os, sys, time, subprocess, glob, shutil

from ftplib import FTP
# http://docs.python.org/library/ftplib.html


tag = 'NSB_iSPHERE_2012'
thereFiles = []                     # list of .csv files on the server
origDir = '../' + tag + '/orig/'    # Where downloaded files will go.  On artweb, should probably be /var/opt/...
finalDir = '../' + tag + '/'        # Where concatinated files will go.  On artweb, should probably be ~/drifters/NSB...


def key_func(s):
    # translates a filename into a timestamp that can be sorted
    # filenames look like:  ../NSB_iSPHERE_2012/orig/300234011561080/300234011561080_2012-07-27.csv
    name = s.split('/').pop()
    date = name.split('_').pop().strip('.csv')
    return time.strptime(date,"%Y-%m-%d")
  

def cmp_func(s1, s2):
    # a function that is used by the list sort method to sort filenames by the date embedded in them
    k1, k2 = key_func(s1), key_func(s2)
    return -1 if k1 < k2 else 0 if k1 == k2 else +1


def thereFilesNames(line):
    # Will be called on each line of ftp's list results to get .csv filenames
    parts = line.split()
    if len(parts) <  8:
        pass
    else:
        if parts[8].endswith('csv'):
            thereFiles.append(parts[8])


def getCSVFromJoubeh(GETALL=True):
    # Uses ftp library to login to ftp.joubeh.com and download .csv files
    # GETALL : optional argument.  Set to False if only want new files
    
    # Open connection
    ftp = FTP('ftp.joubeh.com')
    ftp.login('north', 'northslope')               
    
    # Examples:
    #ftp.retrlines('LIST')     # list directory contents
    # Since is an ASCII file, could use retrlines, but that drops the newline characters, 
    # and you have to write your callback function to add them back in.
    # retrbinary results in a file that should be identical to the original file on the server.
    # http://www.velocityreviews.com/forums/t398555-re-ftplib-and-retrbinary-or-retrlines-losing-newlinecharacters-in-my-log-files.html
    #filename = '300234011160180_2012-07-27.csv'
    #ftp.retrbinary('RETR ' + filename, open(filename, 'wb').write)

    # Get all files.  Names are changing all the time, so need to list anew.
    ftp.retrlines('LIST', thereFilesNames)
    
    # restrict the list if you only want files that haven't been downloaded before
    if GETALL:
        filenames = thereFiles
    else:
        # get a list of all the files that have been downloaded into the subdirectories
        hereFiles = []
        instruments = os.walk(origDir).next()[1]  # the names of all the instrument subdirectories
        for instr in instruments:
            hereFiles.extend( os.listdir(origDir + instr) )   # add the names of file found
        filenames = list(set(thereFiles) - set(hereFiles))  # files that are there but not here
        
    for file in filenames:
        fd = open(file, 'wb')
        print ('Downloading file %s for %s' % (file, tag) )
        ftp.retrbinary("RETR " + file, fd.write)
        
        # For our use, remove the date stamp.
        #newname = file.split('_')[0] + '.csv'
        
        # move the files into a storage directory for each instrument
        # create a directory if needed
        newDir = origDir + '/' + file.split('_')[0] + '/'
        if not os.path.exists(newDir):
            os.makedirs(newDir)
        os.rename(file, newDir + file)
       
    ftp.close()


def combineCSV(filenames, outfile):
    # combine all the CSV files
    # filenames : list of filenames in the order you want (i.e. sorted newest to oldest)
    # Note: iSPHERE data files all start with 1 line of header
    
    print ('Writing to %s' % outfile)
    fout=open(outfile,"w")

    # first file:
    for line in open(filenames[0]):
        fout.write(line)
    # take that first filename off the stack
    del filenames[0]
    # files are missing newline at end, so hack that in
    fout.write('\r\n')
    
    # now the rest, skipping the first (header) line:    
    for name in filenames:
        f = open(name)
        f.next() # skip the header
        for line in f:
             fout.write(line)
        f.close() # not really needed
        fout.write('\r\n')

    fout.close()

    
def main():
    #getCSVFromJoubeh()      # download all files
    getCSVFromJoubeh(False) # download only new files
    
    instruments = os.walk(origDir).next()[1]  # the names of all the instrument subdirectories
    for instr in instruments:
        # make a list of filenames in the directory, and sort from newest to oldest based on the
        # timestamp embedded in the filename
        filenames =  glob.glob(origDir + instr + '/*.csv')
        filenames.sort(cmp=cmp_func)
        filenames.reverse()
        # send that list to be combined into a single file
        outfile = finalDir + instr + '.csv'
        combineCSV(filenames, outfile)
        
        # Orignal files are organized by transmission time rather than collection time, so they
        # need to be sorted.  Also 00:00 - 03:00 records are duplicated in daily original files
        # so those duplicate records need to be filtered.
        # Complex command accounts for header line (which sort ordinarily can't deal with).
        # subprocess.call() is more modern equivalent of os.system, but I can't figure it out.
        command = 'cat %s | (read -r; printf "%%s\\n" "$REPLY"; sort -t"," -k3 -ru) > tmp.csv' % outfile
        os.system(command)
        os.rename('tmp.csv', outfile)

        # copy final file to the distribution directory
        disdir = '/var/www/html/artlab/data/csv/drifters'
        if os.path.exists(disdir):
             shutil.copy2(outfile, disdir)

    return


if __name__ == '__main__':
  main()

