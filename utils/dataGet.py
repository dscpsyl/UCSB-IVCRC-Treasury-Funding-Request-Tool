import datetime
from datetime import datetime as dt
from datetime import timedelta
import json as js
from utils import sqlite
from utils import drive
from utils import sqlite
import shutil
import sys

import logging as log
log.basicConfig(level=log.INFO, format='%(message)s')

def initInput(settings, creds, conn):
    dateReq = input("$: Date Requested (12/20/15): ")
    dateStart = input("$: Start Date (12/20/15): ")
    dateEnd = input("$: End Date (12/20/15): ")
    name = input("$: Project Name: ")
    recipient = input("$: Recipient: ")
    categoryNo = input("$: Category Enter Number([1]AS/[2]External/[3]Internal/[4]UCSB): ")
    amount = input("$: Amount: ")
    
    log.info("\n")
    log.info("What is the Meeting Minutes Doc? Please Choose from the list below. (Press enter for the first option)")

    l = drive.driveLIST("drive", settings["IVCRC_SHARED_DRIVE_ID"], "files/id,files/name", True, "folder", "1000", None, "parents in '" + settings["minutesDriveFolderId"] + "'", True, creds)

    f = l["files"]
    for index, file in enumerate(f):
        print(str(index) + ": " + file["name"])
        if index > 5:
            break  

    minutesId = input("$: ")
    if minutesId == "":
        minutesId = f[0]["id"]
        meetingName = f[0]["name"]
    elif len(minutesId) < 2:
        meetingName = f[int(minutesId)]["name"]
        minutesId = f[int(minutesId)]["id"]
    else:
        log.critical("Invalid Input. Aborting.")
        sys.exit(1)
    
    meetingName = meetingName.split(" ")
    passedDateObj = dt.strptime(meetingName[0], "%Y/%m/%d")
    datePass = dt.strftime(passedDateObj, "%m/%d/%y")
    
    
    log.info("\n")
    
    suggestReqNumber = sqlite.selectEnds('requests', conn)[0] + 1
    log.info(f"We suggest this new requesition to be {suggestReqNumber}. Please press enter when asked if this is correct.")
    reqNum = input("$: What number requisition is this?: ")
    if reqNum == "":
        reqNum = str(suggestReqNumber)
    
    
    contactName = input("$: Who's the Project Lead?: ")
    contactEmail = input("$: What's their email?: ")
    
    
        
    data = {"dateReq" : dateReq, "datePass" : datePass, "dateStart" : dateStart, "dateEnd" : dateEnd, 
            "name" : name, "recipient" : recipient, "categoryNo" : categoryNo, "amount" : amount,
            "minutesId" : minutesId, "reqNum" : reqNum, "contactName":contactName, "contactEmail" : contactEmail}
    
    return data

def sheetData(data):
    
    if data["categoryNo"] == "1":
        category = "🎩 AS"
    elif data["categoryNo"] == "2":
        category = "🌕 External"
    elif data["categoryNo"] == "3":
        category = "🪁 Internal"
    elif data["categoryNo"] == "4":
        category = "🎓 UCSB"
        
    data = {
        "range" : "💵 Transactions!B:B",
        "majorDimension" : "ROWS",
        "values" : [[data["dateReq"], data["datePass"], data["dateStart"], data["dateEnd"], data["name"], data["recipient"], category, "-" + data["amount"]]]
    }
    
    return data

def getSchoolYear():
    year = datetime.date.today().year
    month = datetime.date.today().month
    if(month < 7 == 0):
        schoolYear = str(year-1)[2:] + "-" + str(year)[2:]
    else:
        schoolYear = str(year)[2:] + "-" + str(year+1)[2:]    
    
    return schoolYear

def replaceHTMLTemplate(origFile, seearchStr, replaceStr, htmlFile):

    if (origFile != htmlFile):
        shutil.copy(origFile, htmlFile)
    
    file = open(htmlFile, "r")
    replacement = ""
    for line in file:
        line = line.strip()
        changes = line.replace(seearchStr, replaceStr)
        replacement = replacement + changes + "\n"
        
    file.close()
    fout = open(htmlFile, "w")
    fout.write(replacement)
    fout.close()
   
def deniedInfoInput():
    contactName = input("$: Contact name: ")
    projectName = input("$: Project: ")
    reasons = input("$: Rejection Reasons: ")
    alternates = input("$: Alternative Sources: ")
    email = input("$: Contact's email: ")
    
    data = {"contactName" : contactName, "projectName" : projectName, "reasons" : reasons, "alternates" : alternates,
            "email" : email}
    return data 
   
#? Take an input of a date %m/%d/%y and a number away from it and returns the new date in same format
def daysFromDay(origDay, numOfDays):
    
    dateFormat = "%m/%d/%y"
    dtObj = dt.strptime(origDay, dateFormat)
    newDate = dtObj + timedelta(days=numOfDays)
    
    return newDate.strftime(dateFormat)

#? Takes in an input of string with '' and returns a json dict
def jsonFromSingleQuoteStr(s):
    string = s.split("'")
    stringDB = '"'.join(string)
    data = js.loads(stringDB)
    return data

def dataDBGet(conn):
    log.info("Here are some recent funding requests:")
    data = sqlite.selectAll('requests', conn, ' ORDER BY reqNo DESC')
    for index, reqData in enumerate(data):
        if index > 5:
                break
        dataStr = str(reqData[5])
        data = jsonFromSingleQuoteStr(dataStr)
        log.info(f"{reqData[0]} : {data['name']}\n")
    reqN = input("$: Which funding request number are you looking for?: ")
    log.debug("Finding funding request " + reqN + "...")
    dataRAWList = sqlite.findItem("reqNo", reqN, "data", "requests", conn)
    if(len(dataRAWList) != 1):
        log.critical("SOMETHING WENT HORRIBLY WRONG. WE FOUND MORE THAN ONE ROW MATCHING THIS NUMBER!!! STOPPPPPPPP...")
        return 1
    dataStr = str(dataRAWList[0])[2:-3]
    log.debug("Found! Retrieving data...")
    data = jsonFromSingleQuoteStr(dataStr)
    log.info("Requesition for: " + data["name"])
    log.info("Done.")
    
    
    return reqN, data