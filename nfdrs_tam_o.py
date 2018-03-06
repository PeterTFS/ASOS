# Processing of weather data to/from fire family plus .fw9 format

import string, time, re, sys, logging, os, math, random, glob
#import emailIt

from metar import Metar
import davclient

import ConfigParser

WgetCmd = '/usr/sfw/bin/wget -t 50'

#WgetCmd = 'wget -t 50'


# info for webdav transfer to wims
user = ''
passwd = ''
url = ''
dest= ''

# RESET for TESTING for webdav transfer to wims
#user = ''
#passwd = ''
#url = ''
#dest= ''

CountyInfoFile = 'etc/nfdrs_county-info.csv'
FawnDataFile = 'data/fawn/csv?asText=1'

GmtTime = time.gmtime( time.time()-3600. )
MetarDataFile = 'data/metar/%02dZ.TXT' % GmtTime[3]
# determine hour
try:
    tmpHour = string.atoi( sys.argv[1] )
    MetarDataFile = 'data/metar/%02dZ.TXT' % tmpHour
except:
    pass


OutputDir = 'data/wims'
RawOutputDir = OutputDir+'/raw'
ArchiveOutputDir = OutputDir+'/archive'

ExecutionTime = time.localtime( time.time() )
YYYYMMDD = time.strftime('%Y%m%d', ExecutionTime)

EasternTime = ExecutionTime
eYYYYMMDD = time.strftime('%Y%m%d', EasternTime)

YYYYMMDDHH = '%d%02d%02d%02d' % ( ExecutionTime[0], ExecutionTime[1], ExecutionTime[2], ExecutionTime[3])
#*******************************************************************
# Configure Logging
LogHour = ExecutionTime[3]
logging.basicConfig()
Path, MyApp = os.path.split( sys.argv[0] )
Path = os.path.abspath(os.curdir)
MyApp = MyApp.split('.')[0]
MyLog = logging.getLogger( MyApp )
handler = logging.FileHandler( Path+'/logs/'+MyApp+'-%02d.log'%LogHour, mode='w' )
MyLog.addHandler( handler )
formatter = logging.Formatter("%(levelname)-5s - %(message)s")
handler.setFormatter( formatter )
MyLog.setLevel( logging.DEBUG )
#    MyLog.info('Reading config file' )
#    MyLog.error( Path+'/'+PrgName+'.ini not found' )
#*******************************************************************
MyLog.info('processing '+MyApp )

def LoadConfig( file ):
    MyLog.info('Reading config file' )
    config = {}
    cp = ConfigParser.ConfigParser()
    cp.read(file)
    for section in cp.sections():
        SectionName = section.lower()
        if not config.has_key( SectionName ):
            config[SectionName] = {}
        for option in cp.options(section):
            O = option.lower().split(',')
            if len(O) > 1:
                OptionName = tuple( O )
            else:
                OptionName = O[0]
            try:
                v = map( lambda x: string.atof(x), cp.get(section,option).strip().split(',') )
                if len(v)==1:
                    v = v[0]
            except:
                v = cp.get(section,option).strip()
            config[SectionName][OptionName] = v
    return config


def DownloadFile( name, X, hr ):
    MyLog.info('Downloading '+name )
    URL = X['method']+'://'+X['host']+X['location']+'/'+X['file']
    OutputFilename =  X['destination'] + '/' + X['file']
    #OutputFilename = re.sub('\?', '', OutputFilename)
    try:
        status = os.popen( '%s -O %s %s' %(WgetCmd,OutputFilename,URL) )
        MyLog.info( status.readlines() )
        err = status.close()
        if err != None:
            MyLog.error('Unable to access '+URL )
            emailIt.emailMsg('%s - Error: Unable to access %s' %(MyApp, URL) )
            return False
    except:
        MyLog.error('Unable to access '+URL )
        emailIt.emailMsg('%s - Error: Unable to access %s' % (MyApp,URL) )
        return False
    else:
#        decompress if needed
        if OutputFilename[-7:] == '.tar.gz' :
            try:
                os.chdir( X['destination'] )
                results = os.popen( GZipCmd+' '+OutputFilename.split('/')[-1] )
                err = results.close()
                if err != None:
                    MyLog.error('Error decompressing file with cmd: %s'%(GZipCmd+' '+OutputFilename) )
                    emailIt.emailMsg('%s - Error decompressing file with cmd: %s'%(MyApp, GZipCmd+' '+OutputFilename) )
                    os.chdir('../..')
                    return False
                os.chdir('../..')
            except:
                MyLog.error('Error decompressing file with cmd: %s'%(GZipCmd+' '+OutputFilename) )
                emailIt.emailMsg('%s - Error decompressing file with cmd: %s'%(MyApp, GZipCmd+' '+OutputFilename) )
                os.chdir('../..')
                return False
    return True

def ReadFW9( s ):
    Fields = {'W98':(0,'3A'),'Station Number':(3,'6A'),'Ob Date':(9,'8N'),'Ob Time':(17,'4N'),
              'Type':(21,'1A'),'State of Weather':(22,'1A'),'Temp':(23,'3N'),'Moisture':(26,'3N'),
              'WindDir':(29,'3N'),'WindSpeed':(32,'3N'),'10hr Fuel':(35,'2N'),'Tmax':(37,'3N'),
              'Tmin':(40,'3N'),'RHmax':(43,'3N'),'RHmin':(46,'3N'),'PrecipDur':(49,'2N'),
              'PrecipAmt':(51,'5N'),'WetFlag':(56,'1A'),'Herb':(57,'2N'),'Shrub':(59,'2N'),
              'MoistType':(61,'1N'),'MeasType':(62,'1N'),'SeasonCode':(63,'1N'),'SolarRad':(65,'4N')
              }
    Data = {}
    for f in Fields.keys():
        start, p = Fields[f]
        end = string.atoi( p[:-1] )
        format = p[-1]
        x = s[start:start+end]
        if format == 'N':
            try:
                x = string.atoi( x )
            except:
                x = -999
        Data[f] = x

    return Data

def FormatFW9( X ):
    Fields = (('W98',(0,'3A')),('Station Number',(3,'6A')),('Ob Date',(9,'8N')),('Ob Time',(17,'4N')),
              ('Type',(21,'1A')),('State of Weather',(22,'1A')),('Temp',(23,'3N')),('Moisture',(26,'3N')),
              ('WindDir',(29,'3N')),('WindSpeed',(32,'3N')),('10hr Fuel',(35,'2N')),('Tmax',(37,'3N')),
              ('Tmin',(40,'3N')),('RHmax',(43,'3N')),('RHmin',(46,'3N')),('PrecipDur',(49,'2N')),
              ('PrecipAmt',(51,'5N')),('WetFlag',(56,'1A')),('Herb',(57,'2N')),('Shrub',(59,'2N')),
              ('MoistType',(61,'1N')),('MeasType',(62,'1N')),('SeasonCode',(63,'1N')),('SolarRad',(65,'4N'))
              )
    Out = []
    for f,p in Fields:
        val = X[f]
        length = string.atoi( p[1][:-1] )
        format = p[1][-1]
        if f=='Ob Time':
            if val <100:
                val*=100
            ZeroPad = '0'
        else:
            ZeroPad = ''
        if format == 'N' and val != -999:
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


def WriteFW9( X, OutDir='.' ):
    id = X['Station Number'].replace(' ','_')
    F = open( OutDir+'/wx'+id+'.fw9', 'a')
    F.write( FormatFW9( X ) +'\n' )
    F.close()

def GetStationInfo():
    InputFile = open(CountyInfoFile, 'r')
    RawData = InputFile.readlines()
    InputFile.close()
    StationList = []
    FieldNames = RawData[0].strip().split(',')
    for record in RawData:
        values = record.strip().split(',')
        s = {}
        for k,v in map(None, FieldNames, values):
            try:
                s[k]=string.atoi(v)
            except:
                try:
                    s[k] = string.atof(v)
                except:
                    s[k] = v
        StationList.append(s)
    return StationList

def ReadFawnData():
    f = open(FawnDataFile,'r')
    i = f.readlines()
    f.close()
    Data = {}
    for r in i[1:]:
        record = ParseRecord( r )
        if record != '':
          Data[ record['LocID'] ] = record
    return Data

def ParseRecord( Record ):
    VarMap = {'SolarRad':3,
                'SoilTemp':4,
                'AirTemp6':7,
                'AirTemp2':10,
                'AirTemp30':13,
                'RH':16,
                'WindSpeed':17,
                'WindDir':19,
                'Precip':20,
                'DewPoint':22}
    Info = {}

    Fields = re.split(',', Record.strip() )
    Info['LocID'] = string.atoi(Fields[0])
    Info['RepDate'],Info['ObHr'] = ConvertDate( Fields[1] )
    for k,v in VarMap.iteritems():
        try:
            Info[k] = string.atof( Fields[v] )
        except:
            return ''
    Info['Precip'] *=1000./2.54
    Info['WindSpeed'] *= 0.621
    if Info['Precip'] > 0:
        Info['Precip']=max(5,Info['Precip'])
    return Info

def ConvertDate( d ):
    try:
        MyDate = time.strptime( d.strip(), '%m/%d/%Y %I:%M:%S %p')
    except:
        try:
            MyDate = time.strptime( d.strip(), '%B %d %Y %I:%M%p')
        except:
            try:
                MyDate = time.strptime( d.strip(), '%b %d %Y %I:%M%p')
            except:
                try:
                    MyDate = time.strptime( d.strip(), '%Y-%m-%dT%H:%M:%S-06:00')
                except:
                     try:
			MyDate = time.strptime( d.strip(), '%Y-%m-%dT%H:%M:%S-05:00')
		     except:
			   MyDate = EasternTime

    # Hour value in MyDate will be 15 minutes early, fix this
    MyDate = time.localtime(time.mktime(MyDate) + 900)

    # Check for DST - if in DST, add one hour
    if MyDate.tm_isdst == 1:
        MyDate = time.localtime(time.mktime(MyDate) + 3600)

    # Return the converted time
    return time.strftime('%Y%m%d', MyDate), (MyDate[3])

def WriteRawFawnData( stn, wx, OutDir='.' ):
    X = {'W98':'W98', 'Station Number':'000000', 'Ob Date':'YYYYMMDD', 'Ob Time':0,
              'Type':'R', 'State of Weather':0, 'Temp':0, 'Moisture':0,
              'WindDir':0, 'WindSpeed':0, '10hr Fuel':0, 'Tmax':-999,
              'Tmin':-999, 'RHmax':-999, 'RHmin':-999, 'PrecipDur':0,
              'PrecipAmt':0, 'WetFlag':'N', 'Herb':-999, 'Shrub':-999,
              'MoistType':2, 'MeasType':1, 'SeasonCode':0, 'SolarRad':0
            }
    X['Station Number'] = '0899%02d' %(stn['ID'])
    wx['Ob Date'] = YYYYMMDD
    if wx['ObHr']==13:
        X['Type']='O'
    Mon = time.localtime()[1]
    if Mon in (1,2,12):
        X['SeasonCode'] = 1
    elif Mon in (3,4,5):
        X['SeasonCode'] = 2
    elif Mon in (6,7,8):
        X['SeasonCode'] = 3
    else:
        X['SeasonCode'] = 4
    MapToFawn = {'SolarRad':'SolarRad','AirTemp6':'Temp','RH':'Moisture',
                 'WindSpeed':'WindSpeed','WindDir':'WindDir','Precip':'PrecipAmt',
                 'ObHr':'Ob Time'}
    X['Ob Date'] = string.atoi( wx['RepDate'] )
    for k in MapToFawn.keys():
        v = MapToFawn[k]
        X[v] = wx[k]
    X['Temp'] = C2F( X['Temp'] )
    WriteFW9(X, OutDir)

def C2F( T ):
    return 9./5.*T+32.

def WriteRawMetarData( stn, wx, OutDir='.' ):
    RainRates = ( 0., 0., 0., 0., 48., 24., 8., 0., 4., 1.) # hours per inch
    X = {'W98':'W98', 'Station Number':'000000', 'Ob Date':'YYYYMMDD', 'Ob Time':0,
              'Type':'R', 'State of Weather':0, 'Temp':0, 'Moisture':0,
              'WindDir':0, 'WindSpeed':0, '10hr Fuel':0, 'Tmax':-999,
              'Tmin':-999, 'RHmax':-999, 'RHmin':-999, 'PrecipDur':0,
              'PrecipAmt':0, 'WetFlag':'N', 'Herb':-999, 'Shrub':-999,
              'MoistType':2, 'MeasType':1, 'SeasonCode':0, 'SolarRad':0
            }
    X['Station Number'] = '0899%02d' %(stn['ID'])
    #X['Ob Date'] = string.atoi(eYYYYMMDD)
    # Apply local time from UTC
    obTime = time.localtime(time.mktime(GmtTime) - (stn['tzoffset']*3600))
    X['Ob Time'] = obTime[3]
    X['Ob Date'] = int(time.strftime('%Y%m%d', obTime))
    Mon = obTime[1]
    if Mon in (1,2,12):
        X['SeasonCode'] = 1
    elif Mon in (3,4,5):
        X['SeasonCode'] = 2
    elif Mon in (6,7,8):
        X['SeasonCode'] = 3
    else:
        X['SeasonCode'] = 4
    if X['Ob Time'] == 13:
        X['Type']='O'
    try:
        X['Temp'] = int(wx.temp.value("F"))
    except:
        print stn['ID']
    else:
        X['Moisture'] = wx.rh
        if wx.wind_speed != None:
            X['WindSpeed'] = wx.wind_speed.value("MPH")
        if wx.wind_dir != None:
            X['WindDir'] = int( string.atoi( str(wx.wind_dir).split(' ')[0] ) )
        if wx.PrecipEst > 5:
            X['PrecipAmt'] = wx.PrecipEst
            X['PrecipDur'] = 1
        X['SolarRad'] = wx.SolarRad
        WriteFW9(X, OutDir)

def StateOfWeather( Mx, Mn, RH, Amount, Duration ):
    Ks = 0.16+ 0.03 * ( math.tanh( 2.*(RH-40)*math.pi/100.)+1.)/2.
    FractionSolar = min( max(100. * Ks * math.sqrt( Mx - Mn ), 0.), 100)
    if (FractionSolar > 50 and (Duration<= 3)) or Duration==0:
        if FractionSolar < 60:
            StWx = 3
        elif FractionSolar < 75:
            StWx = 2
        elif FractionSolar < 91:
            StWx = 1
        else:
            StWx = 0
    else:
        RainRate = Amount / Duration
        if RainRate < 33:
            StWx = 5
        elif RainRate > 100:
            StWx = 8
        else:
            StWx=6
    return StWx

def HourlyWimsFile( stn, OutDir='.', ismetar=False ):
    SRAdjust = (1.0, 0.97, 0.95, 0.9, 0.8, 0.75, 0.7, 0.7, 0.7, 0.7, 0.7)
    #open raw wims file and read/parse last 24 records and truncate to 23 records
    id = '0899%02d' %(stn['ID'])
    F = open( OutDir+'/raw/wx'+id+'.fw9', 'r')
    Records = F.readlines()
    F.close()
    maxT  = -999
    minT  = 999
    minRH = 100
    maxRH = 0
    TotPr = 0
    DurPr = 0

    F = open( OutDir+'/raw/wx'+id+'.fw9', 'w')
    for r in Records[-24:]:
        wx = ReadFW9( r )
        maxT  = max(maxT,  wx['Temp'])
        minT  = min(minT,  wx['Temp'])
        maxRH = max(maxRH, wx['Moisture'])
        minRH = min(minRH, wx['Moisture'])
        TotPr = TotPr + wx['PrecipAmt']
        #TotPr = 0
        if wx['PrecipAmt'] > 5:
            DurPr += 1
        F.write( FormatFW9( wx ) +'\n' )
    F.close()
    PLast = wx['PrecipAmt']
    F = open( OutDir+'/wx'+id+'.fw9', 'w')
    A = open( OutDir+'/archive/wx'+id+'.fw9', 'a')
    wx['Tmax'] = maxT
    wx['Tmin'] = minT
    wx['RHmax'] = maxRH
    wx['RHmin'] = minRH
    wx['PrecipAmt'] = TotPr
    wx['PrecipDur'] = DurPr
    wx['State of Weather'] = StateOfWeather( maxT, minT, wx['Moisture'], wx['PrecipAmt'], wx['PrecipDur'] )
    F.write( FormatFW9( wx ) +'\n' )
    A.write( FormatFW9( wx ) +'\n' )
    F.close()
    A.close()
    wx['PrecipAmt'] = PLast
    if wx['SolarRad'] > 0 and ismetar:
        wx['SolarRad'] = wx['SolarRad'] * SRAdjust[int(wx['State of Weather'])]
    return wx


def SpatialAnalysis( F, X, Y ):
    AnalysisFunction = 'lambda x,y:'
    Numerator   = ''
    Denominator = ''
    for f, x, y in map(None, F, X, Y):
        IDistance = '1.0/(0.00001 +( x-%f)**2.+(y-%f)**2.)' % ( x, y)
        Value = '%f' % ( f )
        Numerator = Numerator + Value +'*'+ IDistance + '+'
        Denominator = Denominator + IDistance + '+'

    return AnalysisFunction + '(' + Numerator[:-1] + ')/(' + Denominator[:-1] + ')'

def ReadMetarData( f ):
    MetarFile = open(f,'r')
    RecordList = MetarFile.readlines()
    MetarFile.close()
    #data = map(string.strip, RecordList)
    all = string.join(RecordList,' ')
    return all

def F2C( T ):
    return 5.*(T-32.)/9.

def SatVapPres( T ):
    return math.exp( (16.78 * T - 116.9 )/( T + 237.3 ) )

def CalcRH( T, D ):
    ed = SatVapPres( F2C( D ) )
    esdb = SatVapPres( F2C( T ) )
    return int(100.*(ed/esdb))

def ParseMetar_ORIG( Station, RawMetarData ):
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
                X.rh = CalcRH( X.temp.value("F"), X.dewpt.value("F") )
            except:
                X.rh = -999
            if X.precip_1hr:
                hourlyprecip = max(hourlyprecip, X.precip_1hr.value() * 1000.0)
            X.PrecipEst = hourlyprecip
    return X

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


#=============================================================================
#=============================================================================
#=============================================================================

MyLog.info('Start at '+time.asctime(ExecutionTime) )

PrgName   = os.path.split( sys.argv[0] )[1].split('.')[0]
Config = LoadConfig( Path+'/'+PrgName+'.ini' )

if Config == {}:
    MyLog.error( Path+'/'+PrgName+'.ini not found' )
    emailIt.emailMsg('%s - Error: %s.ini not found' %(MyApp,  (Path+'/'+PrgName)) )
    sys.exit(1)

ProdDef = Config['nfdrs']
Status = DownloadFile( 'nfdrs', ProdDef, LogHour )
if Status == False:
    MyLog.error( 'Download failed' )
    emailIt.emailMsg('%s - Error: Download failed' )
    sys.exit(1)

try:
	# Read in station list
	StationList = GetStationInfo()

	MyLog.info('Reading FAWN data')
	# Read in FAWN data
	FawnData = ReadFawnData()

	## process FAWN Stations
	P  = []
	SR = []
	Lats=[]
	Lons=[]
	for s in StationList:
	    if s['type'] == 'f':
	        try:
	            #FawnData[s['stn id']]['RepDate'] = eYYYYMMDD
	            #FawnData[s['stn id']]['ObHr'] = EasternTime[3]
	            WriteRawFawnData( s, FawnData[s['stn id']], RawOutputDir )
	            NewWimsData = HourlyWimsFile( s, OutputDir )
	            P.append( NewWimsData['PrecipAmt'] )
	            SR.append( NewWimsData['SolarRad'] )
	            Lats.append( s['LAT'] )
	            Lons.append( s['LON'] )
	        except:
	            pass

	# solar radiation spatial interpolation
	if len(SR)  > 0:
	    exec( 'SolarRadiationInterp = '+SpatialAnalysis( SR,Lats,Lons ) )
	else:
	    SolarRadiationInterp = False

	MyLog.info('Reading METAR data')
	# read in metar data
	RawMetarData = ReadMetarData( MetarDataFile )

	# parse/process metar data
	for s in StationList:
	    if s['type'] != 'f':
	        MetarData = ParseMetar( s['stn id'], RawMetarData )
	        if MetarData:
	                #if MetarData.temp != None:
	                    if SolarRadiationInterp:
	                        MetarData.SolarRad = max(0, int(SolarRadiationInterp( s['LAT'],s['LON'] )))
	                    else:
	                        MetarData.SolarRad = -999

	                    WriteRawMetarData( s, MetarData, RawOutputDir )
	                    NewWimsData = HourlyWimsFile( s, OutputDir, ismetar=True )

	MyLog.info('building transfer records')
	# transfer records
	FileList = glob.glob('data/wims/*.fw9')
	FileName = 'data/wims/transfer/fl-wx-data.fw9'
	Output = []
	for fw9File in FileList:
	    fw9data = open(fw9File,'r').readlines()
	    for d in fw9data:
	        Output.append(d)
	TransferFile = open( FileName,'w')
	for d in Output:
	    TransferFile.write(d)
	TransferFile.close()

	MyLog.info('transferring data')

	client = davclient.DAVClient( url )
	client.set_basic_auth( user, passwd )
	myFile = open( FileName,'r')
	name = FileName.split('/')[-1]
	client.put(dest+name, f=myFile)

	#log = open('nfdrs.log','a')
	#log.write('wims processing completed on '+time.asctime()+'\n' )
	#log.close()
	MyLog.info('wims processing completed on '+time.asctime()+'\n' )
except Exception, err:
	MyLog.error('wims processing failed %s' % err )
	emailIt.emailMsg('%s - Error: wims processing failed %s' % (MyApp, err))
	sys.exit(1)



