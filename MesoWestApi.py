# Import the needed libraries
import urllib, urllib2
import csv
import sys
import json
import openpyxl
from datetime import date, datetime, timedelta

# Specify the chosen parameters for the API query
base_url = 'http://api.mesowest.net/v2/stations/'
query_type = 'timeseries'
stid = 'KATT'
stid = 'APLT2' #PALESTINE RAWS
# set up date information
today = datetime.today()
one_day = timedelta(days=1)
yesterday = today - one_day
#Seven day from now (also can be changed to 30,60,90 or 180 days)
end = today.strftime("%d-%b-%y")
start = yesterday.strftime("%d-%b-%y")
print 'Start Date:', start, ' End Date: ',end
##sixty_day = datetime.timedelta(days=60)
##ninety_day = datetime.timedelta(days=90)
##hundredeighty_day = datetime.timedelta(days=180)
##one_day = datetime.timedelta(days=1)
##yesterday = today - one_day
##sixtyday = today - sixty_day
##ninetyday = today - ninety_day
##hundredeightyday = today - hundredeighty_day
##start = yesterday.strftime("%d-%b-%y")
##start = sixtyday.strftime("%d-%b-%y")
##start = ninetyday.strftime("%d-%b-%y")
##start = hundredeightyday.strftime("%d-%b-%y")
start_date = '201604130000'
end_date   = '201607140000'
start_date = '201609260000'
end_date   = '201609270000'
vars = 'air_temp,wind_speed,wind_direction'
#vars = 'TMPF,MSKT,DRCT'#Using abbrievation!
token = 'demotoken' ##this used a demo token
my_api_token = '994a7e628db34fc68503d44c447aaa6f'
token = my_api_token
csv_format = '&output=csv'

# Create the API URL string
'''
api_string = base_url + query_type + '?' + 'stid=' + stid + '&start=' + start_date +\
    '&end=' + end_date + '&vars=' + vars + '&token=' + token + csv_format

print api_string
##api.mesowest.net/v2/stations/timeseries?stid=APLT2&token=demotoken&start=201604130000&end=201607140000
##http://api.mesowest.net/v2/stations/timeseries?stid=APLT2&start=201604130000&end=201607140000&vars=air_temp,wind_speed,wind_direction&token=demotoken&output=csv
# Read the API response in CSV format into program memory.
response = urllib2.urlopen(api_string)

#get a whole list of variable names from mesowest api
#dict_variable = urllib2.urlopen('http://api.mesowest.net/v2/variables?&token=demotoken')

dict_variable=response

print dict_variable

##file = csv.reader(dict_variable)
##data = [row for row in file]

file = csv.reader(response)

for row in file:
    print row

data = [row for row in file]

#print data

# The first 8 rows are metadata from the API return
metadata = data[0:8]
# Put remaining rows into a list of lists
data_rows = data[8:]

# Create variables to store the columns in
stn_id = ['']*len(data_rows)
dattim = ['']*len(data_rows)
air_temp = [0]*len(data_rows)
wind_spd = [0]*len(data_rows)
wind_dir = [0]*len(data_rows)

#print stn_id,dattim

# Put the variables into separate column lists
# At this point, all variables should be strings, user will need
# to convert them as needed for their purposes.
# User will also need to format the date-time strings as needed.
# NOTE: Wind speeds of zero have empty elements for wind directions.
for i in range(len(data_rows)):
    stn_id[i] = data_rows[i][0]
    dattim[i] = data_rows[i][1]
    air_temp[i] = data_rows[i][2]
    wind_spd[i] = data_rows[i][3]
    wind_dir[i] = data_rows[i][4]
'''

#####################################
##test for downloading today's date (but RAAWS only for one day) as result of csv file
#This could be a zulu time, for e.g. the central time 14:00 (PM) is 18:00
#http://api.mesowest.net/v2/stations/timeseries?state=dc&start=201307010000&end=201307020000&vars=air_temp,pressure&obtimezone=local&token=demotoken
start_date = '201607171700'
end_date   = '201607181800'

start_date = '201608021400'
end_date   = '201608041400'

start_date = '200501010000'
end_date   = '201608180000'

start_date = '201609191400'
end_date   = '201609201400'

timezone = 'local'

##start_date = '201609180800'
##end_date   = '201609190800'

start_date = '201609191400'
end_date   = '201609201400'

start_date = '201609181700'
end_date   = '201609201900'

start_date = '201609260000'
end_date   = '201609270000'

timezone = 'UTC'

stid = 'KELP' #ASOS stations
#stid = 'APLT2' #PALESTINE RAWS
varlst = ['air_temp', 'dew_point_temperature', 'relative_humidity', 'wind_speed', 'wind_direction', 'wind_gust', 'altimeter', 'pressure', 'snow_depth', 'solar_radiation', 'soil_temp', 'precip_accum', 'precip_accum_one_minute', 'precip_accum_ten_minute', 'precip_accum_fifteen_minute', 'precip_accum_30_minute', 'precip_accum_one_hour', 'precip_accum_three_hour', 'sea_level_pressure', 'sun_hours', 'water_temp', 'weather_cond_code', 'cloud_layer_3_code', 'cloud_low_symbol', 'cloud_mid_symbol', 'cloud_high_symbol', 'pressure_tendency', 'qc', 'snow_accum', 'precip_storm', 'road_sensor_num', 'road_temp', 'road_freezing_temp', 'road_surface_condition', 'unknown', 'cloud_layer_1_code', 'cloud_layer_2_code', 'precip_accum_six_hour', 'precip_accum_24_hour', 'visibility', 'sonic_wind_direction', 'remark', 'raw_ob', 'air_temp_high_6_hour', 'air_temp_low_6_hour', 'peak_wind_speed', 'fuel_temp', 'fuel_moisture', 'ceiling', 'sonic_wind_speed', 'pressure_change_code', 'precip_smoothed', 'soil_temp_ir', 'temp_in_case', 'soil_moisture', 'volt', 'created_time_stamp', 'last_modified', 'snow_smoothed', 'precip_manual', 'precip_accum_manual', 'precip_accum_5_minute_manual', 'precip_accum_10_minute_manual', 'precip_accum_15_minute_manual', 'precip_accum_3_hour_manual', 'precip_accum_6_hour_manual', 'precip_accum_24_hour_manual', 'snow_accum_manual', 'snow_interval', 'road_subsurface_tmp', 'T_water_temp', 'evapotranspiration', 'snow_water_equiv', 'precipitable_water_vapor', 'air_temp_high_24_hour', 'air_temp_low_24_hour', 'peak_wind_direction', 'net_radiation', 'soil_moisture_tension', 'pressure_1500_meter', 'air_temp_wet_bulb', 'air_temp_2m', 'air_temp_10m', 'm_pressure', 'm_air_temp', 'm_relative_humidity', 'm_wind_speed', 'm_wind_direction', 'm_wind_gust', 'm_latitude', 'm_longitude', 'm_elevation', 'surface_temp', 'net_radiation_sw', 'net_radiation_lw', 'sonic_air_temp', 'sonic_vertical_vel', 'sonic_zonal_wind_stdev', 'sonic_vertical_wind_stdev', 'sonic_air_temp_stdev', 'vertical_heat_flux', 'friction_velocity', 'w_ratio', 'sonic_ob_count', 'sonic_warn_count', 'moisture_stdev', 'vertical_moisture_flux', 'M_dew_point_temperature', 'virtual_temp', 'geopotential_height', 'outgoing_radiation_sw', 'PM_25_concentration', 'filter_percentage', 'sensor_error_code', 'electric_conductivity', 'precip_accum_five_minute', 'particulate_concentration', 'precip_accum_since_local_midnight', 'black_carbon_concentration', 'stream_flow', 'gage_height', 'permittivity']
vars=''
for var in varlst:
    vars = vars + ',' + var
#vars = varlst
#vars = 'air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,altimeter,pressure,snow_depth,solar_radiation,soil_temp,precip_accum,precip_accum_one_minute,precip_accum_ten_minute,precip_accum_fifteen_minute,precip_accum_30_minute,precip_accum_one_hour,precip_accum_three_hour,sea_level_pressure,sun_hours,water_temp,weather_cond_code,cloud_layer_3_code,cloud_low_symbol,cloud_mid_symbol,cloud_high_symbol,pressure_tendency,qc,snow_accum,precip_storm,road_sensor_num,road_temp,road_freezing_temp,road_surface_condition,unknown,cloud_layer_1_code,cloud_layer_2_code,precip_accum_six_hour,precip_accum_24_hour,visibility,sonic_wind_direction,remark,raw_ob,air_temp_high_6_hour,air_temp_low_6_hour,peak_wind_speed,fuel_temp,fuel_moisture,ceiling,sonic_wind_speed,pressure_change_code,precip_smoothed,soil_temp_ir,temp_in_case,soil_moisture,volt,created_time_stamp,last_modified,snow_smoothed,precip_manual,precip_accum_manual,precip_accum_5_minute_manual,precip_accum_10_minute_manual,precip_accum_15_minute_manual,precip_accum_3_hour_manual,precip_accum_6_hour_manual,precip_accum_24_hour_manual,snow_accum_manual,snow_interval,road_subsurface_tmp,T_water_temp,evapotranspiration,snow_water_equiv,precipitable_water_vapor,air_temp_high_24_hour,air_temp_low_24_hour,peak_wind_direction,net_radiation,soil_moisture_tension,pressure_1500_meter,air_temp_wet_bulb,air_temp_2m,air_temp_10m,m_pressure,m_air_temp,m_relative_humidity,m_wind_speed,m_wind_direction,m_wind_gust,m_latitude,m_longitude,m_elevation,surface_temp,net_radiation_sw,net_radiation_lw,sonic_air_temp,sonic_vertical_vel,sonic_zonal_wind_stdev,sonic_vertical_wind_stdev,sonic_air_temp_stdev,vertical_heat_flux,friction_velocity,w_ratio,sonic_ob_count,sonic_warn_count,moisture_stdev,vertical_moisture_flux,M_dew_point_temperature,virtual_temp,geopotential_height,outgoing_radiation_sw,PM_25_concentration,filter_percentage,sensor_error_code,electric_conductivity,precip_accum_five_minute,particulate_concentration,precip_accum_since_local_midnight,black_carbon_concentration,stream_flow,gage_height,permittivity'
#for ASOS
vars = 'metar,air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,precip_accum,precip_accum_one_hour,weather_cond_code,cloud_layer_3_code,cloud_layer_1_code,cloud_layer_2_code,precip_accum_24_hour,visibility,peak_wind_speed,fuel_moisture,soil_moisture,air_temp_high_24_hour,air_temp_low_24_hour,peak_wind_direction,cloud_layer_3_code, cloud_low_symbol, cloud_mid_symbol, cloud_high_symbol'
##       'air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,solar_radiation,precip_accum,precip_accum_one_hour,precip_accum_24_hour,peak_wind_speed,fuel_moisture,weather_cond_code,cloud_layer_3_code,cloud_layer_1_code,cloud_layer_2_code'
#vars ='air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,solar_radiation,precip_accum,precip_accum_one_hour,weather_cond_code,cloud_layer_3_code,precip_accum_24_hour,metar,peak_wind_speed,fuel_moisture,precip_manual,precip_accum_manual,precip_accum_24_hour_manual,air_temp_high_24_hour,air_temp_low_24_hour,peak_wind_direction,net_radiation,past_weather_code,cloud_layer_3_code, cloud_low_symbol, cloud_mid_symbol, cloud_high_symbol'
#vars ='precip_accum_one_hour'
#vars = 'precip_accum,precip_accum_24_hour,precip_accum_one_hour'
#For RAWS
#vars ='air_temp,dew_point_temperature,relative_humidity,wind_speed,wind_direction,wind_gust,solar_radiation,precip_accum,precip_accum_one_hour,precip_accum_24_hour,peak_wind_speed,fuel_moisture,weather_cond_code,cloud_layer_3_code,cloud_layer_1_code,cloud_layer_2_code'

##api_string = base_url + query_type + '?' + 'stid=' + stid + '&start=' + start_date +\
##    '&end=' + end_date + '&vars=' + vars + '&obtimezone=' + timezone + '&token=' + token + csv_format

#Without specifying the time zone
api_string = base_url + query_type + '?' + 'stid=' + stid + '&start=' + start_date +\
    '&end=' + end_date + '&vars=' + vars +  '&token=' + token + csv_format
#csvfile = r'c:\\DEV\\ASOS\\PALESTINE0912more.csv'
csvfile = 'c:\\DEV\\ASOS\\' + stid + end_date + '.csv'
print api_string
urllib.urlretrieve(api_string,csvfile)
