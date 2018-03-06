import time
import os
import urllib2
from metar import Metar
import csv

"KCLL 171953Z 20013G18KT 10SM BKN016 OVC021 27/23 A2991 RMK AO2 SLP122 T02720228"
report ="KPSX 162347Z AUTO 15030G44KT 3/4SM +RA BR BKN012 BKN018 OVC032 26/25 A2967 RMK AO2 PK WND 15050/2320 LTG DSNT NW RAB20 P0008 $"
report ="KCLL 231953Z 17008KT 10SM FEW055 33/22 A3012 RMK AO2 SLP195 T03280222"
report = "KTRL 142353Z AUTO 18008KT 10SM -RA CLR 34/22 A2982 RMK AO2 RAB49 SLP089 P0000 60000 T03440217 10361 20333 58010"
report = 'KFST 212153Z AUTO 18013G23KT 10SM VCTS FEW100 32/12 A2989 RMK AO2 LTG DSNT SE-W SLP070 T03170122'
report = 'KLBB 151253Z COR 25006KT 10SM FEW180 SCT260 BKN300 A3009 RMK AO2 SLP145 T01500133 $'
report = 'KELP 280051Z 28016KT 10SM BKN250 25/M04 A2996 RMK AO2 SLP090 T02501044'
X=Metar.Metar(report)
print X.string()
T = float( X.temp.value("F") )
DP = float( X.dewpt.value("F") )
#X.rh = CalcRH( T, DP )
hourlyprecip = 0.0
print T, DP
if X.precip_1hr:
    hourlyprecip = max(hourlyprecip, X.precip_1hr.value() * 1000.0)
    print hourlyprecip

X.PrecipEst = hourlyprecip
X.Peter = hourlyprecip

def ReadMetarData( f ):
    MetarFile = open(f,'r')
    RecordList = MetarFile.readlines()
    MetarFile.close()
    #data = map(string.strip, RecordList)
    all = string.join(RecordList,' ')
    return all

def ParseMetar( Station, RawMetarData ):
    rg = re.compile(Station+'.*?\n',re.IGNORECASE|re.DOTALL)

    X = False
    hourlyprecip = 0.0

    m = rg.findall(RawMetarData)
    for report in m:
        try:
            X = Metar.Metar('METAR '+report)
        except:
            print 'Bad report: %s' %(report)
        else:
            try:
                T = float( X.temp.value("F") )
                DP = float( X.dewpt.value("F") )
                X.rh = CalcRH( T, DP )
            except:
                X = False
            else:
                if X.precip_1hr:
                    hourlyprecip = max(hourlyprecip, X.precip_1hr.value() * 1000.0)
                    break
    if X:
        X.PrecipEst = hourlyprecip
    return X

GmtTime = time.gmtime( time.time()-3600. )
MetarDataFile = 'C:/DEV/ASOS/%02dZ.TXT' % GmtTime[3]
WgetCmd = 'C:/cygwin64/bin/wget '
URL = 'http://weather.noaa.gov/pub/data/observations/metar/stations/KCLL.TXT'

status = os.popen( '%s -O %s %s' %(WgetCmd,MetarDataFile,URL) )
data = urllib2.urlopen(URL)
out = open(MetarDataFile, 'w')
out.write(data.read())
out.close()

Stations = ["KDHT","KAMA","KSPS","KINK","KFST","KLBB","KJCT","KSJT","KELP","KDRT","KHDO","KSSF","KCOT","KALI","KBAZ","KCLL","KCRS","KTYR","KTRL","KDTO","KMWL"]
for station in Stations:
    print station
    URL = 'http://weather.noaa.gov/pub/data/observations/metar/stations/%s.TXT'%station
    data = urllib2.urlopen(URL)
#    out = open(MetarDataFile, 'r')
#    out.write(data.read())
 #   out.close()

 #   status = os.popen( '%s -O %s %s' %(WgetCmd,MetarDataFile,URL))

    MetarData = ParseMetar(station, RawMetarData )
    if MetarData:
            #if MetarData.temp != None:
                if SolarRadiationInterp:
                    MetarData.SolarRad = max(0, int(SolarRadiationInterp( s['LAT'],s['LON'] )))
                else:
                    MetarData.SolarRad = -999

                WriteRawMetarData( s, MetarData, RawOutputDir )
                NewWimsData = HourlyWimsFile( s, OutputDir, ismetar=True )