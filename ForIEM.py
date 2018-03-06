
# Define primary workspace based on location of script
WorkSpace = os.getcwd()
#The downloaded file and processed file will be in the HIST directory
ASOSArchive = os.path.join(WorkSpace, "CSV")
hoursBeforeNow = 48
Stations = {"KLBB": 419002}
for STATION,ID in Stations.items():
    URL = 'http://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=csv&hoursBeforeNow=%d&stationString=%s'%(hoursBeforeNow,STATION,)
    #Updated to 48 hour to calculate the 24-hour summary for each hour
    print 'Downloading ASOS data for Station: ' + STATION
    filename = "%s-%s.csv"%(STATION,today.strftime("%Y%m%d%H%M"))
    print filename
    csvfile = os.path.join(ASOSArchive, filename)
    urllib.urlretrieve(URL,csvfile)