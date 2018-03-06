#-------------------------------------------------------------------------------
# Name:      XML2FW13.py
# Purpose:   Transform Obs from WXML feed into FW13 format for a station
# Author:    Peter Yang
# Created:   01/10/2015
#-------------------------------------------------------------------------------

import urllib
import xml.etree.ElementTree as ET
import datetime
import os
import string
#--------------------------------------------------------------------
# Function for Formatting the extracted information to the wf13 format
# Input: Dictionary (X) that contains all the information
# Output: A string with fw13 format
#-------------------------------------------------------------------
def FormatFW13( X ):
    Fields = (('W13',(0,'3A')),('sta_id',(3,'6A')),('obs_dt',(9,'8A')),('obs_tm',(17,'4A')),
              ('obs_type',(21,'1A')),('sow',(22,'1N')),('dry_temp',(23,'3N')),('rh',(26,'3N')),
              ('wind_dir',(29,'3N')),('wind_sp',(32,'3N')),('10hr Fuel',(35,'2N')),('temp_max',(37,'3N')),
              ('temp_min',(40,'3N')),('rh_max',(43,'3N')),('rh_min',(46,'3N')),('pp_dur',(49,'2N')),
              ('pp_amt',(51,'5N')),('wet',(56,'1A')),('grn_gr',(57,'2N')),('grn_sh',(59,'2N')),
              ('MoistType',(61,'1N')),('MeasType',(62,'1N')),('season_cd',(63,'1N')),('SolarRad',(64,'4N')),
              ('GustDir',(68,'3N')),('GustSpeed',(71,'3N')),('snow_flg',(74,'1A'))
              )

    Out = []
    for f,p in Fields:
        val = X[f]
        #str(X[f]).zfill()
        length = int(p[1][:-1]) #not working
        format = p[1][-1]

        if f=='pp_amt':
            if val == 0:
                val=-999
            else:
                val*=1000
        else:
            ZeroPad = ''
        if format == 'N' and val != -999:
            #q = str(0).zfill(length)
            q = '%%%s%dd' % (ZeroPad,length)
        elif format == 'N' and val == -999:
            val = ' '
            q = '%%%s%ds' % (ZeroPad,length)
        else:
            q = '%%%ds' % length
        try:
            Out.append( q % val )
        except:
            print f, p, q, val, type(val)
    #print Out
    return string.join( Out, '' )

#-----------------------------------------------------------------------------------------
# Parse the XML feeds into Fire Weather 13 format
#-----------------------------------------------------------------------------------------
def ParseXML(station,XMLFileName):
    #rawFile = XMLFileName[:-4] + '.csv'
    print XMLFileName
    # Header from the XML file
    header0 = ['sta_id', 'obs_dt', 'obs_tm', 'obs_type','sow','dry_temp','rh','wind_dir',
                'wind_sp','temp_max','temp_min','rh_max','rh_min','pp_dur','pp_amt','wet','season_cd','grn_gr','grn_sh','snow_flg']

    tree = ET.parse(XMLFileName)
    root = tree.getroot()

    MSG=''
    #Dictionary for holding all the parameter in the FW13 format
    X13 = {'W13':'W13', 'sta_id':'000000', 'obs_dt':'YYYYMMDD', 'obs_tm':13,
      'obs_type':'O', 'sow':0, 'dry_temp':0, 'rh':0,
      'wind_dir':0, 'wind_sp':0, '10hr Fuel':0, 'temp_max':-999,
      'temp_min':-999, 'rh_max':-999, 'rh_min':-999, 'pp_dur':0,
      'pp_amt':0, 'wet':'N', 'grn_gr':20, 'grn_sh':15,
      'MoistType':2, 'MeasType':1, 'season_cd':3, 'SolarRad':0,
      'GustDir':0,'GustSpeed':0,'snow_flg':'N'
    }

    fileWF13 = os.path.join(WorkSpace, "tx-raws_hundredeightyday_days.fw13")

    with open(fileWF13,'a') as F13:
        if not root.getchildren():
            MSG = "There is a problem of RAWS observation for station in WIMS: %s "% (station)
        else:
            for row in root.findall('row'):
                for field in header0:
                    if row.find(field).text is None:
                        MSG = MSG + "\n %s is not derived for station"%(field,station)
                        print MSG
                    else:
                        if field in ['wind_dir','rh_max','pp_dur','wind_sp','sow','temp_min','GustDir','temp_max','dry_temp','season_cd','rh','grn_sh','rh_min','grn_gr']:
                            X13[field] = int(row.find(field).text)
                        elif field in ['obs_dt']:
                            date = row.find(field).text
                            YYMMDD = date[6:] + date[0:2] + date[3:5]
                            X13[field] = YYMMDD
                        elif field in ['obs_tm']:
                            time = row.find(field).text
                            TIME = time + '00'
                            X13[field] = TIME
                        elif field in ['pp_amt']:
                            X13[field] = float(row.find(field).text)
                        else:
                            X13[field] = row.find(field).text
                print X13
                F13.write( FormatFW13( X13 ) +'\n' )


def DownloadASOS(station,stationid,start,end):

    # define xml file locations
    downloadtime = datetime.datetime.now().strftime("%Y%m%dH%HM%M")

    xmlobs = "C:\\DEV\\ASOS\\XML\\"  + str(stationid) + "_"+ start + "-" + end + "-" + downloadtime + "_obs.xml"

    # Get reponse from WIMS server
    serverResponse = urllib.urlopen('https://famtest.nwcg.gov/wims/xsql/nfdrs.xsql')
    # Check reponse code
    # If WIMS server is available, download xml files. Otherwise, exit process.
    if serverResponse.getcode() == 200:
        # Observations
        url = "https://fam.nwcg.gov/wims/xsql/obs.xsql?stn=" + str(stationid) + "&sig=&type=O&start=" + start + "&end=" + end + "&time=&sort=asc&ndays=&user="
        print url
        #urllib.urlretrieve("https://famtest.nwcg.gov/wims/xsql/obs.xsql?stn=417601&sig=&type=O&start=" + start + "&end=" + end + "&time=&user=mdunivan&priority=",xmlobs)
##        urllib.urlretrieve("https://fam.nwcg.gov/wims/xsql/obs.xsql?stn=" + str(stationid) + "&sig=&type=O&start=" + start + "&end=" + end + "&time=&user=mdunivan&priority=",xmlobs)
##                           # NTXS mdunivan &priority="
        urllib.urlretrieve(url,xmlobs)
##        urllib.urlretrieve("https://fam.nwcg.gov/wims/xsql/obs.xsql?stn=&sig=TWIM&type=O&start=" + start + "&end=" + end + "&time=&sort=asc&ndays=7&user=pyang&priority=",
##                   xmlobs)
        print 'Downloaded ASOS from famtest for station:'+ str(stationid)
        ###Open the file and parse the XML into Fire Weather Format###
        ParseXML(station,xmlobs)
    else:
        logging.info('WIMS System is unavailable')
        logging.info('The input tables for Fire Danger Processing have not been updated')
        print 'WIMS System is unavailable'
        raise SystemExit()

#A list of weather stations with station id
RAWS_TX = {'ANAHUAC NWR': 416099}
RAWS_TX = {'ATTWATER': 416601}
#Get today's date (start and end can be used for specific date)
today = datetime.datetime.today()
sixty_day = datetime.timedelta(days=60)
ninety_day = datetime.timedelta(days=90)
hundredeighty_day = datetime.timedelta(days=180)
one_day = datetime.timedelta(days=1)
yesterday = today - one_day
sixtyday = today - sixty_day
ninetyday = today - ninety_day
hundredeightyday = today - hundredeighty_day
end = today.strftime("%d-%b-%y")
end = yesterday.strftime("%d-%b-%y")
start = yesterday.strftime("%d-%b-%y")
start = sixtyday.strftime("%d-%b-%y")
start = ninetyday.strftime("%d-%b-%y")
start = hundredeightyday.strftime("%d-%b-%y")
#start = end

print start,end

WorkSpace = os.getcwd()

for station,stationid in RAWS_TX.items():
    print station,stationid
    DownloadASOS(station,stationid,start,end)

