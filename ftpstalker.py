# ____________________________    _________________________  .____     ____  ________________________ 
# \_   _____     __/\______   \  /   _____/\__    ___/  _  \ |    |   |    |/ ___    _____/\______   \
#  |   ___) |   |    |     ___/  \_____  \   |    | /  /_\  \|    |   |      <   |    __)_  |       _/
#  |   \    |   |    |    |      /        \  |    |/    |    \    |___|    |  \  |        \ |    |   \
#  \___/    |___|    |____|     /_________/  |____|\____|____/________.____|___\/_________/ |____|_  /
#                                                                                                  \/ 
# FTP Stalker 0.1 by Jaime Alekos - http://www.jaimealekos.com - contacto [at] jaimealekos [dot] com
#
# When run for the first time, FTP Stalker will write a list with all the files of a given FTP server.
# The succesive times you run it it'll catch a new list, compare it with the last one and send you an
# e-mail with the new files, so just add a cron job with it with the refresh time you need.

ftpHost = ""
ftpLogin = ""
ftpPass = ""
ftpInitDir = ""
listLogPath = ""

smtp_server = ""
sender_address = ""
sender_pass = ""
receiver_address = ""

import ftplib
import os
import math
from genericpath import isfile
from datetime import datetime, timedelta
from dateutil import parser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class DirEntry:
    def __init__(self, filename, ftpobj, startingdir = None):
        self.filename = filename
        if startingdir == None:
            startingdir = ftpobj.pwd()
        try:
            ftpobj.cwd(filename)
            self.filetype = 'd'
            ftpobj.cwd(startingdir)
        except ftplib.error_perm:
            self.filetype = 'f'
        
    def gettype(self): return self.filetype
    def getfilename(self): return self.filename

def writeTodaysLog(ftpFiles):    
    if os.path.isdir(listLogPath) == False: os.mkdir(listLogPath)
    
    with open(os.path.join(listLogPath+"newlog.txt"), "w") as fp: 
        pass   

    for item in ftpFiles:               
        f = open(listLogPath+"newlog.txt","a")                 
        f.write(item+"\n")

def ftpScan(ftp, ftpPath):
    ftp.cwd(ftpPath)

    rootList = ftp.nlst()  

    rootItems = [DirEntry(item, ftp, ftpPath) for item in rootList]
    arrayFiles = []
    arrayFolders = []
    for item in rootItems:
        if item.gettype() == "f":
            arrayFiles.append(ftp.pwd() + "/" + item.getfilename())        
        elif item.gettype() == "d":
            arrayFolders.append(ftp.pwd() + "/" + item.getfilename() + "/")
    arrayFiles.sort()
    arrayFolders.sort()
    for item in arrayFolders:                
        files2 = ftpScan(ftp, item)
        for item in files2: arrayFiles.append(item)
    return arrayFiles

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

print("____________________________    _________________________  .____     ____  ________________________ ")
print("\\_   _____     __/\\______   \  /   _____/\\__    ___/  _  \\ |    |   |    |/ ___    _____/\\______   \\")
print(" |   ___) |   |    |     ___/  \_____  \   |    | /  /_\  \|    |   |      <   |    __)_  |       _/")
print(" |   \\    |   |    |    |      /        \\  |    |/    |    \\    |___|    |  \\  |        \\ |    |   \\")
print(" \\___/    |___|    |____|     /_________/  |____|\\____|____/________.____|___\\/_________/ |____|_  /")
print("                                                                                                 \\/ ")
print("\033[1mFTP Stalker 0.1 by Jaime Alekos\033[0m - http://www.jaimealekos.com - contacto [at] jaimealekos [dot] com\n\n")

if os.path.isfile(listLogPath+"newlog.txt") == True:
    if os.path.isfile(listLogPath+"oldlog.txt") == True:
        os.remove(listLogPath+"oldlog.txt")
    os.rename(listLogPath+"newlog.txt", listLogPath+"oldlog.txt")

ftp = ftplib.FTP(ftpHost)
ftp.login(ftpLogin, ftpPass)
ftp.cwd(ftpInitDir)

ftpFiles = ftpScan(ftp, ftpInitDir)

writeTodaysLog(ftpFiles)
print("Successfully stalked " + "\033[95m" + ftpHost + "\033[0m\n")

if os.path.isfile(listLogPath+"oldlog.txt") == False:
    print(ftpHost + " has just been stalked for the first time, halting program...\n\n")
    exit()

readLog = open(listLogPath+"oldlog.txt", 'r')
yesterdayLog = readLog.readlines()
readLog = open(listLogPath+"newlog.txt", 'r')
todayLog = readLog.readlines()  

newOnes = []

for todayLine in todayLog:    
    match=False
    for yesterdayLine in yesterdayLog:        
        if yesterdayLine == todayLine: match=True
    if match == False:
        newOnes.append(todayLine)

if len(newOnes) == 0:
    print(ftpHost + " has no new files since the last log\n\n")
    exit()    

newOnesDate = []
for newFile in newOnes:
    timestamp = ftp.voidcmd("MDTM "+newFile.strip())
    newOnesDate.append(str(parser.parse(timestamp[4:])))    

ftp.sendcmd("TYPE i")
newOnesSize = []
for newFile in newOnes:       
    newOnesSize.append(ftp.size(newFile.strip()))    

quitReply = ftp.quit()

print(str(len(newOnes)) +" new files found!\n")

mail_content = "FTP Stalker 0.1 - Reporting new files (<b>" + str(len(newOnes)) + "</b>) for the last 24 hours in <b>" + ftpHost + ftpInitDir + "</b><br /><br />"

newOnesCont = 0
for newFile in newOnes:
    justPath, justFilename = os.path.split(newOnes[newOnesCont])    
    mail_content+="- " + newOnesDate[newOnesCont] + "  " + justPath + "/<b>" + justFilename + "</b> (" + convert_size(newOnesSize[newOnesCont]) + ") <br />"
    newOnesCont+=1

message = MIMEMultipart()
message["From"] = sender_address
message["To"] = receiver_address
message["Subject"] = "FTP Stalker report - " + str(datetime.today())[0:10] + " - " + ftpHost + ftpInitDir
message.attach(MIMEText(mail_content, "html"))
session = smtplib.SMTP(smtp_server, 587)
session.starttls()
session.login(sender_address, sender_pass) 
text = message.as_string()
session.sendmail(sender_address, receiver_address, text)
session.quit()

print("Today's report succesfully sent to "+receiver_address+"\n\n")