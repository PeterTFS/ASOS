#WIMS_Query: This script will collect WIMS data from the xsql system for the current or previous day
#The data will then be processed to filter stations by 7G or 8G fuel model and calculate percentile range values

# import modules
import logging
import datetime
import urllib
import os
import shutil
import csv
import collections
import sys
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ElementTree
from itertools import groupby

# Define primary workspace based on location of script
wsRoot = os.getcwd()
ws = os.path.join(wsRoot, "WIMS_Data")

# set up date information
today = datetime.datetime.today()
one_day = datetime.timedelta(days=1)

yesterday = today - one_day
tomorrow = today + one_day

# Date formatting information for later. Date strings will produce date field in points
#rawFormat = "%m%d%y"
#fieldFormat = "%m/%d/%Y"

# set up date for query, dd-Mon-yy
hour = int(today.strftime("%H"))
format1 = "%d-%b-%y"

#set up logger
if hour > 1 and hour < 17:
    filemode = 'w'
else:
    filemode = 'a'

logging.basicConfig(filename=os.path.join(wsRoot, 'WIMS_Query_log.log'),
                    format='%(asctime)s   %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S%p',
                    filemode=filemode,
                    level=logging.INFO)

logging.info("Begin WIMS Data processing...")
print "Begin WIMS Data processing..."

# if query is run before 3 p.m. central time, check for data from yesterday, otherwise check for today's data
##if hour < 15:
##    start = yesterday.strftime(format1)
##    date = yesterday.strftime("%Y%m%d")
##    archiveYear = yesterday.strftime("%Y")
##    logging.info("Collecting data from yesterday, %s", start)
##    print "Collecting data from yesterday, " + start
##else:
##    start = today.strftime(format1)
##    date = today.strftime("%Y%m%d")
##    archiveYear = today.strftime("%Y")
##    logging.info("Collecting data from today, %s", start)
##    print "Collecting data from today, " + start

##
start = today.strftime(format1)
date = today.strftime("%Y%m%d")
##archiveYear = today.strftime("%Y")
##logging.info("Collecting data from today, %s", start)
##print "Collecting data from today, " + start
end = start
# set up folder paths and check to see if they exist
rawFolder = os.path.join(ws, "Raw_Data")
if not os.path.exists(rawFolder):
    os.makedirs(rawFolder)

# define xml file locations
#xmlweather = os.path.join(rawFolder, "tx_weather_obs.xml")
##xmlobs = os.path.join(rawFolder, "tx_nfdr_obs.xml")
##xmlfcst = os.path.join(rawFolder, "tx_nfdr_fcst.xml")

# Get reponse from WIMS server
serverResponse = urllib.urlopen('https://fam.nwcg.gov/wims/xsql/obs.xsql')


Stations = {"KDHT": 418702,
            "KAMA": 418803,
            "KSPS": 419302,
            "KINK": 417501,
            "KFST": 417601,
            "KLBB": 419002,
            "KJCT": 417803,
            "KSJT": 419204,
            "KELP": 416901,
            "KDRT": 418003,
            "KHDO": 418103,
            "KSSF": 418104,
            "KCOT": 418402,
            "KALI": 418504,
            "KBAZ": 418105,
            "KCLL": 413901,
#                "KCRS": 412001,
            "KTYR": 411701,
            "KTRL": 419703,
            "KDTO": 419603,
            "KMWL": 419404}
# Check reponse code
#Stations = {"KDHT": 418702}

for station,stationid in Stations.items():
    # If WIMS server is available, download xml files. Otherwise, exit process.
    if serverResponse.getcode() == 200:
    # Two ways to get the XML file (1. downloading a file 2. get the data into memory)
##        xmlweather = os.path.join(rawFolder, "wims_obs_" + str(stationid) + ".xml")
##        xmlf = urllib.urlretrieve(queryUrl,xmlweather)
##        tree = ET.parse(xmlweather)
##        root = tree.getroot()
##        (start,end) =('16-Oct-17', '16-Oct-17')
        #queryUrl = "https://fam.nwcg.gov/wims/xsql/obs.xsql?stn=%s&type=R&start=%s&end=%s&user=pyang"%(stationid,start,end)
        queryUrl = "https://fam.nwcg.gov/wims/xsql/obs.xsql?stn=%s&start=%s&end=%s&user=pyang"%(stationid,start,end)
        #Should only
        #queryUrl = "https://fam.nwcg.gov/wims/xsql/obs.xsql?stn=%s&type=O&start=%s&end=%s&user=pyang"%(stationid,start,end)
        print queryUrl
        #Here need to test the downloading is successful or not, if can not get today's "O" record, the program can be re-run to re-upload the FW to WIMS Alternate Gateway
        #try:
        content = urllib2.urlopen(url = queryUrl)
        result = content.read()
        #print result
        #Here is a little trick with the ElementTree
        tree = ElementTree(fromstring(result))
        root = tree.getroot()
        if root.findall('row'):
            #print "there are records"
            for row in root.findall('row'):
                num = row.get('num')
                print 'num:',num
                sta_id = row.find('sta_id').text
                sta_nm = row.find('sta_nm').text
                obs_dt = row.find('obs_dt').text
                obs_tm = row.find('obs_tm').text
                obs_type = row.find('obs_type').text
                print obs_dt,obs_tm,obs_type
        #Here if there is no record for today, re-run the propoer process!
        else:
            print "no observation today"

