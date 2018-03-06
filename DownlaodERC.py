#-------------------------------------------------------------------------------
# Name:        ArchiveERCgraph.py
# Purpose:     Download the ERC graphs using a link provided
# Problem :    Not able to get the timestamp on the downloaded files
# Author:      pyang
# Created:     18/02/2016
# Copyright:   (c) pyang 2016
#-------------------------------------------------------------------------------

import urllib2,urllib
import re
import os
import sys
import datetime
from PyPDF2 import PdfFileMerger, PdfFileReader

today = datetime.datetime.today().strftime("%Y%m%d")

WorkSpace = os.getcwd()

Download = os.path.join(WorkSpace, "Download")

Archive = os.path.join(WorkSpace, "Archive")

##if os.path.exists(Download):
##    os.remove(Download)
##    os.makedirs(Download)
##else:
##    os.makedirs(Download)


if not os.path.exists(Archive):
    os.makedirs(Archive)

links = []
PSAPDF ={'CENTRLTX':'erc_ctx',
                'NTXS':'erc_ntx',
                'TRANSPEC':"erc_tp",
                'ROLLPLN':"erc_rp",
                'SETX':"erc_setx",
                'NETX':"erc_netx",
                'COASTLPL':"erc_cp",
                'HIGHPLAN':"erc_hp",
                'HILLCNTY':"erc_hc",
                'LOWCOAST':"erc_lgc",
                'RIOGRAND':"erc_rgp",
                'SOUTHPLN':"erc_sp",
                'UPRCOAST':"erc_ugc",
                'WESTPINE':"erc_wpw"}
for key, fn in PSAPDF.items():
    psapdf = 'http://ticc.tamu.edu/Documents/PredictiveServices/Fuels/' + fn + '.pdf'
    psapng = 'http://ticc.tamu.edu/Documents/PredictiveServices/Fuels/' + fn + '.png'
    print key,psapng
    links.append((psapdf,'http'))


#print links
for link in links:
    if '.pdf' in link[0]:
        index = link[0].rfind('/')+1
        filename = link[0][index:]
        print filename + ' is downloading...'
        try:
            urllib.urlretrieve(link[0],os.path.join(Download,filename))
        except:
            print "Unexpected error:", sys.exc_info()[0]

filenames = os.listdir(Download)
merger = PdfFileMerger()
os.chdir(Download)
for filename in filenames:
    merger.append(PdfFileReader(file(filename, 'rb')))
ArchiveFile = os.path.join(Archive, today +"_ERC.pdf")
merger.write(ArchiveFile)
