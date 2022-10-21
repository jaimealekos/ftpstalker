# ____________________________    _________________________  .____     ____  ________________________ 
# \_   _____     __/\______   \  /   _____/\__    ___/  _  \ |    |   |    |/ ___    _____/\______   \
#  |   ___) |   |    |     ___/  \_____  \   |    | /  /_\  \|    |   |      <   |    __)_  |       _/
#  |   \    |   |    |    |      /        \  |    |/    |    \    |___|    |  \  |        \ |    |   \
#  \___/    |___|    |____|     /_________/  |____|\____|____/________.____|___\/_________/ |____|_  /
#                                                                                                  \/ 
# FTP Stalker 0.2 by Jaime Alekos - http://www.jaimealekos.com - contacto [at] jaimealekos [dot] com
#
# When run for the first time, FTP Stalker will write a list with all the files of a given FTP server.
# The succesive times you run it it'll catch a new list, compare it with the last one and send you an
# e-mail with the new files, so just add a cron job with it with the refresh time you need.
#
# Set the FTP servers, email config and log folder in ftpstalker.ini
#
# Usage: ftpstalker --ftpname <ftpname>


import sys
from math import floor, log, pow
from argparse import ArgumentParser
from dateutil import parser
import ftplib
from smtplib import SMTP
from os import path, mkdir, remove, rename, getcwd
from datetime import datetime
from email.mime.text import MIMEText
from configparser import ConfigParser
from email.mime.multipart import MIMEMultipart

p=ArgumentParser()
p.add_argument('--ftpname', type=str, required=True, help="ftp name from config file")
args=p.parse_args()

conf=ConfigParser()
conf.read(sys.path[0]+"/ftpstalker.ini")

for section in conf.sections():  # Parses config file
    if section=="general":
        for (key, val) in conf.items(section):
            if key=="logfolder":
                logfolder=val        
                if logfolder[-1] != "/": logfolder=logfolder+"/"
                if path.isdir(logfolder) == False: mkdir(logfolder)
    elif section=="email-config": # Takes email
        for (key, val) in conf.items(section):
            if key=="smtpserver": smtpServer=val
            elif key=="mailfrom": mailFrom=val
            elif key=="mailpass": mailPass=val
            elif key=="mailto": mailTo=val    
    elif section==args.ftpname: 
        for (key, val) in conf.items(section):
            if key=="ftphost": ftpHost=val
            elif key=="ftpport": ftpPort=val
            elif key=="ftpuser": ftpUser=val
            elif key=="ftppass": ftpPass=val
            elif key=="ftpdir": ftpDir=val
        ftp=[section, ftpHost, ftpPort, ftpUser, ftpPass, ftpDir]
        oldlog=logfolder+section+"/old.log"
        newlog=logfolder+section+"/new.log"
        if path.isdir(logfolder+section+"/") == False: mkdir(logfolder+section+"/")

def recursive_mlsd(ftp, files, dir): # Takes FTP object and path, returns array with all recursive files using MLSD
    folders=([])

    mlsd=ftp.mlsd(dir)
    
    for item in mlsd:
        if item[1]['type'] == 'dir':
            path=dir+item[0]
            if path[-1] != "/": path+="/"
            folders.append(path)
        elif item[1]['type'] == 'file':
            files.append(dir+item[0])
    
    files.sort()
    folders.sort()

    for folder in folders: recursive_mlsd(ftp, files, folder)

    return files

def recursive_nlst(ftp, files, dir): # Same but using NLST when MLSD's not available - CWD's everything to separate files from folders
    folders=([])

    nlst=ftp.nlst(dir)

    for item in nlst:
        try:
            a=ftp.cwd(item)
            path=item
            if path[-1] != "/": path+="/"
            folders.append(path)                                    
        except:            
            files.append(item)

    files.sort()
    folders.sort()

    for folder in folders: recursive_nlst(ftp, files, folder)            

    return files

def write_new_log(files, logfile): 
    f = open(logfile,"a")                 
    for file in files:        
        f.write(file+"\n")        
    f.close

def compare_logs(new_one, old_one): # Returns an array with the new files - or an empty array if there's no difference
    oldlogLines=open(old_one, 'r').readlines()
    newlogLines=open(new_one, 'r').readlines()

    newOnes = []

    for newLine in newlogLines:
        if newLine not in oldlogLines:
            newOnes.append(newLine)

    return newOnes

def convert_size(size_bytes): # Bytes to human readable
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i=int(floor(log(size_bytes, 1024)))
   p=pow(1024, i)
   s=round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])    

def send_report(newFiles, allfiles): # Takes an array with the new files and sends report
    mail_content = "FTP Stalker 0.2 - Reporting <b>" + str(len(newFiles)) + "</b> new files ("+str(len(allfiles))+" total) since "+lastlogTime+" in <b>" + ftp[1] + ftp[5] + "</b><br /><br />"
    for file in newFiles:
        mail_content+=file+"<br />"

    message=MIMEMultipart()
    message["From"]=mailFrom
    message["To"]=mailTo
    message["Subject"] = "FTP Stalker report - " + str(datetime.today())[0:10] + " - " + ftp[1] + ftp[5]
    message.attach(MIMEText(mail_content, "html"))
    session=SMTP(smtpServer, 587)
    session.starttls()
    session.login(mailFrom, mailPass) 
    text = message.as_string()
    session.sendmail(mailFrom, mailTo, text)
    session.quit()    

    print("Report succesfully sent to "+mailTo+"\n\n")

print("____________________________    _________________________  .____     ____  ________________________ ")
print("\\_   _____     __/\\______   \  /   _____/\\__    ___/  _  \\ |    |   |    |/ ___    _____/\\______   \\")
print(" |   ___) |   |    |     ___/  \_____  \   |    | /  /_\  \|    |   |      <   |    __)_  |       _/")
print(" |   \\    |   |    |    |      /        \\  |    |/    |    \\    |___|    |  \\  |        \\ |    |   \\")
print(" \\___/    |___|    |____|     /_________/  |____|\\____|____/________.____|___\\/_________/ |____|_  /")
print("                                                                                                 \\/ ")
print("\033[1mFTP Stalker 0.2 by Jaime Alekos\033[0m - http://www.jaimealekos.com - contacto [at] jaimealekos [dot] com\n")    
print("SCANNING "+args.ftpname+"\n")

ftp_host=ftplib.FTP(ftp[1])
ftp_host.login(ftp[3],ftp[4])
feat=ftp_host.sendcmd("FEAT")

files=([])

if "MLST" in feat: 
    files=recursive_mlsd(ftp_host, files, ftp[5])
elif "MDTM" in feat:
    files=recursive_nlst(ftp_host, files, ftp[5])

if path.isfile(newlog) == False:
    write_new_log(files, newlog) 
    print(ftp[0] + " has just been stalked for the first time, "+str(len(files))+" files indexed, halting program...\n\n")
    exit()

if path.isfile(oldlog) == True: remove(oldlog) 
rename(newlog, oldlog)
lastlogTime=datetime.utcfromtimestamp(path.getmtime(oldlog)).strftime('%Y-%m-%d %H:%M:%S')
write_new_log(files, newlog) 

newOnes=compare_logs(newlog, oldlog)

if len(newOnes) == 0:
    print(ftpHost + " has no new files since the last log ("+lastlogTime+")\n\n")
    exit()    

newOnesDate = [] # Paralel array with file date
for newFile in newOnes:
    timestamp = ftp_host.voidcmd("MDTM "+newFile.strip())
    newOnesDate.append(str(parser.parse(timestamp[4:])))    

ftp_host.sendcmd("TYPE i")

newOnesSize = [] # Paralel array with file size
for newFile in newOnes:       
    newOnesSize.append(ftp_host.size(newFile.strip()))    

ftp_host.quit()

print(str(len(newOnes)) +" new files found!\n")

c=0 # Merges the three paralel arrays: files, date and size
for newFile in newOnes:
    justPath, justFilename = path.split(newFile.strip())    
    newOnes[c]=newOnesDate[c]+" "+justPath+"/<b>"+justFilename+"</b> ("+convert_size(newOnesSize[c])+")"
    c+=1

send_report(newOnes, files)
