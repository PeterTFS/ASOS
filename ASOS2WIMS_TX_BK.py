#-------------------------------------------------------------------------------
# Name:      ASOS2WIMS_TX.py
# Purpose:   Compile ASOS weather into FW9 for feeding WIMS
# Author:    Peter Yang
# Created:   02/07/2015
#-------------------------------------------------------------------------------
import time
import os
import urllib2
import re
import csv
import string
import datetime
import urllib
import json
import pandas
import math



def F2C( T ):
    return (T-32.)*5./9.

#minT_c                              19.4
#It is wrong
def C2F( T ):
    return T * 9./5. + 32.

def SatVapPres( T ):
    return math.exp( (16.78 * T - 116.9 )/( T + 237.3 ) )

#--------------------------------------------------------------------
#RH: =100*(EXP((17.625*TD)/(243.04+TD))/EXP((17.625*T)/(243.04+T)))
#T = Temperature in Celcius
#TD = Dewpoint in Celcius
#Raw ASOS data in Celcius
#--------------------------------------------------------------------
def RH(T,TD):
    return 100*(math.exp((17.625*TD)/(243.04+TD))/math.exp((17.625*T)/(243.04+T)))

def RH(series):
    return 100*(math.exp((17.625* series['dewpoint_c'])/(243.04 + series['dewpoint_c']))/math.exp((17.625*series['temp_c'])/(243.04+series['temp_c'])))

#a dictionary for assigning the state of weather based on the ASOS weather code(defined by Mike)
#There will be a set of rule for determing the state of weather
#SOW = {'CLR':0,'FEW':0,'SCT':1,'BKN':2,'OVC':3,'FG':4,'DZ':5,'RA':6,'SN':7,'SH':8,'TS':9}
def SOW(sky_cover):
    SOW = {'CLR':0,'FEW':1,'SCT':1,'BKN':2,'OVC':3,'FG':4,'DZ':5,'RA':6,'SN':7,'SH':8,'TS':9}#updated on 08242015 for FEW should be 1 based on discussion
    #Need to look at the hour-in-between do determin this value,"LTG DSNT" "TS" and "VCTS"
    return SOW[sky_cover]

#Define a precipitation hous based on the measurable amount of precipitation
def precipDuration(preci_in):
    if preci_in > 0:
        return 1
    else:
        return 0


#-----------------------------------------------------------------------------------------
# ASOS wind sensors are at a height of 10 meters, but the RAWS/WIMS standard is for 6
# meter/20 foot winds. To estimate the 6 meter wind speed from the 10 meter measurement, the
# logarithmic wind profile method can be used
def windspeed(series):
    return series['wind_speed_kt'] * math.log(6/0.0984)/math.log(10/0.0984)

#Use a special treatment for the value at 0.005 or smaller
def CorrectPrcpAmount(p):
    if p <= 0.005 : p = 0.0
    return p
#-----------------------------------------------------------
# Formatting the extracted information to the wf9 format
# Input: Dictionary (X) that contains all the information
#08-21-2015 need to adjust to get a correct length
# Output: A string with fw9 format
#-----------------------------------------------------------
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
#        print f
        val = X[f]
        #str(X[f]).zfill()
        length = int(p[1][:-1]) #not working
        format = p[1][-1]
        if f=='Ob Time':
            if val <100:
                val*=100
            ZeroPad = '0'
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
            #print q % val
            Out.append( q % val )
        except:
            print f, p, q, val, type(val)
        #print Out
    return string.join( Out, '' )


#---------------------------------------------
# Write wf9 format string stream into a file
# Input: a Dictionary and directory
# Output: A string with fw9 format
#---------------------------------------------
def WriteFW9( X, OutDir='.' ):
    id = X['Station Number'].replace(' ','_')
    F = open( OutDir+'/wx'+id+'.fw9', 'a')
    F.write( FormatFW9( X ) +'\n' )
    F.close()

precipVDict = {}

#get the time for today
today = datetime.datetime.today().strftime("%Y%m%d")
GmtTime = time.gmtime( time.time()-3600. )


#def verifyASOS(precipVDict):
#5 Referece of precipitation(24 prcp) from IEM to verify Aviation data
network = 'http://mesonet.agron.iastate.edu/rainfall/obhour-json.php?network=TX_ASOS&ts=201507131800'
uri = "http://mesonet.agron.iastate.edu/rainfall/obhour-json.php?network=TX_ASOS&ts=%s1800" % (today,)
data = urllib.urlopen(uri)
jdict = json.load(data)
for d in jdict['precip']:
    precipVDict[str(d['id'])]=float(d['p24'])
#    return precipVDict

#----------------------------------------------------------------------------------------
# Function to inteprete the downloaded ASOS csv file and extract the relevant information
# Input : csv file for the precious 24 hours;station name;diction for precipitation from IEM
# Output: string stream fils formatting fw9
#----------------------------------------------------------------------------------------
def IntepreteASOS(csvfile,STATION,ID,precipVDict):
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
                      'sky_cover',
                      #'cloud_base_ft_agl'
                      #add 'TS',
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
    #    for record in asos['minute']:
        for record in asos.loc[:,('minute')]:
            majoritylst.append(record)
        flagtime = max(set(majoritylst),key=majoritylst.count)

    #3  tiss out the hour-in-between records and this is the observation data that is gonna to use
        asos = asos[asos['minute']==flagtime]

    #4 Fill the No data value with 0 for precipitation
        asos['precip_in'].fillna(0, inplace=True)
    #Regarding the rain duration, onyly > 0.005 will be recorded(so 0.005 should be disregarded) Ask Mike or Brad how they did with RAWS observation
        asos['precip_in']=asos['precip_in'].apply(CorrectPrcpAmount)

        #To define the Precipitation Duration hours
        asos['precip_duration']=asos['precip_in'].apply(precipDuration)

        #Wind speed at 6m, only pick up the 13 hours wind speed!!
        asos['WindSpeed']=asos.apply(windspeed,axis = 1)

        #Maximum and Minimum Relative Humidity
        asos['RH']= asos.apply(RH,axis = 1)

        #need to Fill the No data value with 0 for all the newly computed fields
        asos.fillna(0, inplace=True)

        #define a dictionary to hold all the information from the csv file
        X = {'W98':'W98', 'Station Number':'000000', 'Ob Date':'YYYYMMDD', 'Ob Time':0,
                  'Type':'R', 'State of Weather':0, 'Temp':0, 'Moisture':0,
                  'WindDir':0, 'WindSpeed':0, '10hr Fuel':0, 'Tmax':-999,
                  'Tmin':-999, 'RHmax':-999, 'RHmin':-999, 'PrecipDur':0,
                  'PrecipAmt':0, 'WetFlag':'N', 'Herb':-999, 'Shrub':-999,
                  'MoistType':2, 'MeasType':1, 'SeasonCode':0, 'SolarRad':0
                }
        #use an orderedDict instead(exploration) may stick with tuple.

    #We have 24 hour record and for each hour will be a stream that formatted into a fw9 letter stream,
    #Note: when the hour comes to the 13:00 PM(how do I know it?) a 24 hour analyses will be applied
#        print asos['observation_time']
        print 'There are total', len(asos.index),' Records for Station: ', STATION
        #pass the station ID
        X['Station Number'] = ID
        #process the hourly report
        Report(asos,X)

#-------------------------------------------------------------------
# hours report except 13 observation hour
# Input: data.fram for the day and row for the hour and a dictionary
# Output: A dictionary X with all required information
#-------------------------------------------------------------------
def rReport(X,row):
#    print row
    return X
#-------------------------------------------------------------------
# Sumarrize 24 hours report at 13 observation hour
# Input: data.fram for the day and row for the hour and a dictionary
# Output: A dictionary X with all required information
#-------------------------------------------------------------------
def Report(asos,X):
    for index,row in asos.iterrows():
        date = row['observation_time'][0:10]
        hour = row['observation_time'][11:13]
        minute = row['observation_time'][14:16]
#        print date,hour,minute
    #        for time in asos['observation_time']:
        X['Ob Date'] = date[0:4]+date[5:7]+date[8:10]
        #Fore one station, all 24 hour observation will be saved in a file
        #using one file (using date) for all the stations 1300 observation
        F = open(csvfile[-15:-5] + '.fw9','a')
        #if observation hour is 13:00 PM Central time(06 UTZ), it needs all the 24 observation to get the O type data
        if hour == '17':
            #print type(row)
            #print X['Ob Date']
            #round the hour into 1300 or XX00 format
            if minute >= 50:
                minute = '00'
            X['Ob Time']= '13' + minute #updated on 09042015
            X['Type'] = 'O'
            oReport(asos,X,row)
#            print X
            F.write( FormatFW9( X ) +'\n' )

    F.close()

def formatFloat(v):
    return int(round(v))

def StateOfWeather(X,row):
#    print row
    print 'raw_text',row['raw_text'],type(row['raw_text']), 'wx_string',row['wx_string'],type(row['wx_string'])
	#rawInput = row['raw_text'].split() + row['wx_string'].split()
    rawInput = row['raw_text'].split()
    rawInput.append(row['sky_cover']) #add the sky_cover in the list

    if type(row['wx_string'])==str:
        rawInput.append(row['wx_string'])
    print rawInput
        #WetFlag Default is ?Y? for State of Weather 5, 6, and 7. Required
    if 'VCTS' in rawInput or 'DSNT' in rawInput or 'TS' in rawInput:
        X['State of Weather'] = 9
    elif 'SH' in rawInput:
        X['State of Weather'] = 8
    elif 'SN' in rawInput:
        X['State of Weather'] = 7
    elif 'RA' in rawInput:
        #How to determin the rain code? bigger than 0.1
        if X['PrecipAmt'] >= 0.1:
            X['State of Weather'] = 6
    elif 'DZ' in rawInput:
        if X['PrecipAmt'] >= 0.01:
            X['State of Weather'] = 5
    elif 'FG' in rawInput:
        X['State of Weather'] = 4
    elif 'OVC' in rawInput:
        X['State of Weather'] = 3
    elif 'BKN' in rawInput:
        X['State of Weather'] = 2
    elif 'SCT' in rawInput:
        X['State of Weather'] = 1
    elif 'CLR' in rawInput or 'FEW' in rawInput:
        X['State of Weather'] = 0

    print 'State of Weather is',X['State of Weather']
    #set the wet flag value
    if X['State of Weather'] == 5 or X['State of Weather'] == 6 or X['State of Weather'] == 7:
        X['WetFlag']= 'Y'
    #If the SOW is 8 (showers) or 9 (thunderstorms) and the station of interest reported any
    #precipitation in the past hour, set the Wet Flag to Y.
    elif X['State of Weather'] == 8 or X['State of Weather'] == 9:
        if row['precip_duration'] >= 0.01:
            X['WetFlag']= 'Y'
    else:
        X['WetFlag']= 'N'
    return X

def oReport(asos,X,row):
    #int(round(24.789))
    X['Ob Date']='20150904'
    X['Temp'] = formatFloat(C2F(row['temp_c']))
    X['Moisture']= formatFloat(row['RH'])#use type 2 Relative Humidity
    X['WindDir'] = formatFloat(row['wind_dir_degrees'])
    X['WindSpeed'] = formatFloat(row['WindSpeed']) #this has been transformed
#    X['10hr Fuel'] #lEAVE BLANK??
#    print row['SOW']
    X['Tmax'] = formatFloat(C2F( max(asos['temp_c']) ))
    X['Tmin'] = formatFloat(C2F( min(asos['temp_c']) ))
    #X['Station Number']=             id = X['Station Number'].replace(' ','_')
    TotPr = 0
    #print row['observation_time'][11:13] 17 hours for the 13 hr central time!
    X['RHmax'] = formatFloat(max(asos['RH']))
    X['RHmin'] = formatFloat(min(asos['RH']))
    #This is the number of hours out of the past 24 hours in which measurable precipitation was reported
    #This should be a method to compute the measurable precipitation, the measuable precipitation should be bigger than 0.005
#    print asos['precip_duration']
#    print 'precip_duration',asos['precip_duration']
    X['PrecipDur'] = asos['precip_duration'].sum()
    TotPr = asos['precip_in'].sum()
    print 'TotPr', TotPr
    #verify the total precipitation against the summarized from other source
    # do a verification with the IEM website: this should be done before this function!
    station = row['station_id']
    if TotPr!=precipVDict[station[1:]]:
        print station," NOT Verified:",TotPr,'!=',precipVDict[station[1:]]
    X['PrecipAmt'] = TotPr #Assign a real value for comparison!
    #Determin the SOW value by a complicated rule
    #Start with 9, check raw_txet, wx_string to find "DS, TS, CSTS,?." if it is
    StateOfWeather(X,row)
    #Moisture Type code (1=Wet bulb, 2=Relative Humidity, 3=Dewpoint).
    X['MoistType'] = 2
    #Measurement Type code: 1=U.S.
    X['MeasType'] = 1
#    X['SeasonCode']=0
    #Solar radiation (watts per square meter).
    X['SolarRad'] = 0 #Need to discuss the default value suppose it to be 0

    #This is the total precipitation in the previous 24 hours, given in thousands of an inch. For
    #example, an observation of 0.04? would be entered as ___40, preceded by three
    #blanks/spaces. An observation of 1.25? would be entered as _1250, preceded by one space.
    #An observation of no rainfall would be entered as all blanks/spaces.
    X['PrecipAmt'] = 1000*TotPr
    return X

#-------------------------------------------------------------------------------
# Start from here
#-------------------------------------------------------------------------------
#Station list for the 21 stations that provided by Mike

#Need to dictionary to get the WIMS ID for ASOS station
##
##0 - Clear, less than 1/10 cloud cover	SKC or CLR - Clear, 0/8 cloud cover
##0 - Clear, less than 1/10 cloud cover	FEW - Few clouds, 1/8-2/8 cloud cover
##1 - Scattered clouds, 1/10-5/10 cloud cover	SCT - Scattered clouds, 3/8-4/8 cloud cover
##2 - Broken clouds, 6/10-9/10 cloud cover	BKN - Broken clouds, 5/8-7/8 cloud cover
##3 - Overcast, 10/10 cloud cover	OVC - Overcast, 8/8 cloud cover
##4 - Fog	FG - Fog
##5 - Drizzle	DZ - Drizzle
##6 - Rain	RA - Rain
##7 - Snow or sleet	SN - Snow
##8 - Showers	SH - Showers
##9 - Thunderstorms	TS - Thunderstorms
Stations = {"KDHT":'000000',
            "KAMA":'000000',
            "KSPS":'000000',
            "KINK":'000000',
            "KFST":417601,
            "KLBB":'000000',
            "KJCT":'000000',
            "KSJT":'000000',
            "KELP":'000000',
            "KDRT":'000000',
            "KHDO":'000000',
            "KSSF":'000000',
            "KCOT":'000000',
            "KALI":'000000',
            "KBAZ":'000000',
            "KCLL":'000000',
            "KCRS":'000000',
            "KTYR":'000000',
            "KTRL":'000000',
            "KDTO":'000000',
            "KMWL":'000000'}

Stations = {"KDHT":'00KDHT',
            "KAMA":'00KAMA',
            "KSPS":'00KSPS',
            "KINK":'00KINK',
            "KFST":417601,
            "KLBB":'00KLBB',
            "KJCT":'00KJCT',
            "KSJT":'00KSJT',
            "KELP":'00KELP',
            "KDRT":'00KDRT',
            "KHDO":'00KHDO',
            "KSSF":'00KSSF',
            "KCOT":'00KCOT',
            "KALI":'00KALI',
            "KBAZ":'00KBAZ',
            "KCLL":'00KCLL',
            "KCRS":'00KCRS',
            "KTYR":'00KCRS',
            "KTRL":'00KTRL',
            "KDTO":'00KDTO',
            "KMWL":'00KMWL'}

#Need to dictionary to get the WIMS ID for ASOS station
# NOT CORRECT! The program should be scheduled to run near the end of each hour(:59), it can be implemented on windows,
# one time running at 12:59 PM
##Stations ={"KCRS":'000000',
##            "KCLL":'000000'}
for STATION,ID in Stations.items():
    URL = 'http://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=csv&hoursBeforeNow=24&stationString=%s'%(STATION,)
    #One possible option to change the 24 hour to 48 hour to calculate the 24-hour summary for each hour
    csvfile = "c:\\DEV\\ASOS\%s%s%02dZ.csv"%(STATION,today,GmtTime[3])
    try:
        urllib.urlretrieve(URL,csvfile)
    except:
        print "The ASOS source data were not downloaded successfully"
        exit()
    # Inteprete ASOS data
    IntepreteASOS(csvfile,STATION,ID,precipVDict)
    #Formate to fw9 format



#Upload for WIMS Submit the formatted information into a file stream for WIMS input




