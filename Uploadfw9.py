##import davclient
##url = "https://famtest.nwcg.gov/fam-web/wims_dav/incoming"
##user = "mdunivan"
##passwd = "T43Gr8T3X@S!"
##dest= ''
##
##client = davclient.DAVClient( url )
##client.set_basic_auth( user, passwd )
##
##FileName = "c:\\DEV\ASOS\\tx-asos.fw9"
##myFile = open(FileName,'r')
###fw9data = open(FileName,'r').readlines()
###for d in fw9data:
###    print d
##name = FileName[12:]
##print client.put(dest + name, f=myFile)
####
####    put(self, path, body=None, f=None, headers=None)
####      Put resource with body
##myFile.close()
import subprocess
import shutil
url = "https://famtest.nwcg.gov/fam-web/wims_dav/incoming"
user = "mdunivan"
passwd = "T43Gr8T3X@S!"
winCMD = 'NET USE g:' + url + ' /User:' + user + ' ' + passwd
subprocess.Popen(winCMD, stdout=subprocess.PIPE, shell=True)
#shutil.copy2(url + 'c:\\DEV\ASOS\\tx-asos.fw9', './tx-asos.fw9')
