import csv
import os
import shutil
###------------------------------------------------------------------------------------------------
### Functions for reading the station list from a csv(or text file with ',' delemitated)
### Input: A csv file with two columns for station name and staiton id
### Output: Dictionary (X) that contains station name and station id
###--------------------------------------------------------------------------------------------
def readDict(fn):
    f=open(fn,'rb')
    dict_rap={}
    for key, val in csv.reader(f):
        dict_rap[key]=eval(val)
    f.close()
    return(dict_rap)

fn = r"C:\DEV\ASOS\PRCP\ID_Name.csv"
f=open(fn,'rb')
rd = csv.reader(f)
dict_rap={}
for stname in rd:
    #print stname[0],stname[1]
    key =stname[0]
    val =stname[1]
    dict_rap[key]=val


#readDict(fn)
##f= open(fn,'rb')
##rawlist = []
##for sta in f:
##    rawlist.append(sta.strip())
##    #print sta
##
##
##Stations = {"KDHT": 418702,
##            "KAMA": 418803,
##            "KSPS": 419302,
##            "KINK": 417501,
##            "KFST": 417601,
##            "KLBB": 419002,
##            "KJCT": 417803,
##            "KSJT": 419204,
##            "KELP": 416901,
##            "KDRT": 418003,
##            "KHDO": 418103,
##            "KSSF": 418104,
##            "KCOT": 418402,
##            "KALI": 418504,
##            "KBAZ": 418105,
##            "KCLL": 413901,
##            "KCRS": 412001,
##            "KTYR": 411701,
##            "KTRL": 419703,
##            "KDTO": 419603,
##            "KMWL": 419404}
##
##asoslist = []
##for key,value in Stations.items():
##    asoslist.append(key)
##
##
##stalist = rawlist + asoslist
##
##for raw in stalist:
##    print raw
##
##print os.listdir("c:\\DEV\\ASOS\\PRCP\\Since2005")
##list = os.listdir("c:\\DEV\\ASOS\\PRCP\\Since2005")
##
##
##fn = r"C:\DEV\ASOS\PRCP\station2005.txt"
##f=open(fn,'rb')
####for sta in dict_rap:
####    print sta,dict_rap[sta]
##for sta in f:
##    print sta.strip(),':', dict_rap[sta.strip()]
##    if sta in dict_rap:
##        print dict_rap[sta]

list = os.listdir("D:\PRISM\PRISM_ppt_stable_4kmM3_201602_201607_bil")
#print list
for fn in list:
    newfn = fn[:10]+'stable'+fn[21:]
    sourcefile = "D:\\PRISM\\PRISM_ppt_stable_4kmM3_201602_201607_bil\\" + fn
    destfile = "D:\\PRISM\\PRISM_ppt_stable_4kmM3_201602_201607_bil\\" + newfn
    shutil.copyfile(sourcefile,destfile)
