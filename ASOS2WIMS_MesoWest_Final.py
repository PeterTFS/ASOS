#-----------------------------------------------------------------------------------------------------------------
# Name:      ASOS2WIMS_ASOSWest.py
# Purpose:   Compile ASOS weather into FW9 for feeding WIMS from ASOSWest instead of Aviatation Whether center
# Author:    Peter Yang
# Note :    May used as an alternative data downloading for WIMS alternative gateway(Leave it there)!
# Created:   04/03/2017
#-------------------------------------------------------------------------------
import time
import os
import sys
import re
import string
import urllib
import urllib2
import shutil
import pandas
import math
import logging
#from datetime import date, datetime, timedelta
import datetime
from dateutil import tz
import smtplib
pandas.options.mode.chained_assignment = None  # default='warn'
import csv
import json
#import openpyxl

#--------------------------------------------------------------------------------------------------------------------------------
# Convert UTC to Standard time (only for central standard time)
# Since we know there will be always 6 hours difference between the UTC and standard time(disregard the daylight saving effect
#-------------------------------------------------------------------------------------------------------------------------------


def UTC2STANDARD(TIMESTR):
    utc = datetime.datetime.strptime(TIMESTR, "%Y-%m-%dT%H:%M:%SZ")
    standard = utc - datetime.timedelta(hours=6)
    #print utc,standard
    return standard

#-----------------------------------------------------------------------------------------------------------------
# ASOSnet wind sensors are at a height of 10 meters, but the RAWS/WIMS standard is for 6 meter/20 foot winds.
#To estimate the 6 meter wind speed from the 10 meter measurement, the logarithmic wind profile method  math.log(6/0.0984)/math.log(10/0.0984) can be used
#To convert the knot to mph, the 1.15078 ration is used. Mike suggest mannually reduce the windspeed by 10% (*0.9) for WIMS
#------------------------------------------------------------------------------------------------------------------


def windspeed(wind_speed):
    ##    print 'windspeed 10m',wind_speed
    ##    sixmeterwindspeed = wind_speed* 0.9 * math.log(6/0.0984)/math.log(10/0.0984)
    ##    print 'windspeed 6m',sixmeterwindspeed
    windspeed = wind_speed * 0.9 * math.log(6 / 0.0984) / math.log(10 / 0.0984)
    return round(windspeed, 2)

#Use a special treatment for the value at 0.005 or smaller precipitation


def CorrectPrcpAmount(p):
    if p <= 0.005:
        p = 0.0
    return p

#Define hourly precipitation based on the measurable amount of precipitation


def precipDuration(p):
    if p > 0.005:
        return 1
    else:
        return 0

#Formatting Float into Int


def formatFloat(v):
    return int(round(v))

#Formatting precipitation with 2 decimals


def formatPrecip(p):
    return round(p, 2)

#--------------------------------------------------------------------
# Function for Formatting the extracted information to the wf9 format
# Input: Dictionary (X) that contains all the information
# Output: A string with fw9 format
#-------------------------------------------------------------------


def FormatFW9(X):
    ##To define the byte writing structure using a tuple
    Fields = (('W98', (0, '3A')), ('Station Number', (3, '6A')), ('Ob Date', (9, '8A')), ('Ob Time', (17, '4A')),
              ('Type', (21, '1A')), ('State of Weather', (22, '1N')
                                     ), ('Temp', (23, '3N')), ('Moisture', (26, '3N')),
              ('WindDir', (29, '3N')), ('WindSpeed', (32, '3N')
                                        ), ('10hr Fuel', (35, '2N')), ('Tmax', (37, '3N')),
              ('Tmin', (40, '3N')), ('RHmax', (43, '3N')
                                     ), ('RHmin', (46, '3N')), ('PrecipDur', (49, '2N')),
              ('PrecipAmt', (51, '5N')), ('WetFlag', (56, '1A')
                                          ), ('Herb', (57, '2N')), ('Shrub', (59, '2N')),
              ('MoistType', (61, '1N')), ('MeasType', (62, '1N')
                                          ), ('SeasonCode', (63, '1N')), ('SolarRad', (64, '4N'))
              )
    Out = []
    for f, p in Fields:
        val = X[f]
        #str(X[f]).zfill()
        length = int(p[1][:-1])  # not working
        format = p[1][-1]
        #This is the total precipitation in the previous 24 hours, given in thousands of an inch. For
        #example, an observation of 0.04? would be entered as ___40, preceded by three
        #blanks/spaces. An observation of 1.25? would be entered as _1250, preceded by one space.
        #An observation of no rainfall would be entered as all blanks/spaces.
        if f == 'PrecipAmt':
            if val == 0:
                val = -999
            else:
                val *= 1000
        #WindParaList = ['WindSpeed','WindDir']
        # Updated on 01092017 after meeting discussion that the 0 should be replaced by 3 mph
        WindParaList = ['WindSpeed']
        if f in WindParaList:
            if val == 0:
               val = 3  # Updated on 01092017 after discussion that the 0 windspeed should be replaced by 3 mph
        else:
            ZeroPad = ''
        if format == 'N' and val != -999:
            #q = str(0).zfill(length)
            q = '%%%s%dd' % (ZeroPad, length)
        elif format == 'N' and val == -999:
            val = ' '
            q = '%%%s%ds' % (ZeroPad, length)
        else:
            q = '%%%ds' % length
        try:
            Out.append(q % val)
        except:
            print f, p, q, val, type(val)
    return string.join(Out, '')
#----------------------------------------------------------------------------------------
# Function to determin the State of Weather value by a defined rule
# RULE: from 9 to 0
# first look into the raw_text for lightning information,
# then to wx_string for thunderstorm shower, snow ,rain and drizzle
# then to skycover for 4,3,2,1
# Input : Dictionary and Current hour record
# Updated (09/30/2015):
# David suggesting realtime query for the previous hour (previous 3 hours and 24hour)
#the current hour precipitaiton is 0 and WeatherCode and Metar information for get the SOW
#----------------------------------------------------------------------------------------
def StateOfWeather(X, row):
    raw_input = str(row['Metar'])
    wxstring = str(row['WeatherCode'])
    CurrentHourPrecip = row['Precipitation']
    print CurrentHourPrecip
    if CurrentHourPrecip <= 0.1:
        if not wxstring.find('Clear') == -1:
            X['State of Weather'] = 0
        elif not wxstring.find('Partly Cloudy') == -1:
            X['State of Weather'] = 1
        elif not wxstring.find('Mostly Cloudy') == -1:
            X['State of Weather'] = 2
        elif not wxstring.find('Overcast') == -1:
            X['State of Weather'] = 3
        elif not wxstring.find('Fog') == -1 and row['RelativeHumidity'] >= 95:
            X['State of Weather'] = 4
        elif not raw_input.find('OVC') == -1:
            X['State of Weather'] = 3
        elif not raw_input.find('BKN') == -1:
            X['State of Weather'] = 2
        elif not raw_input.find('SCT') == -1:
            X['State of Weather'] = 1
        elif not raw_input.find('FEW') == -1:
            X['State of Weather'] = 1
        elif not raw_input.find('CLR') == -1:
            X['State of Weather'] = 0

    else:  # only to see if there are rain
        # changed from DSNT to LTG 09182015
        if not wxstring.find('Thunderstorm') == -1:
            X['State of Weather'] = 9
        elif not wxstring.find('Heavy Rain') == -1:
            X['State of Weather'] = 8
        elif not wxstring.find('Snow') == -1 and row['AirTemperature'] <= 32:
            X['State of Weather'] = 7
        elif not wxstring.find('Rain') == -1:
            X['State of Weather'] = 6
        elif not wxstring.find('Light Rain') == -1:
            X['State of Weather'] = 5
    return X
#-------------------------------------------------------------------------------
# Function for generate hours report for each hour (including the 'O' and 'R' record)
# Input: data.fram for the day and row for the current hour and a dictionary
# Output: A dictionary X with all required information
# Use the 18 UTC hour instead of local hour to check if it is the 'O' or 'R'
#------------------------------------------------------------------------------
def Report9(meso, X, row):
    UTC_Hour = row['Date_Hour'][-2:]
##    X['Ob Date'] = row['obs_time_local'].strftime("%Y%m%d")
##    X['Ob Time']=  row['obs_time_local'].strftime("%H%M")
    X['Ob Date'] = row['obs_time_standard'].strftime("%Y%m%d")
    X['Ob Time'] = row['obs_time_standard'].strftime("%H%M")
    #X['SeasonCode'] = get_season(LOCTIME)
    ##Larry mentioned to round up the minutes to whole instead of changing the system configuration,
    ##however, Brad and Mike prefer use the original time for human intervention (updated 09/24/2015)
    if UTC_Hour == '18':  # Should always be 18 and don't interfere with local time
        X['Type'] = 'O'
    else:
        X['Type'] = 'R'
    X['Temp'] = formatFloat(row['AirTemperature'])
    # use type 2 Relative Humidity
    X['Moisture'] = formatFloat(row['RelativeHumidity'])
    # this has been re-calculated
    X['WindSpeed'] = formatFloat(row['WindSpeed'])
    if X['WindSpeed'] == 0:
        X['WindDir'] = 0
    else:
        X['WindDir'] = formatFloat(row['WindDirection'])

    X['GustSpeed'] = formatFloat(row['WindGust'])
##    if X['WindGust']==0:
##        X['GustDir']= 0
##    else:
##        X['GustDir'] = X['WindDir']

    #print 'Ob Time:',X['Ob Time'],'WindSpeed:',X['WindSpeed'],'WindDir:',X['WindDir']##'GustDir:',X['GustDir'],'GustSpeed:',X['GustSpeed']
    X['Tmax'] = formatFloat(max(meso['MaxAirTemperature']))
    X['Tmin'] = formatFloat(min(meso['MinAirTemperature']))

    X['RHmax'] = formatFloat(max(meso['RelativeHumidity']))
    X['RHmin'] = formatFloat(min(meso['RelativeHumidity']))

    TotPr = 0
    #This should be a method to compute the measurable precipitation, the measuable precipitation should be bigger than 0.005
    X['PrecipDur'] = meso['precip_duration'].sum()
    #need the query
    TotPr = meso['Precipitation'].sum()

    ##print 'TotPr', TotPr

##    #This is the total precipitation in the previous 24 hours, given in thousands of an inch. For
##    #example, an observation of 0.04? would be entered as ___40, preceded by three
##    #blanks/spaces. An observation of 1.25? would be entered as _1250, preceded by one space.
##    #An observation of no rainfall would be entered as all blanks/spaces.
##    #Updated 10/26/2015, rounding precip into hundredths
    X['PrecipAmt'] = formatPrecip(max(meso['Precipitation']))

## based on the Weather condition code and raw METAR records
    StateOfWeather(X, row)
    #based on discussion with Mike on 02/09/2018 a table was developed for associating solar radiation with SOW for next genration of NFDRS
    """
    0-----750
    1-----600
    2-----300
    3-----200
    Othere should be considered as 0
    """
    if X['State of Weather'] == 0:
        X['SolarRad'] = 750  # Need to discuss the default value suppose it to be 0
    elif X['State of Weather'] == 1:
        X['SolarRad'] = 600
    elif X['State of Weather'] == 2:
        X['SolarRad'] = 300
    elif X['State of Weather'] == 3:
        X['SolarRad'] = 200
    else:
        X['SolarRad'] = 0

    #Moisture Type code (1=Wet bulb, 2=Relative Humidity, 3=Dewpoint).
    X['MoistType'] = 2
    #Measurement Type code: 1=U.S.
    X['MeasType'] = 1

##   no need greeness code and seasoncode because of 78G model
    #print int(X['Station Number'])
    X['Herb'] = herbaceousGreennessF[X['Station Number']]
    X['Shrub'] = shrubGreennessF[X['Station Number']]
    X['SeasonCode'] = seasonCode[X['Station Number']]

##    if X['State of Weather'] == 7:
##        X[SnowFlag]='Y'
    #print X
    return X


# Seeting the working evironments
WorkSpace = os.getcwd()
ASOSArchive = os.path.join(WorkSpace, "CSV")
FW13Archive = os.path.join(WorkSpace, "FW13")
FW9Archive = os.path.join(WorkSpace, "FW9")
LOGArchive = os.path.join(WorkSpace, "LOG")

if not os.path.exists(ASOSArchive):
    os.makedirs(ASOSArchive)
if not os.path.exists(FW13Archive):
    os.makedirs(FW13Archive)
if not os.path.exists(FW9Archive):
    os.makedirs(FW9Archive)
if not os.path.exists(LOGArchive):
    os.makedirs(LOGArchive)


#Greeness code dictionary Should be derived from a csv file that modify by Mike
GreenessCodeCSV = os.path.join(WorkSpace, "ASOS_SeasonCode_GreenessCode.csv")
# create groups and sorted stations lists for later use
shrubGreennessF = {}
herbaceousGreennessF = {}
seasonCode = {}

def FUN(v):
    if v == 'n/a':
        return -999
    else:
        return int(v)
# read new csv file
with open(GreenessCodeCSV, mode='r') as rawcsv:
    rawReader = csv.reader(rawcsv, delimiter=',')
    rawReader.next()
    for row in rawReader:
        shrubGreennessF[int(row[6])] = FUN(row[7])
        herbaceousGreennessF[int(row[6])] = FUN(row[8])
        seasonCode[int(row[6])] = FUN(row[9])


fileWF9 = os.path.join(WorkSpace, "tx-asos_mesowest.fw9")
#----------------------------------------------------------------------------------------
# Function to inteprete the downloaded West TX ASOSnet csv file and extract the relevant information
# Input : csv file for the precious 48 hours;station name
# Output: string stream fils formatted in fw9
# Update: 02/20/2018
# the data from ASOSwest instead of aviation weather center
# the order is opposite from aviation weather center
#----------------------------------------------------------------------------------------
def IntepreteASOSWest(csvfile, STATION, ID):
    #Open the downloaded csv for information
    #csvfile = r"c:\DEV\ASOS\CSV\KCLL-201802191900-201802211859_F.csv"
    majoritylst = []
    # ID = 413901
    # STATION = 'KCLL'
    #Open the downloaded csv for information
    with open(csvfile) as csv:
        # use usecols=range(39) to avoid the error "CParserError: Error tokenizing data. and get the correct header"
        pread = pandas.read_csv(csv, skiprows=6, usecols=range(39))
        #print(pread.columns)
        pread = pread.iloc[1:]  # removing the row for units
        print pread.head(10)
    ##Format the data frame
        asos = pread[['Station_ID',
                    'Date_Time',
                    'air_temp_set_1',
                    'dew_point_temperature_set_1d',
                    'wind_speed_set_1',
                    'wind_direction_set_1',
                    'wind_gust_set_1',
                    'relative_humidity_set_1',
                    'precip_accum_one_hour_set_1',
                    'metar_set_1',  # METAR raw_txt
                    'weather_condition_set_1d'  # Weather code used to determin SOW
                    ]]
        #Remove duplicated records suggested by Larry 10-14-2015
        asos = asos.drop_duplicates()
        #Add a colum based on the observing minutes
        #print(asos.loc[:, ('Date_Time')].str[14:16])
        asos.loc[:, 'minute'] = asos.loc[:, ('Date_Time')].str[14:16]
        #2 do a statistical on them and get the flag time(a majority time)
        #for record in asos['minute']:
        for record in asos.loc[:, ('minute')]:
            majoritylst.append(record)
        flagtime = max(set(majoritylst), key=majoritylst.count)
        #3 tiss out the hour-in-between records and this is the observation data that is gonna to use
        asos = asos[asos['minute'] == flagtime]
        #print(asos.head(10))
        #logging.info("There are total %s Records for Station: %s",len(asos.index),STATION)
        if len(asos) != 48:
            print('something is wrong!', len(asos))
        else:
            print('The total records are: ', len(asos))

        #Fill the no data value with blank for the four levels of sky cover and wx_string
        asos['weather_condition_set_1d'].fillna('', inplace=True)
        asos['metar_set_1'].fillna('', inplace=True)

        #Change the data type to str instead of float(default by pandas)
        asos[['weather_condition_set_1d', 'metar_set_1']] = asos[[
            'weather_condition_set_1d', 'metar_set_1']].astype(str)

        asos.loc[:, 'Date_Hour'] = asos.loc[:, ('Date_Time')].str[0:13]
        asos['wind_direction_set_1'].fillna(0, inplace=True)
        asos['wind_speed_set_1'].fillna(0, inplace=True)
        asos['wind_gust_set_1'].fillna(0, inplace=True)
        ###Need to leave it blank if detected as 0
        #4 Fill the No data value with 0 for precipitation and relative humidity
        asos['precip_accum_one_hour_set_1'].fillna(0, inplace=True)
        asos['relative_humidity_set_1'].fillna(0, inplace=True)
        #print(asos.head(10))
        #First need to change the data type from string to float before processing
        asos[['air_temp_set_1', 'relative_humidity_set_1',
            'wind_speed_set_1', 'wind_direction_set_1', 'wind_gust_set_1', 'precip_accum_one_hour_set_1',
            ]] = asos[['air_temp_set_1', 'relative_humidity_set_1',
                        'wind_speed_set_1', 'wind_direction_set_1', 'wind_gust_set_1', 'precip_accum_one_hour_set_1', ]].astype(float)
        #print(asos.head(10))
        #Apply group function on fields for hourly records
        asos.loc[:, 'Precipitation'] = asos.loc[:, 'precip_accum_one_hour_set_1']
        #updated on 11/09/2017, changed to use median instead of mean to better match the values of hourly record from RAWS
        asos.loc[:, 'AirTemperature'] = asos.loc[:, 'air_temp_set_1']
        asos.loc[:, 'RelativeHumidity'] = asos.loc[:, 'relative_humidity_set_1']
        asos.loc[:, 'MaxAirTemperature'] = max(asos.loc[:, 'air_temp_set_1'])
        asos.loc[:, 'MinAirTemperature'] = min(asos.loc[:, 'air_temp_set_1'])
        asos.loc[:, 'WindSpeed'] = asos.loc[:, 'wind_speed_set_1']
        asos.loc[:, 'WindDirection'] = asos.loc[:, 'wind_direction_set_1']
        asos.loc[:, 'WindGust'] = asos.loc[:, 'wind_gust_set_1']
        asos.loc[:, 'Metar'] = asos.loc[:, 'metar_set_1']
        asos.loc[:, 'WeatherCode'] = asos.loc[:, 'weather_condition_set_1d']

        ASOS = asos[['Station_ID', 'Date_Time', 'Precipitation', 'AirTemperature', 'RelativeHumidity',
                    'MaxAirTemperature', 'MinAirTemperature', 'WindSpeed', 'WindDirection', 'WindGust', 'Date_Hour', 'WeatherCode', 'Metar']]
        ASOS.loc[:, 'obs_time_standard'] = ASOS.loc[:,
                                                    'Date_Time'].apply(UTC2STANDARD)
        #Regarding the rain duration, onyly > 0.005 will be recorded(so 0.005 should be disregarded)
        ASOS.loc[:, 'Precipitation'] = ASOS.loc[:,
                                                'Precipitation'].apply(CorrectPrcpAmount)
        #To define the Precipitation Duration hours
        ASOS.loc[:, 'precip_duration'] = ASOS.loc[:,
                                                'Precipitation'].apply(precipDuration)
        ##ASOS.loc[:,'precip_duration']=ASOS.loc[:,'Precipitation'].apply(lambda t: 1 if t > 0.0 else 0)
        ASOS.loc[:, 'WindSpeed'] = ASOS.loc[:, 'WindSpeed'].apply(windspeed)
        #Gust speed
        ASOS.loc[:, 'WindGust'] = ASOS.loc[:, 'WindGust'].apply(windspeed)

        X9 = {'W98': 'W98', 'Station Number': '000000', 'Ob Date': 'YYYYMMDD', 'Ob Time': 0,
            'Type': 'R', 'State of Weather': -999, 'Temp': 0, 'Moisture': 0,
            'WindDir': 0, 'WindSpeed': 0, '10hr Fuel': 0, 'Tmax': -999,
            'Tmin': -999, 'RHmax': -999, 'RHmin': -999, 'PrecipDur': 0,
            'PrecipAmt': 0, 'WetFlag': 'N', 'Herb': 20, 'Shrub': 15,
            'MoistType': 2, 'MeasType': 1, 'SeasonCode': 3, 'SolarRad': 0
            }

        #print(ASOS.head(10))
        X9['Station Number'] = ID
        ##X13['Station Number'] = ID
        with open(fileWF9, 'a') as F9:
            #Get each a 24 hour period for calculating the fire weather parameters
            for hour in range(1, 25):  # change the sequence from later to latest
                #print hour, hour+24
                df = ASOS.iloc[hour:hour + 24]
                print(len(df))
                #need to create a dict from the last row
                currenthour = df.tail(1).set_index('Station_ID').T.to_dict()
                currenthourdf = currenthour[STATION]
                #print(currenthourdf)
                Report9(df, X9, currenthourdf)
                # ##Write the records into a FW13 and FW9 format
                F9.write(FormatFW9(X9) + '\n')

############################################
#Setting the directories for data archiving
############################################
WorkSpace = os.getcwd()
print WorkSpace
MesonetArchive = os.path.join(WorkSpace, "CSV")
#FW13Archive  = os.path.join(WorkSpace, "FW13")
FW9Archive  = os.path.join(WorkSpace, "FW9")
LOGArchive  = os.path.join(WorkSpace, "LOG")

if not os.path.exists(MesonetArchive):
    os.makedirs(MesonetArchive)
##if not os.path.exists(FW13Archive):
##    os.makedirs(FW13Archive)
if not os.path.exists(FW9Archive):
    os.makedirs(FW9Archive)
if not os.path.exists(LOGArchive):
    os.makedirs(LOGArchive)

##A table for the 1300 hour historical maximum solar radiation hourly mean
srtable = os.path.join(WorkSpace,'SRTable.csv')
SRtable = pandas.read_csv(srtable,sep=' ')
SRtable=SRtable.set_index(['Month'])
#print SRtable.loc[6,'CNST2']

LOGfile = os.path.join(LOGArchive,"MESONET4WIMS.log")
#Set up a logger for logging the running information
logging.basicConfig(filename=LOGfile,
                    format='%(asctime)s   %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S%p',
                    filemode='w',
                    level=logging.INFO)

#define the fire weather file name
#fileWF13 = os.path.join(WorkSpace, "tx-asos.fw13")
fileWF9 = os.path.join(WorkSpace, "tx-asos-mesowest.fw9")
#for each day first removing the existing file
##if os.path.isfile(fileWF13):
##    os.remove(fileWF13)
#for each day first removing the existing file
if os.path.isfile(fileWF9):
    os.remove(fileWF9)

START_UTC = "1900"
END_UTC = "1859"

##START_UTC = "1901"
##END_UTC = "1900"

#today = date(datetime.now())
# set up date information
today = datetime.datetime.today()
#logging.info("Start ASOS processing for %s", today.strftime("%Y%m%d"))
#logging.info("Start ASOS processing for %s", datetime.now().strftime("%Y%m%d%H"))
UTC_now = datetime.datetime.utcnow()
UTCHOUR_now = int(UTC_now.strftime("%H"))

#How about using the UTC hour (should always be 19:00) to avoid day saving issue
if UTCHOUR_now >= 19:
## Process today's data
    TODATSTR = today.strftime("%Y%m%d")
    two_day = datetime.timedelta(days=2)
    Twodaybeforetoday = today - two_day
    TWODAYSTR = Twodaybeforetoday.strftime("%Y%m%d")

else:
    three_day = datetime.timedelta(days=3)
    one_day = datetime.timedelta(days=1)
    ThreeDay = today - three_day
    YesterDay = today - one_day
    TODATSTR = YesterDay.strftime("%Y%m%d")
    TWODAYSTR = ThreeDay.strftime("%Y%m%d")

StartTime  =  TWODAYSTR + START_UTC
EndTime = TODATSTR + END_UTC
print StartTime,EndTime

StartTime = '201802171900'
EndTime =   '201802191859'
#The two stations that Mike marked one has different current hour temperature and max/mim temperature
Stations = {"KDHT": 418702,
            #"KAMA": 418803,
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

Stations = {"KLBB": 419002}
#####Parameters for downloading Mesonet data using MesoWest API#####
MyToken = '994a7e628db34fc68503d44c447aaa6f'
#m = Meso(token=MyToken)
base_url = 'http://api.mesowest.net/v2/stations/'
query_type = 'timeseries'
csv_format = '&output=csv'
noHighFrequecy = '&hfmetars=0'

#units = '&units=precip|in,temp|F,speed|mph'
#Changed the temperature from F to C
#units = '&units=precip|in,temp|C,speed|mph'
units = '&units=precip|in,temp|F,speed|mph'
#######################################################################
##Loop through each station for downloading and processing Mesonet Data
for STATION,ID in Stations.items():
    try:
        print STATION,ID
        api_string = base_url + query_type + '?' + 'stid=' + STATION + '&start=' + StartTime + \
            '&end=' + EndTime + '&token=' + MyToken + units + csv_format + noHighFrequecy
        print api_string
        print 'Downloading ASOS data for Station: ' + STATION
        #filename = "%s-%s-MesoWest.csv"%(STATION,today.strftime("%Y%m%d%H%M"))
        filename = "%s-%s-%s_y.csv"%(STATION,StartTime,EndTime)
        print filename
        csvfile = os.path.join(MesonetArchive, filename)
        print csvfile
        urllib.urlretrieve(api_string,csvfile)
        #Precipitation query
        #precip = m.precip(stid='kfnl', start='201504261800', end='201504271200', units='precip|in')
    # Catch the error type from the urllib.urlretrieve(URL,csvfile)
    except:
        MSG = "The MesoWest source data were not downloaded successfully for Station: %s %s"% (STATION,Stations[STATION])
        print MSG
        #Should not exit here, use continue
        logging.info(MSG)
        continue
        #exit()
    IntepreteASOSWest(csvfile,STATION,ID)
"""
    try:
        print 'Processing MesoNet Station: ' + STATION + ' with Station ID: ' + str(ID)
        #IntepreteMesoNet(csvfile,STATION,ID)
    except:
        MSG = "The MesoNet data were not processed successfully for Station: %s %s"% (STATION,Stations[STATION])
        logging.info(MSG)
        print "Unexpected error:", sys.exc_info()[0]
        #sendEmail(MSG)

#Archive the WF9 file for each day
archivefileWF9 = today.strftime("%Y%m%d") + ".fw9"
archivefileWF9 = os.path.join(FW9Archive, archivefileWF9)
shutil.copyfile(fileWF9,archivefileWF9)
#Archive the WF13 file for each day
##archivefileWF13 = today.strftime("%Y%m%d") + ".fw13"
##archivefileWF13 = os.path.join(FW13Archive, archivefileWF13)
##shutil.copyfile(fileWF13,archivefileWF13)
#Keep Record of the log file
archivefileLOG = today.strftime("%Y%m%d") + ".log"
archivefileLOG = os.path.join(LOGArchive, archivefileLOG)
shutil.copyfile(LOGfile,archivefileLOG)
"""
