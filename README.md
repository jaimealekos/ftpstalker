# FTP Stalker 0.2 by Jaime Alekos - http://www.jaimealekos.com - contacto [at] jaimealekos [dot] com
#
# When run for the first time, FTP Stalker will write a list with all the files of a given FTP server.
# The succesive times you run it it'll catch a new list, compare it with the last one and send you an
# e-mail with the new files, so just add a cron job with it with the refresh time you need.
#
# Set the FTP servers, email config and log folder in ftpstalker.ini
#
# Usage: ftpstalker --ftpname <ftpname>
