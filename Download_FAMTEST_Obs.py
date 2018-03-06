import urllib
import datetime
import xml.etree.ElementTree as ET
#Download the XML WIMS output for different Sigs
import smtplib

#Send email if issue happenned!
def sendEmail(TXT):
    server = smtplib.SMTP('tfsbarracuda.tamu.edu', 25)
    #server.set_debuglevel(1)
    SUBJECT = 'There is an issue with ASOS4WIMS'
    message = 'Subject: %s\n\n%s' % (SUBJECT, TXT)
    print "Sending email to " + message
    tolist=["pyang@tfs.tamu.edu"]#,"mdunivan@tfs.tamu.edu"]
    server.sendmail("pyang@tfs.tamu.edu", tolist, message)


#It is better to parse them into a dataframe instead of a csv file
def ParseXML(station,XMLFileName):
    #rawFile = XMLFileName[:-4] + '.csv'
    print XMLFileName
    # Header for output csv file. Contains all fields for final csv file
    header0 = ['sta_id', 'sta_nm', 'obs_dt', 'obs_tm', 'obs_type','sow','dry_temp','rh','wind_dir',
                'wind_sp','temp_max','temp_min','rh_max','rh_min','pp_dur','pp_amt','wet']

    tree = ET.parse(XMLFileName)

    root = tree.getroot()

    ASOSFlag = 0
    MSG=''

    if not root.getchildren():
        ASOSFlag = ASOSFlag + 1
        MSG = "There is a problem of ASOS observation for station in WIMS test: %s Check the website http://w1.weather.gov/obhistory/%s.html"% (station,station)
    else:
        for row in root.findall('row'):
            for field in header0:
                if row.find(field).text is None:
                    ASOSFlag = ASOSFlag + 1
                    MSG = MSG + "\n %s is not derived for station"%(field,station)
                    print MSG
                else:
                    print field + ':' + row.find(field).text

    #print ASOSFlag
    if ASOSFlag != 0:
        print MSG
        sendEmail(MSG)
##    with open(rawFile, 'wb') as xmlf:
##        writer = csv.writer(xmlf, delimiter = ',')
##        writer.writerow(header0)
##        tree = ET.parse(XMLFileName)
##        root = tree.getroot()
##        for row in root.findall('row'):
##            #print row
##            for field in header0:
##                if row.find(field).text is None:
##                    print 'Something is wrong!'
##                else:
##                    print 'ASOS uploaded successfully!'
##            if row.find('sta_id').text is None:
##                sta_id = -99
##            else:
##                sta_id = row.find('sta_id').text
##            if row.find('sta_nm').text is None:
##                sta_nm = -99
##            else:
##                sta_nm = row.find('sta_nm').text
##            if row.find('nfdr_dt').text is None:
##                nfdr_dt = -99
##            else:
##                nfdr_dt = row.find('nfdr_dt').text
##                #nfdr_tm = row.find('nfdr_tm').text
##            if row.find('msgc').text is None:
##                msgc = -99
##            else:
##                msgc = row.find('msgc').text
##            if row.find('ec') is None:
##                ec = -99
##            else:
##                ec = row.find('ec').text
##            if row.find('mp').text is None:
##                mp = -99
##            else:
##                mp = row.find('mp').text
##            rows = (sta_id, sta_nm, nfdr_dt, msgc, ec,mp)
##            print rows
##            writer.writerow(rows)
##        return(rawFile)

def DownloadASOS(station,stationid,start,end):
    #Should be today's ERC date
##    start = '22-Mar-16'
##    end = '22-Mar-16'
    # define xml file locations
    downloadtime = datetime.datetime.now().strftime("%Y%m%dH%HM%M")

    xmlobs = "C:\\DEV\\ASOS\\XML\\"  + str(stationid) + "_"+ start + "-" + end + "-" + downloadtime + "_obs.xml"

    # Get reponse from WIMS server
    serverResponse = urllib.urlopen('https://famtest.nwcg.gov/wims/xsql/nfdrs.xsql')
    # Check reponse code
    # If WIMS server is available, download xml files. Otherwise, exit process.
    if serverResponse.getcode() == 200:
        # Observations
        url = "https://famtest.nwcg.gov/wims/xsql/obs.xsql?stn=" + str(stationid) + "&sig=&type=O&start=" + start + "&end=" + end + "&time=&user=mdunivan&priority="
        print url
        #urllib.urlretrieve("https://famtest.nwcg.gov/wims/xsql/obs.xsql?stn=417601&sig=&type=O&start=" + start + "&end=" + end + "&time=&user=mdunivan&priority=",xmlobs)
        urllib.urlretrieve("https://famtest.nwcg.gov/wims/xsql/obs.xsql?stn=" + str(stationid) + "&sig=&type=O&start=" + start + "&end=" + end + "&time=&user=mdunivan&priority=",xmlobs)
                           # NTXS mdunivan &priority="

        print 'Downloaded ASOS from famtest for station:'+ str(stationid)
        ###Open the file and check the value not blank###
        ParseXML(station,xmlobs)
    else:
        logging.info('WIMS System is unavailable')
        logging.info('The input tables for Fire Danger Processing have not been updated')
        print 'WIMS System is unavailable'
        raise SystemExit()

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

##Stations = {"KELP": 416901}

today = datetime.datetime.today()
##one_day = datetime.timedelta(days=1)
##Firstday_2016 = "01-Jan-16"
##yesterday = today - one_day

end = today.strftime("%d-%b-%y")
#start = yesterday.strftime("%d-%b-%y")
start = end

#end = "31-Jan-16"
for station,stationid in Stations.items():
    DownloadASOS(station,stationid,start,end)

##
##xmlobs = r'C:\DEV\ASOS\XML\410202_26-Apr-16-28-Apr-16-20160428H11M12_obs.xml'
##ParseXML('All',xmlobs)
##pdraws = pandas.DataFrame.from_dict(Raws_Station.items())