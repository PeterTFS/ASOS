import datetime
##zuluTimeNow = datetime.datetime.utcnow()
##print zuluTimeNow
##UTCHOUR = "T19:00:00Z"
##currentzuluTime = datetime.datetime.strptime(UTCHOUR,"T%H:%M:%SZ")
##currentzuluTime = zuluTimeNow.replace(hour=currentzuluTime.time().hour, minute=currentzuluTime.time().minute, second=currentzuluTime.time().second, microsecond=0)
##print currentzuluTime
##if (zuluTimeNow > currentzuluTime):
##    print "Process data for today"
##else:
##    print "Process data for yesterday"


zuluTimeNow = datetime.datetime.utcnow()
##    utc= datetime.datetime.strptime(TIMESTR,"%Y-%m-%dT%H:%M:%SZ")
##    standard = utc - timedelta(hours=6)
zuluTime24Hour = zuluTimeNow - timedelta(hours=24)

zuluTimeOneWeek = zuluTimeNow - timedelta(hours=168)

print zuluTimeNow.strftime("%Y-%m-%d %H:%M:%S")
print zuluTime24Hour.strftime("%Y-%m-%d %H:%M:%S")
print zuluTimeOneWeek.strftime("%Y-%m-%d %H:%M:%S")
