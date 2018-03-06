import urllib
download = 'http://api.mesowest.net/v2/stations/timeseries?state=tx&start=201506251800&end=201506261800&vars=solar_radiation&obtimezone=local&token=1234567890'
fhand= urllib.urlopen(download)
for line in fhand:
    print line
