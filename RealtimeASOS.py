#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      pyang
#
# Created:     02/02/2017
# Copyright:   (c) pyang 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

URL = 'http://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=csv&hoursBeforeNow=%d&stationString=%s'%(hoursBeforeNow,STATION,)
    #Updated to 48 hour to calculate the 24-hour summary for each hour
'''This works for 48, but not for all the ASOS stations can provide every 5 minutes report, e.g. KCLL report every hour
#
http://www.aviationweather.gov/adds/dataserver_current/httpparam?datasource=metars&requesttype=retrieve&format=csv&hoursBeforeNow=48&stationString=KCLL
#
       http://www.aviationweather.gov/adds/dataserver_current/httpparam?datasource=metars& requesttype=retrieve&format=xml&compression=gzip& hoursBeforeNow=1.25&mostRecentForEachStation=constraint
print 'Downloading ASOS data for Station: ' + STATION
filename = "%s-%s.csv"%(STATION,today.strftime("%Y%m%d%H%M"))
print filename
csvfile = os.path.join(ASOSArchive, filename)
urllib.urlretrieve(URL,csvfile)