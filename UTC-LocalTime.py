from datetime import *
from dateutil import *
from dateutil.tz import *

localTimeNow = datetime.now()
zuluTimeNow = datetime.utcnow()



# METHOD 1: Hardcode zones:
##utc_zone = tz.gettz('UTC')
##local_zone = tz.gettz('America/Chicago')
# METHOD 2: Auto-detect zones:
utc_zone = tz.tzutc()
local_zone = tz.tzlocal()

# Convert time string to datetime
local_time = datetime.strptime('2017-03-07 16:15:35', '%Y-%m-%d %H:%M:%S')


local_time= datetime.now()
# Tell the datetime object that it's in local time zone since
# datetime objects are 'naive' by default
local_time = local_time.replace(tzinfo=local_zone)
# Convert time to UTC
utc_time = local_time.astimezone(utc_zone)
# Generate UTC time string
utc_string = utc_time.strftime('%Y-%m-%d %H:%M:%S')

#print localTimeNow,zuluTimeNow
print utc_string,'-------------',zuluTimeNow.strftime('%Y-%m-%d %H:%M:%S')
