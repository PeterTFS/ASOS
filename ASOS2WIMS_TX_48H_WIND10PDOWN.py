#-------------------------------------------------------------------------------
# Name:      ASOS2WIMS_TX.py
# Purpose:   Compile ASOS weather into FW9 for feeding WIMS
# Author:    Peter Yang
# Created:   01/10/2015
#-------------------------------------------------------------------------------
import time
import os
import urllib2
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

#Send email if issue happenned!
def sendEmail(TXT):
    server = smtplib.SMTP('tfsbarracuda.tamu.edu', 25)
    #server.set_debuglevel(1)
    SUBJECT = 'There is an issue with ASOS4WIMS'
    message = 'Subject: %s\n\n%s' % (SUBJECT, TXT)
    server.sendmail("pyang@tfs.tamu.edu", "pyang@tfs.tamu.edu", message)

#For the season code:input an actual day to get the season code
seasons = [(1, (date(1,  1,  1),  date(1,  3, 20))),
           (2, (date(1,  3, 21),  date(1,  6, 20))),
           (3, (date(1,  6, 21),  date(1,  9, 22))),
           (4, (date(1,  9, 23),  date(1, 12, 20))),
           (1, (date(1, 12, 21),  date(1, 12, 31)))]

def get_season(now):
    if isinstance(now, datetime):
        now = now.date()
    now = now.replace(year=1)
    for season, (start, end) in seasons:
        if start <= now <= end:
            return season
    assert 0, 'never happens'
#-----------------------------------------------------------------------------------------
# Convert UTC to Central Zone (can be any zone)
#-----------------------------------------------------------------------------------------
def UTC2LOCAL(TIMESTR):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal() #changed to local zone
    #to_zone = tz.gettz("US/Central")
    utc= datetime.strptime(TIMESTR,"%Y-%m-%dT%H:%M:%SZ")
    utc=utc.replace(tzinfo=from_zone)
    local = utc.astimezone(to_zone)
    return local

def F2C( T ):
    return (T-32.)*5./9.

def C2F( T ):
    return T * 9./5. + 32.

def SatVapPres( T ):
    return math.exp( (16.78 * T - 116.9 )/( T + 237.3 ) )

def formatFloat(v):
    return int(round(v))

#----------------------------------------------------------------------------
#RH: =100*(EXP((17.625*TD)/(243.04+TD))/EXP((17.625*T)/(243.04+T)))
#T = Temperature in Celcius TD = Dewpoint in Celcius Raw ASOS data in Celcius
#----------------------------------------------------------------------------
def RH(T,TD):
    return 100*(math.exp((17.625*TD)/(243.04+TD))/math.exp((17.625*T)/(243.04+T)))

def RH(series):
    return 100*(math.exp((17.625* series['dewpoint_c'])/(243.04 + series['dewpoint_c']))/math.exp((17.625*series['temp_c'])/(243.04+series['temp_c'])))

#-----------------------------------------------------------------------------------------
# Processing the 4 level of sky cover into one column
def SKY(series):
    return series['sky_cover'] + series['sky_cover.1'] + series['sky_cover.2'] + series['sky_cover.3']

#-----------------------------------------------------------------------------------------------------------------
# ASOS wind sensors are at a height of 10 meters, but the RAWS/WIMS standard is for 6 meter/20 foot winds.
#To estimate the 6 meter wind speed from the 10 meter measurement, the logarithmic wind profile method can be used
#------------------------------------------------------------------------------------------------------------------
def windspeed(series):
    return series['wind_speed_kt'] * 0.9 * math.log(6/0.0984)/math.log(10/0.0984)
    #updated on 10-13-2015: Mike requet to reduce wind 10% down from Larry's suggestion
    #return gust * 0.90 * math.log(6/0.0984)/math.log(10/0.0984)

#Use a special treatment for the value at 0.005 or smaller precipitation
def CorrectPrcpAmount(p):
    if p <= 0.005 : p = 0.0
    return p

#Define a precipitation hous based on the measurable amount of precipitation
def precipDuration(preci_in):
    if preci_in > 0:
        return 1
    else:
        return 0
#---------------------------------------------------------------------------
#Function to remove the pre-24 hour observation if there are missing records
#---------------------------------------------------------------------------
def checkMissingRecords(df):
    #check time difference for each hour is 1 hour and for the first and last record is 24
    timeBegin = datetime.strptime(df.iloc[0]['observation_time'],"%Y-%m-%dT%H:%M:%SZ")
    for index,row in df.iterrows():
        timeEnd   = datetime.strptime(row['observation_time'],"%Y-%m-%dT%H:%M:%SZ")
        tdelta =  timeBegin - timeEnd
        #print timeBegin,timeEnd,tdelta
        if(tdelta.seconds/3600 > 23):
            df = df.drop(index)
            print "There is a missing record for Station: ",(row['station_id'])
            logging.info("There is a missing record for Station: %s",row['station_id'])
    return df
#--------------------------------------------------------------------
# Function for Formatting the extracted information to the wf9 format
# Input: Dictionary (X) that contains all the information
# Output: A string with fw9 format
#-------------------------------------------------------------------
def FormatFW9( X ):
    print X
    Fields = (('W98',(0,'3A')),('Station Number',(3,'6A')),('Ob Date',(9,'8A')),('Ob Time',(17,'4A')),
              ('Type',(21,'1A')),('State of Weather',(22,'1N')),('Temp',(23,'3N')),('Moisture',(26,'3N')),
              ('WindDir',(29,'3N')),('WindSpeed',(32,'3N')),('10hr Fuel',(35,'2N')),('Tmax',(37,'3N')),
              ('Tmin',(40,'3N')),('RHmax',(43,'3N')),('RHmin',(46,'3N')),('PrecipDur',(49,'2N')),
              ('PrecipAmt',(51,'5N')),('WetFlag',(56,'1A')),('Herb',(57,'2N')),('Shrub',(59,'2N')),
              ('MoistType',(61,'1N')),('MeasType',(62,'1N')),('SeasonCode',(63,'1N')),('SolarRad',(64,'4N'))
              )
    Out = []
    for f,p in Fields:
        val = X[f]
        #str(X[f]).zfill()
        length = int(p[1][:-1]) #not working
        format = p[1][-1]
            #This is the total precipitation in the previous 24 hours, given in thousands of an inch. For
            #example, an observation of 0.04? would be entered as ___40, preceded by three
            #blanks/spaces. An observation of 1.25? would be entered as _1250, preceded by one space.
            #An observation of no rainfall would be entered as all blanks/spaces.
        if f=='PrecipAmt':
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
    return string.join( Out, '' )

#----------------------------------------------------------------------------------------
# Function to inteprete the downloaded ASOS csv file and extract the relevant information
# Input : csv file for the precious 48 hours;station name
# Output: string stream fils formatted in fw9
#----------------------------------------------------------------------------------------
def IntepreteASOS(csvfile,STATION,ID):
    majoritylst = []
    #Open the downloaded csv for information
    with open(csvfile) as filt_csv:
        pread = pandas.read_csv(filt_csv,skiprows=5)
        #1 Extracting the fields required
        asos = pread[['station_id',
                      'observation_time',
                      'temp_c',
                      'dewpoint_c',
                      'wind_dir_degrees',
                      'wind_speed_kt',
                      'wind_gust_kt',
                      'sky_cover','sky_cover.1','sky_cover.2','sky_cover.3', #Four levels of skycover in the report
                      'maxT_c',
                      'minT_c',
                      'maxT24hr_c',
                      'minT24hr_c',
                      'precip_in',
                      'pcp3hr_in',
                      'pcp6hr_in',
                      'pcp24hr_in',
                      'raw_text',
                      'wx_string']] #Added raw_txt and wx_string two more fields for SOW detemining

        #Add a colum based on the observing minutes
        asos['minute'] = asos.loc[:,('observation_time')].str[14:16]
        #asos1['minute'] = asos1.apply(lambda row: int(str(asos1['observation_time']).strip()[14:16]),axis=1 )

        #2 do a statistical on them and get the flag time(a majority time)
        #for record in asos['minute']:
        for record in asos.loc[:,('minute')]:
            majoritylst.append(record)
        flagtime = max(set(majoritylst),key=majoritylst.count)

        #3 tiss out the hour-in-between records and this is the observation data that is gonna to use
        asos = asos[asos['minute']==flagtime]

        print 'There are total', len(asos.index),' Records for Station: ', STATION
        logging.info("There are total %s Records for Station: %s",len(asos.index),STATION)
        #check how many recodrs for the major time, if the records == 24 go with it
        #if the record less than 24 need to recheck and get. Make sure there are 24 records, otherwise report
        #In order to get a 24 previous records, now the 48 hours record were pulled in
        if len(asos.index)!=48:
            print 'There are missing', 48 - len(asos.index),' Records for Station: ', STATION
            logging.info("There are missing %s Records for Station: %s",48-len(asos.index),STATION)
            #By the time tested, the number is always the same if scheduled run from 13:00 to 13:50, the minutes between 50 and 00 will have missing record
            #Some measure need to be taken where some report were deliberatly changed by the end of the hour. e.g. from 51 to 53 or other time need to recreate the data frame again
        #process the hourly report for just the past 24 hours, be careful about the timezone difference
        #Make sure there are 24 records passed onto the Report, using a loop for processing each hour (from the recent to latest 24 hour)
        #Fill the no data value with blank for the four levels of sky cover and wx_string
        asos['sky_cover.1'].fillna('', inplace=True)
        asos['sky_cover.2'].fillna('', inplace=True)
        asos['sky_cover.3'].fillna('', inplace=True)
        asos['wx_string'].fillna('', inplace=True)

        #Change the data type to str instead of float(default by pandas)
        asos[['sky_cover', 'sky_cover.1','sky_cover.2','sky_cover.3','wx_string']] = asos[['sky_cover', 'sky_cover.1','sky_cover.2','sky_cover.3','wx_string']].astype(str)
        #Merge four field together
        asos['sky_cover'] = asos.apply(SKY,axis=1)

        #Wind speed at 6m, only pick up the 13 hours wind speed!!
        asos['WindSpeed']=asos.apply(windspeed,axis = 1)

        #Maximum and Minimum Relative Humidity
        asos['RH']= asos.apply(RH,axis = 1)

        #need to Fill the NUMERICAL data value with 0 for all the numerical fields
        asos['temp_c'].fillna(0, inplace=True)
        asos['wind_dir_degrees'].fillna(0, inplace=True)
        asos['wind_speed_kt'].fillna(0, inplace=True)
        asos['wind_gust_kt'].fillna(0, inplace=True)
        asos['WindSpeed'].fillna(0, inplace=True)
        asos['RH'].fillna(0, inplace=True)

        #Need to do something to get the previous 3 hour precipitation
        #4 Fill the No data value with 0 for precipitation
        asos['precip_in'].fillna(0, inplace=True)
        #Regarding the rain duration, onyly > 0.005 will be recorded(so 0.005 should be disregarded) Ask Mike or Brad how they did with RAWS observation
        asos['precip_in']=asos['precip_in'].apply(CorrectPrcpAmount)
        #To define the Precipitation Duration hours
        asos['precip_duration']=asos['precip_in'].apply(precipDuration)
##        #Not applying the 3 hours this time Create a new field to hold the previous 3 hour precipitation
##        asos['PRCP3HOUR'] = 0
##        #Use a loop to calculate the 3hour precipitation, not used at this time, need to discuss
##        for hour in range(0,24):
##            #print asos.loc[hour,'PRCP3HOUR'],asos.loc[hour,'precip_in'],asos.loc[hour+1,'precip_in'],asos.loc[hour+2,'precip_in']
##            asos.loc[hour,'PRCP3HOUR']=asos.loc[hour,'precip_in'] + asos.loc[hour+1,'precip_in'] + asos.loc[hour+2,'precip_in']
        #define a dictionary to hold all the information
        X = {'W98':'W98', 'Station Number':'000000', 'Ob Date':'YYYYMMDD', 'Ob Time':0,
                  'Type':'R', 'State of Weather':0, 'Temp':0, 'Moisture':0,
                  'WindDir':0, 'WindSpeed':0, '10hr Fuel':0, 'Tmax':-999,
                  'Tmin':-999, 'RHmax':-999, 'RHmin':-999, 'PrecipDur':0,
                  'PrecipAmt':0, 'WetFlag':'N', 'Herb':-999, 'Shrub':-999,
                  'MoistType':2, 'MeasType':1, 'SeasonCode':0, 'SolarRad':0
                }
        #pass the station ID
        X['Station Number'] = ID
        #Create a file with fixed name ('tx-asos.fw9') suggested by Larry
        with open(fileWF9,'a') as F:
        #Slicing the dataframe from 48 to 24 for processing
            for hour in range(23,-1,-1): #change the sequence from later to latest
                df = asos[hour:hour+24]
                #should be a way to subset the dataframe by loop from the first row until the previous 24 hour
                #Detect missing record to avoid 2 'o' report for a station
                checkMissingRecords(df)
                #Transform the current row into a dictionary for better operation
                currenthour= df[:1].set_index('station_id').T.to_dict()
                currenthour = currenthour[STATION]
                ##Pass the previous 24 hours and current hour record for WIMS fw9 format
                Report(df,X,currenthour)
                F.write( FormatFW9( X ) +'\n' )

#-------------------------------------------------------------------------------
# Function for generate hours report for each hour (including the 'O' and 'R' record)
# Input: data.fram for the day and row for the current hour and a dictionary
# Output: A dictionary X with all required information
#------------------------------------------------------------------------------
def Report(asos,X,row):
    UTCtime = row['observation_time']
    LOCTIME=UTC2LOCAL(UTCtime)
    X['Ob Date'] = LOCTIME.strftime("%Y%m%d")
    X['Ob Time']=LOCTIME.strftime("%H%M")
    X['SeasonCode'] = get_season(LOCTIME)
    hour = LOCTIME.strftime("%H")
    ##Larry mentioned to round up the minutes to whole instead of changing the system configuration,
    ##however, Brad and Mike prefer use the original time for human intervention (updated 09/24/2015)
    if hour=='12':
        X['Type']='O'
    else:
        X['Type']='R'
    X['Temp'] = formatFloat(C2F(row['temp_c']))
    X['Moisture']= formatFloat(row['RH'])#use type 2 Relative Humidity
    X['WindDir'] = formatFloat(row['wind_dir_degrees'])
    X['WindSpeed'] = formatFloat(row['WindSpeed']) #this has been re-calculated
    X['Tmax'] = formatFloat(C2F( max(asos['temp_c']) ))
    X['Tmin'] = formatFloat(C2F( min(asos['temp_c']) ))
    TotPr = 0
    X['RHmax'] = formatFloat(max(asos['RH']))
    X['RHmin'] = formatFloat(min(asos['RH']))
    #This should be a method to compute the measurable precipitation, the measuable precipitation should be bigger than 0.005
    X['PrecipDur'] = asos['precip_duration'].sum()
    TotPr = asos['precip_in'].sum()
    print 'TotPr', TotPr
    #Determin the SOW value by a defined rule
    #This is the total precipitation in the previous 24 hours, given in thousands of an inch. For
    #example, an observation of 0.04? would be entered as ___40, preceded by three
    #blanks/spaces. An observation of 1.25? would be entered as _1250, preceded by one space.
    #An observation of no rainfall would be entered as all blanks/spaces.
    X['PrecipAmt'] = TotPr
    StateOfWeather(X,row)
    #Moisture Type code (1=Wet bulb, 2=Relative Humidity, 3=Dewpoint).
    X['MoistType'] = 2
    #Measurement Type code: 1=U.S.
    X['MeasType'] = 1
    #Solar radiation (watts per square meter).
    X['SolarRad'] = 0 #Need to discuss the default value suppose it to be 0

    return X

#----------------------------------------------------------------------------------------
# Function to determin the State of Weather value by a defined rule
# RULE: from 9 to 0
# first look into the raw_text for lightning information,
# then to wx_string for thunderstorm shower, snow ,rain and drizzle
# then to skycover for 4,3,2,1
# Input : Dictionary and Current hour record
# Updated (09/30/2015):
#----------------------------------------------------------------------------------------
def StateOfWeather(X,row):
    rawInput = str(row['raw_text'])
    #print type(rawInput), rawInput
    wxstring = str(row['wx_string'])
    #print type(wxstring), wxstring
    skycover = str(row['sky_cover'])
    #print type(skycover), skycover
    skycover = row['sky_cover']#how does pandas read several field with the same name(probably a new name?)
    if not rawInput.find('LTG') == -1:#changed from DSNT to LTG 09182015
        X['State of Weather'] = 9
    elif not wxstring.find('TS') ==-1 :
        X['State of Weather'] = 9
    elif not wxstring.find('SH') ==-1 :
        X['State of Weather'] = 8
    elif not wxstring.find('SN') ==-1 :
        X['State of Weather'] = 7
    elif not wxstring.find('RA') ==-1 :
        #How to determin the rain code? bigger than 0.1,
        if X['PrecipAmt'] >= 0.1:
            X['State of Weather'] = 6
    elif not wxstring.find('DZ') ==-1 :
        #How to determin the drizzle code? bigger than 0.01
        if X['PrecipAmt'] >= 0.01:
            X['State of Weather'] = 5
    elif not wxstring.find('FG') ==-1 :
        X['State of Weather'] = 4
    #elif not wxstring.find('HZ') ==-1 :
    #    X['State of Weather'] = 4
    elif not wxstring.find('BR') ==-1 :
        X['State of Weather'] = 4
    elif 'OVC' in skycover:
        X['State of Weather'] = 3
    elif 'BKN' in skycover:
        X['State of Weather'] = 2
    elif 'SCT' in skycover or 'FEW' in skycover:
        X['State of Weather'] = 1
    elif 'CLR' in skycover or 'SKC' in skycover:
        X['State of Weather'] = 0
    print 'State of Weather is',X['State of Weather']
    #######################################################
    #Updated 09-28-2015
    #Per Discussion with Mike and Brad on 09/24/2015
    #The wet flag will be always be set to 'N' because human intervention will be needed for the determination
##    if X['State of Weather'] == 5 or X['State of Weather'] == 6 or X['State of Weather'] == 7:
##        X['WetFlag']= 'Y'
##    #If the SOW is 8 (showers) or 9 (thunderstorms) and the station of interest reported any precipitation in the past hour, set the Wet Flag to Y.
##    elif X['State of Weather'] == 8 or X['State of Weather'] == 9:
##        if row['precip_duration'] == 1:
##            X['WetFlag']= 'Y'
##    else:
##        X['WetFlag']= 'N'
    return X
#-------------------------------------------------------------------------------
# Start from here
#-------------------------------------------------------------------------------
# Set up working space
workspace='c:\\DEV\\ASOS\\'
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
    print fileWF9
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

##for STATION,ID in Stations.items():
##    try:
##        URL = 'http://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=csv&hoursBeforeNow=48&stationString=%s'%(STATION,)
##        #Updated to 48 hour to calculate the 24-hour summary for each hour
##        csvfile = "c:\\DEV\\ASOS\\CSV\\%s-%s.csv"%(STATION,datetime.today().strftime("%Y%m%d%H%M"))
##        urllib.urlretrieve(URL,csvfile)
##    except:
##        MSG = "The ASOS source data were not downloaded successfully for Station: %s"% (STATION)
##        print MSG
##        logging.info(MSG)
##        sendEmail(MSG)
##        exit()
##    # Inteprete ASOS data for WIMS instake
##    try:
##        IntepreteASOS(csvfile,STATION,ID)
##    except:
##        MSG = "The ASOS data were not processed successfully for Station: %s"% (STATION)
##        sendEmail(MSG)


###Archive the WF9 file for each day
##archivefileWF9 = datetime.today().strftime("%Y%m%d") + ".fw9"
##archivefileWF9 = os.path.join(workspace,"FW9", archivefileWF9)
##print shutil.copyfile(fileWF9,archivefileWF9)
###Keep Record of the log file
##archivefileLOG = datetime.today().strftime("%Y%m%d") + ".log"
##archivefileLOG = os.path.join(workspace,"LOG", archivefileLOG)
##shutil.copyfile(os.path.join(workspace,"ASOS4WIMS.log"),archivefileLOG)
###############################################################
#need a way to re-process the previous files for debugging
#Input : Downloaded CSV file for re-process
#Output: fw9 files with all information interpreted
#############################################################
csvFN = "C:\\DEV\ASOS\CSVKDHT-201510131300"
def reProcessASOS(csvfile):
    STATION = csvfile[16:20]
    ID = Stations[STATION]
    IntepreteASOS(csvfile,STATION,ID)

reProcessASOS(csvFN)



