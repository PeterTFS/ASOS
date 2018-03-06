#-------------------------------------------------------------------------------
# Name:      ASOS2WIMS_TX.py
# Purpose:   Compile ASOS weather into FW9 for feeding WIMS
# Author:    Peter Yang
# Created:   01/10/2015
#-------------------------------------------------------------------------------
import time
import os
import sys
import re
import csv
import string
import urllib
import shutil
import pandas
import math
import logging
from datetime import date, datetime
from dateutil import tz
import smtplib
from itertools import groupby

#-------------------------------------------------------------------------------
# Start from here
#-------------------------------------------------------------------------------
# Set up working space
#workspace='c:\\DEV\\ASOS\\'

# Define primary workspace based on location of script
workspace = os.getcwd()
#The downloaded file and processed file will be in the HIST directory
ASOSArchive = os.path.join(workspace, "CSV")
FW9Archive  = os.path.join(workspace, "FW9")
LOGArchive  = os.path.join(workspace, "LOG")

if not os.path.exists(ASOSArchive):
    os.makedirs(ASOSArchive)
if not os.path.exists(FW9Archive):
    os.makedirs(FW9Archive)
if not os.path.exists(LOGArchive):
    os.makedirs(LOGArchive)

#Set up a logger for logging the running information
logging.basicConfig(filename=os.path.join(workspace,"ASOS4WIMS.log"),
                    format='%(asctime)s   %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S%p',
                    filemode='w',
                    level=logging.INFO)
#Record a start time
logging.info("Start ASOS processing for %s", datetime.today().strftime("%Y%m%d"))

fileWF9 = os.path.join(workspace, "tx-asos.fw9")
#for each day first removing the existing file
if os.path.isfile(fileWF9):
    os.remove(fileWF9)

#Station list for the 21 stations that provided by Mike
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
            "KCRS": 412001,
            "KTYR": 411701,
            "KTRL": 419703,
            "KDTO": 419603,
            "KMWL": 419404}

#shrubGreeness factor, season code, and herbaceous Greenness Factor defined by Mike on 11/23/2015
#Greeness code dictionary Should be derived from a csv file that modify by Mike
GreenessCodeCSV = os.path.join(workspace,"ASOS_SeasonCode_GreenessCode.csv")
    # create groups and sorted stations lists for later use
shrubGreennessF= {}
herbaceousGreennessF = {}
seasonCode = {}
# read new csv file
with open(GreenessCodeCSV,mode='r') as rawcsv:
    rawReader = csv.reader(rawcsv, delimiter = ',')
    #mydict = {rows[7]:rows[8] for rows in rawReader}
    rawReader.next()
    for row in rawReader:
        #print row['WIMS ID']
        shrubGreennessF[int(row[6])]=int(row[7])
        herbaceousGreennessF[int(row[6])]=int(row[8])
        seasonCode[int(row[6])]=int(row[9])

    print shrubGreennessF,herbaceousGreennessF,seasonCode
##    header = next(rawReader)
##    for keys, rows in groupby(rawReader, lambda row: row[1]):
##        print keys,rows
##        groups.append(list(rows))
##        stations.append(keys)
##


##shrubGreennessF = {  411701: 10,
##                     412001: 10,
##                     413901: 10,
##                     416901: 15,
##                     417501: 15,
##                     417601: 15,
##                     417803: 10,
##                     418003: 10,
##                     418103: 10,
##                     418104: 10,
##                     418105: 10,
##                     418402: 15,
##                     418504: 15,
##                     418702: 15,
##                     418803: 15,
##                     419002: 15,
##                     419204: 15,
##                     419302: 15,
##                     419404: 10,
##                     419603: 10,
##                     419703: 10}

##herbaceousGreennessF =  {411701: 0,
##                         412001: 0,
##                         413901: 0,
##                         416901: 20,
##                         417501: 20,
##                         417601: 20,
##                         417803: 0,
##                         418003: 0,
##                         418103: 0,
##                         418104: 0,
##                         418105: 0,
##                         418402: 20,
##                         418504: 20,
##                         418702: 20,
##                         418803: 20,
##                         419002: 20,
##                         419204: 20,
##                         419302: 20,
##                         419404: 0,
##                         419603: 0,
##                         419703: 0}

##seasonCode  = { 411701: 4,
##                412001: 4,
##                413901: 4,
##                416901: 3,
##                417501: 3,
##                417601: 3,
##                417803: 4,
##                418003: 4,
##                418103: 4,
##                418104: 4,
##                418105: 4,
##                418402: 3,
##                418504: 3,
##                418702: 3,
##                418803: 3,
##                419002: 3,
##                419204: 3,
##                419302: 3,
##                419404: 4,
##                419603: 4,
##                419703: 4}

for STATION,ID in Stations.items():
    try:
        URL = 'http://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=csv&hoursBeforeNow=48&stationString=%s'%(STATION,)
        #Updated to 48 hour to calculate the 24-hour summary for each hour
        filename = "%s-%s.csv"%(STATION,datetime.today().strftime("%Y%m%d%H%M"))
        csvfile = os.path.join(ASOSArchive, filename)
        #csvfile = "c:\\DEV\\ASOS\\CSV\\%s-%s.csv"%(STATION,datetime.today().strftime("%Y%m%d%H%M"))
        #urllib.urlretrieve(URL,csvfile)
    except:
        MSG = "The ASOS source data were not downloaded successfully for Station: %s %s"% (STATION,Stations[STATION])
        print MSG
        logging.info(MSG)
        #sendEmail(MSG)
        exit()
    # Inteprete ASOS data for WIMS instake
