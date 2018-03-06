#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Yang
#
# Created:     12/09/2015
# Copyright:   (c) Yang 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import easywebdav

webdav = easywebdav.connect(
    host='https://fam.nwcg.gov/fam-web/wims_dav/incoming',
    username='mdunivan',
    #port=443,
    protocol="https",
    password='T43Gr8T3X@S!')

webdav = easywebdav.connect('https://fam.nwcg.gov', username='mdunivan', password='T43Gr8T3X@S!')


#_file = "ez_setup.py"
#print webdav.cd('fam-web/wims_dav/incoming')
#print webdav.ls('fam-web/wims_dav/incoming')
# print webdav._get_url("")
print webdav.ls()
# print webdav.exists("/dav/test.py")
# print webdav.exists("ECS.zip")
# print webdav.download(_file, "./"+_file)
#print webdav.upload("", "C:\\DEV\\ASOS\\2015092917.fw9")