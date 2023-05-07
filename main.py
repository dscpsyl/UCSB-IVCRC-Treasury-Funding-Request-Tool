from utils import auth
from utils import sheets
from utils import dataGet
from utils import drive
from utils import wordDocx
from utils import gmail
from utils import slack
from utils import sqlite
from utils import pdf

import os
import sys
import json as js
from datetime import datetime as dt

import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

#? Create a new funding request entry and initial processing
def newEntry(settings, slackClient, creds, conn):
    l.info("##########~[New Funding Request Entry]~########## \n")
    
    #? Getting user required information
    l.info("We currently need some information to continue. Getting info...")
    data = dataGet.initInput(settings, creds, conn)
    l.info("Done.\n")
    
    #? Get's School Year to append to file names
    l.debug("Getting School year..")
    schoolYear = dataGet.getSchoolYear()
    l.debug("School year: " + schoolYear)
    l.debug("Done.\n")
    
    #? Getting 'Expenditures' sheet and adding a new row of information
    l.info("Adding new entry to expense sheet...")
    sheetData = dataGet.sheetData(data)
    sheets.sheetsAppend(settings["expendWkbkId"], sheetData, "OVERWRITE", settings["EXPENDATURE_WORKBOOK_GOOGLESHEET_ID"], creds)
    l.info("Done.\n")
    
    #? Download meeting minutes, highligh passed part, and upload it
    l.debug("Downloading meeting minutes...")
    downM = drive.driveEXPORT(data["minutesId"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document", creds)
    with open("env/tempMinutes.docx", "wb") as f:
        f.write(downM)
        
    l.debug("Making minutes file name...")
    mnFileName = schoolYear + " IVCRC F" + data["reqNum"] + " MN " + data["name"] + " ("  + data["recipient"] + ")"
    
    l.debug("Highlighting passed part...")
    check = wordDocx.highlightPar("env/tempMinutes.docx",data["name"], "tempMinutes")
    
    l.debug("Uploading it to Drive...")
    mnFileId = drive.driveUP("env/tempMinutes.docx", settings["reqIncompleteDriveFolderId"], mnFileName, creds)
    
    if not check:
        l.warning("!!Could not find passed part in minutes. Please manually highlight it and upload it to Drive.")
        l.warning("https://docs.google.com/document/d/" + mnFileId + "/edit")
        input("$: Press any key to continue...")
    
    l.debug("Done.\n")
    
    #? Writting the correct version of the follow up report and saving it and uploading it and get the id
    l.debug("Writting Followup Report...")
    wordDocx.replaceTextPar("res/FReport.docx", "[meetDate]", data["datePass"], "FRTemp")
    wordDocx.replaceTextPar("env/FRTemp.docx", "[projectSignatory]", data["contactName"], "FRTemp")
    wordDocx.replaceTextPar("env/FRTemp.docx", "[projectName]", data["name"], "FRTemp")
    wordDocx.replaceTextTable("env/FRTemp.docx", "[projectName]", data["name"], "FRTemp")
    wordDocx.replaceTextTable("env/FRTemp.docx", "[projEndDate]", data["dateEnd"], "FRTemp")
    wordDocx.replaceTextTable("env/FRTemp.docx", "[organization]", data["recipient"], "FRTemp")
    wordDocx.replaceTextTable("env/FRTemp.docx", "[frEndDate]", dataGet.daysFromDay(data["dateEnd"], 7), "FRTemp")
    
    l.debug("Copying it to Drive...")
    frFileName = schoolYear + " IVCRC F" + data["reqNum"] + " FR " + data["name"] + " ("  + data["recipient"] + ")"
    frFileId = drive.driveUP("env/FRTemp.docx", settings["reqIncompleteDriveFolderId"], frFileName, creds)
    
    l.debug("Removing it from local machine...")
    os.remove("env/FRTemp.docx")
    l.debug("Done.\n")
    
    comments = input("$: Please enter the comments by the board including line item specifications: ")
    
    #? Writting the correct version of the funding agreement and connecting the follow up report to it and then uploading it
    l.debug("Writting Funding Agreement Doc...")
    wordDocx.replaceTextPar("res/FAgreement.docx", "[meetDate]", data["datePass"], "FATemp")
    wordDocx.replaceTextPar("env/FATemp.docx", "[projectSignatory]", data["contactName"], "FATemp")
    wordDocx.replaceTextPar("env/FATemp.docx", "[boardComments]", comments, "FATemp")
    wordDocx.replaceTextTable("env/FATemp.docx", "[projectName]", data["name"], "FATemp")
    wordDocx.replaceTextTable("env/FATemp.docx", "[amount]", "$" + data["amount"], "FATemp")
    wordDocx.replaceTextTable("env/FATemp.docx", "[startDate]", data["dateStart"], "FATemp")
    wordDocx.replaceTextTable("env/FATemp.docx", "[frEndDate]", dataGet.daysFromDay(data["dateEnd"], 7), "FATemp")
    
    #? Adding Followup Report Link to Funding Agreement
    wordDocx.theMostNicheFunctionBecauseIDontWantMainToLookTooUgly("env/FATemp.docx", frFileId, "FATemp")
    
    l.debug("Copying it to Drive...")
    faFileName = "21-22 IVCRC F" + data["reqNum"] + " FA " + data["name"] + " ("  + data["recipient"] + ")"
    faFileId = drive.driveUP("env/FATemp.docx", settings["reqIncompleteDriveFolderId"], faFileName, creds)

    l.debug("Removing it from local machine...")
    os.remove("env/FATemp.docx")
    l.debug("Done.\n")
    
    #? Creates Accepted Email Template
    l.debug("Drafting Acceptance email...")
    dataGet.replaceHTMLTemplate("res/Accepted.html", "[recipientName]", data["contactName"], "env/AccTemp.html")
    dataGet.replaceHTMLTemplate("env/AccTemp.html", "[fundedAmount]", data["amount"], "env/AccTemp.html")
    dataGet.replaceHTMLTemplate("env/AccTemp.html", "[organizaitonRequested]", data["recipient"], "env/AccTemp.html")
    dataGet.replaceHTMLTemplate("env/AccTemp.html", "[projectName]", data["name"], "env/AccTemp.html")
    dataGet.replaceHTMLTemplate("env/AccTemp.html", "[refLink]", "https://docs.google.com/document/d/" + faFileId + "/edit", "env/AccTemp.html")
    dataGet.replaceHTMLTemplate("env/AccTemp.html", "[treasurerName]", settings["treasurerName"], "env/AccTemp.html")
    
    l.info("Creating acceptance draft email...")
    acceptedMessageBody = gmail.createEmailBody("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", data["contactEmail"], data["name"] + " : IVCRC Funding Request Approved!", "env/AccTemp.html")
    acceptedDraftId = gmail.createDraft("me", acceptedMessageBody, creds)
    l.debug("Done.\n")
    
    l.info("Please review the drafted email manually and make any changes necessary...")
    emailDecision = input("$: Would you like to send the email? (Y/n): ")
    if(emailDecision == "Y"):
        l.info("Sending email...")
        gmail.sendDraft("me", acceptedDraftId, creds)
        l.info("Done.\n")
    else:
        l.info("Email not sent. The draft is still in your inbox to be dealt with...")
    
    l.info("\n")
    
    l.debug("Removing email from local machine...")
    os.remove("env/AccTemp.html")
    l.debug("Done.\n")
    
    #? Share the funding agreement and follow up report with the recipient
    l.debug("Sharing the funding agreement and follow up report with the recipient...")
    drive.shareFile(frFileId, data["contactEmail"], "user", "reader", creds)
    drive.shareFile(faFileId, data["contactEmail"], "user", "reader", creds)
    l.debug("Done.\n")
    
    #? Posting Slack message about the new funding request
    l.debug("Creating slack message for finance channel...")
    initialSlackMsg = "Funding Request\n No: " + data["reqNum"] + "\n Name: " + data["name"] + "\n Recipient: " + data["recipient"] + "\n Amount: $" + data["amount"]
    l.info("Sending initial slack message...")
    slackThread = slack.sendTxtMsg(initialSlackMsg, settings["SLACK_TREASURER_CHANNEL_ID"], slackClient)
    l.info("Sending email confirmation message in thread...")
    confirmEmailMsg = "Confirmation Email has been sent at: " + dt.now().strftime("%m/%d %H:%M")
    slack.replyinThread(confirmEmailMsg, slackThread, settings["SLACK_TREASURER_CHANNEL_ID"], slackClient)
    l.debug("Pinning message...")
    slack.addPin(slackThread, settings["SLACK_TREASURER_CHANNEL_ID"], slackClient)
    l.info("Done.\n")
    
    l.debug("///Summary of data:///")
    l.debug("Req No: " + data["reqNum"])
    l.debug("Min: " + mnFileId)
    l.debug("Fa: " + faFileId)
    l.debug("Fr: " + frFileId)
    l.debug("Slack Thread: " + slackThread)
    l.debug("Data: " + str(data))
    l.debug("\n")
    
    #? Storing data into database
    l.info("Storing information into database...")
    tableP = "requests(reqNo, mnId, faId, frId, SlackTs, data)"
    values = "VALUES(?,?,?,?,?,?)"
    dbData = (data["reqNum"], mnFileId, faFileId, frFileId, slackThread, str(data))
    sqlite.addRow(dbData, tableP, values, conn)
    l.info("Done.\n")
    l.warning("THE BUDGET SHEET IS NOT TRACKED CURRENTLY AND WILL HAVE TO BE MANUALLY ADDED LATER!")
    l.info("\n")
    
    l.info("########################################")

#? Helps combine and upload a completed funding requests for signatures
def requisitionPre(settings, slackClient, creds, conn):
    l.info("##########~[Requesition and Publicity]~########## \n")
    #?Get data from DB
    reqN, data = dataGet.dataDBGet(conn)
    
    #? Get file ID's from DB
    mnID = sqlite.findItem("reqNo", reqN, "mnId", "requests", conn)
    mnID = mnID[0][0]
    
    faID = sqlite.findItem("reqNo", reqN, "faId", "requests", conn)
    faID = faID[0][0]
    
    frID = sqlite.findItem("reqNo", reqN, "frId", "requests", conn)
    frID = frID[0][0]
    
    #? Get Signed Funding Agreement from requestor 
    signedFundingFa = input("$: Please show me where the funding agreement is (pdf): ")
    signedFundingFa = signedFundingFa[1:-1]
    
    #? Get the budget pdf from user
    budgetPdf = input("$: Please show me where the budget is (pdf): ")
    budgetPdf = budgetPdf[1:-1]
    
    #? Get meeting minutes 
    l.info("Getting meeting minutes from database...")
    meetingIdRAW = sqlite.findItem("reqNo", reqN, "mnId", "requests", conn)
    if(len(meetingIdRAW) != 1):
        l.critical("SOMETHING BAD HAS HAPPENED TO FINDING THE RIGHT MEETING MINUTES ID. ABORTING!!!")
        sys.exit(1)
    l.info("Found in database. Retrieving from Google Drive...")
    meetingId = str(meetingIdRAW[0])[2:-3]
    meetingPdf = drive.driveEXPORT(meetingId, "application/pdf", creds)
    l.debug("Done.\n")
    l.debug("Writting to local disk...")
    with open("env/MeetingMinutes.pdf", "wb") as f:
        f.write(meetingPdf)
    l.info("Done.\n")
    meetingPdfLoc = "env/MeetingMinutes.pdf"
    
    #? Get requisition form filled
    l.debug("Getting requisition template...")
    l.info("Use the commandline to fill out most of the required information: ")
    templatePdf = ReqFormFiller(settings, data)
    l.info("Done.\n")
    
    #? Combine pdf files into one and put it onto the desktop and ask user to fill it out
    l.debug("Combining files into single and putting it on the desktop...")
    pdfList = [signedFundingFa, templatePdf, budgetPdf, meetingPdfLoc]
    pdfFile = pdf.pdfMerge(pdfList, os.path.expanduser('~') + "/Desktop")
    l.debug("Done.\n")
    l.info("Please edit the file and the requesition with the line items as needed on the desktop...")
    input("$: Press any key to continue when finished...")
    
    l.info("\n")
    
    #? Get slackts and upload it in thread with mgs asking people to sign
    l.info("Uploading file to slack...")
    slackTsRAW = sqlite.findItem("reqNo", reqN, "SlackTs", "requests", conn)
    slackTs = str(slackTsRAW)[2:-3]
    
    sTagsD = settings["slackTags"]
    sTagsD = sTagsD.split(",")
    sTags = ""
    for t in sTagsD:
        sTags += "<@" + t + ">"
    
    msg = sTags + " Could I please have our committee director and another authorized signer help complete this funding requests? Thanks!"
    fileId = slack.sendMsgWithAttachment(msg, pdfFile, dataGet.getSchoolYear() + " IVCRC F" + data["reqNum"] + " " + data["name"] + " ("  + data["recipient"] + ")", settings["SLACK_TREASURER_CHANNEL_ID"], slackClient, slackTs)
    l.info("Done.\n")
    
    #? Move Funding Agreement, Meeting Minutes, Followup Report to the archive folder
    l.info("Moving files to archive folder...")
    l.debug("Moving Funding Agreement...")
    drive.driveMV(faID, settings["archiveIncompleteDriveFolderId"], creds)
    l.debug("Moving Meeting Minutes...")
    drive.driveMV(mnID, settings["archiveIncompleteDriveFolderId"], creds)
    l.debug("Moving Followup Report...")
    drive.driveMV(frID, settings["archiveIncompleteDriveFolderId"], creds)    
    l.info("Done.\n")
    
    l.debug("Deleting it off of local computer...")
    os.remove(pdfFile)
    os.remove(templatePdf)
    os.remove(meetingPdfLoc)
    l.debug("Done.\n")
    
    # #? Send message to publicity
    # l.info("Sending slack message to publicity...")
    # pubMsg = "Hey guys! Please start making a promotional material for " + data["name"]
    # slack.sendTxtMsg(pubMsg, settings["SLACK_PUBLICITY_CHANNEL_ID"], slackClient)
    # l.info("Done.\n")
    
    # l.info("Sending slack message to history channel...")
    # #? Send message to history
    # histMsg = data["name"] + " by " + data["recipient"] + " on " + data["dateStart"] + ". Contact " + data["contactName"] + "(" + data["contactEmail"] + ") for more information."
    # slack.sendTxtMsg(histMsg, settings["SLACK_HISTORY_CHANNEL_ID"], slackClient)
    # l.info("Done.\n")
    
    
    l.info("\n")
    l.info("########################################")
    
#? Send requesition off for processing and notify requestee
def requisitionPost(settings, slackClient, creds, conn):
    l.info("##########~[Requisition Send]~########## \n")
    
    #?Get data from DB
    reqN, data = dataGet.dataDBGet(conn)
    
    #? Input file path for signed and completed funding request
    completedFundingRequestUrl = input("$: Please show me where the completed and compiled funding request is: ")
    completedFundingRequestUrl = completedFundingRequestUrl[1:-1]
    l.info("Thank you!")
    
    #? Create new Draft with attachment and body template & then send it
    l.info("Drafing requisition email for AS with attachment...")
    dataGet.replaceHTMLTemplate("res/Requisition.html", "[projectName]", data["name"], "env/ReqTemp.html")
    dataGet.replaceHTMLTemplate("env/ReqTemp.html", "[projectOrg]", data["recipient"], "env/ReqTemp.html")
    dataGet.replaceHTMLTemplate("env/ReqTemp.html", "[fundedAmount]", data["amount"], "env/ReqTemp.html")
    dataGet.replaceHTMLTemplate("env/ReqTemp.html", "[treasurerName]", settings["treasurerName"], "env/ReqTemp.html")
    
    reqMessageBody = gmail.createEmailBodyWithPdfAttachment("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", "ASTD Requisitions <requisitions@as.ucsb.edu>", "Payable to "+ data["recipient"] + " - $" + data["amount"], "env/ReqTemp.html", completedFundingRequestUrl)
    l.debug("Creating new draft in email...")
    reqDraftId = gmail.createDraft("me", reqMessageBody, creds)
    l.debug("Done.\n")
    l.info("Please review the drafted email manually and make any changes necessary...")
    emailDecision1 = input("$: Would you like to send the email? (Y/n): ")
    if(emailDecision1 == "Y"):
        l.info("Sending email...")
        gmail.sendDraft("me", reqDraftId, creds)
    else:
        l.info("Email not sent. The draft is still in your inbox to be dealt with...")    
    l.info("Done.\n")
    
    l.debug("Removing email from local machine...")
    os.remove("env/ReqTemp.html")
    l.debug("Done.\n")
    
    
    #? Notifies the Requestor that the requisition has been sent
    l.info("Drafting new email to notify requestor...")
    dataGet.replaceHTMLTemplate("res/Sent.html", "[leadName]", data["contactName"], "env/SentTemp.html")
    dataGet.replaceHTMLTemplate("env/SentTemp.html", "[treasurerName]", settings["treasurerName"], "env/SentTemp.html")
    
    sentMessageBody = gmail.createEmailBody("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", data["contactEmail"], "IVCRC Funding Payment Processed!", "env/SentTemp.html")
    l.debug("Creating new draft in email...")
    sentDraftId = gmail.createDraft("me", sentMessageBody, creds)
    l.debug("Done.\n")
    l.info("Please review the drafted email manually and make any changes necessary...")
    emailDecision2 = input("Would you like to send the email? (Y/n): ")
    if(emailDecision2 == "Y"):
        l.info("Sending email...")
        gmail.sendDraft("me", sentDraftId, creds)
    else:
        l.info("Email not sent. The draft is still in your inbox to be dealt with...")
    l.info("Done.\n")
    
    l.debug("Removing email from local machine...")
    os.remove("env/SentTemp.html")
    l.debug("Done.\n")
    
    l.warning("!PLEASE MAKE SURE TO MANUALLY SNOOZE THE EMAIL TO A MONTH LATER!")
    input("$: Press any key to continue...")
    l.info("\n")
    
    #? Send slack message update and unpin from channel
    l.debug("Getting slack thread...")
    slackTsRAW = sqlite.findItem("reqNo", reqN, "SlackTs", "requests", conn)
    slackTs = str(slackTsRAW[0])[2:-3]
    l.debug("Done.\n")
    l.info("Sending slack update...")
    msg = "Requisition and notification email sent " + dt.now().strftime("%m/%d %H:%M")
    slack.replyinThread(msg, slackTs, settings["SLACK_TREASURER_CHANNEL_ID"], slackClient)
    l.info("Done.\n")
    l.debug("Unpinning message...")
    slack.removePin(slackTs, settings["SLACK_TREASURER_CHANNEL_ID"], slackClient)
    l.debug("Done.\n")
    
    #? Upload file to drive
    l.info("Uploading Completed Agreement to drive...")
    completedAgreementID = drive.driveUP(completedFundingRequestUrl, settings["completedReqsDriveFolderId"], dataGet.getSchoolYear() + " IVCRC F" + data["reqNum"] + " " + data["name"] + " ("  + data["recipient"] + ")", creds)
    l.info("Done.\n")
    
    #? Link it in the spreadsheet
    l.debug("Linking file in spreadsheet...")
    sheetData = sheets.sheetsGet(settings["expendWkbkId"], settings["EXPENDATURE_WORKBOOK_GOOGLESHEET_NAME"], creds)
    rows = sheetData["values"]
    for r in rows:
        if data["name"] == r[0]:
            _dTxt = r[0]
            r[0] = '=HYPERLINK("https://drive.google.com/file/d/' + completedAgreementID + '", "' + _dTxt +'")'
            break
    sheetData["values"] = rows
    sheets.sheetUpdate(settings["expendWkbkId"], sheetData, sheetData["range"], creds)
    l.debug("Done.\n")
            
    l.info("\n")
    l.info("########################################")
    
    return 0

#? Check's in with Funding Requestor if payment has been recieved
def paymentCheckIn(settings, creds, conn):
    l.info("##########~[Payment Check-In]~########## \n")
    
    #?Get data from DB
    reqN, data = dataGet.dataDBGet(conn)
    
    
    #?send email of payment checkin 
    l.debug("Creating new draft in email...")
    dataGet.replaceHTMLTemplate('res/paymentCheckin.html', "[leadName]", data["contactName"], 'env/checkin.html')
    dataGet.replaceHTMLTemplate('env/checkin.html', "[treasurerName]", settings["treasurerName"], 'env/checkin.html')
    checkinMsg = gmail.createEmailBody("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", data["contactEmail"], "IVCRC Payment Recipient CheckIn", 'env/checkin.html')
    draft = gmail.createDraft("me", checkinMsg, creds)
    l.debug("Done.\n")
    l.info("Please review the drafted email manually and make any changes necessary...")
    emailDecision3 = input("$: Would you like to send the email? (Y/n): ")
    if(emailDecision3 == "Y"):
        l.info("Sending email...")
        gmail.sendDraft("me", draft, creds)
    else:
        l.info("Email not sent. The draft is still in your inbox to be dealt with...")
    l.info("Done.\n")
        
    #?Remove template 
    l.debug("Removing email from local machine...")
    os.remove("env/checkin.html")
    l.debug("Done.\n")
    
    
    l.info("\n")
    l.info("########################################")

#? Handles the Follow Up Report Conditions
def followUpReport(settings, creds, conn):
    l.info("##########~[FollowUp Report Check-In]~########## \n")
    
    #?Get data from DB
    reqN, data = dataGet.dataDBGet(conn)
    
    submitted = input("$: Has the requestor submitted their followup report?(Y/n): ")

    if(submitted == "n"):
        #? Send email asking if they have submitted their report or if they need an extension   
        l.info("Creating checkin email...") 
        dataGet.replaceHTMLTemplate('res/frCheckin.html', "[leadName]", data["contactName"], 'env/frCheckin.html')
        dataGet.replaceHTMLTemplate('env/frCheckin.html', "[treasurerName]", settings["treasurerName"], 'env/frCheckin.html')
        frCheckEmail = gmail.createEmailBody("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", data["contactEmail"], "IVCRC Follow Up Report CheckIn", 'env/frCheckin.html')
        draft = gmail.createDraft("me", frCheckEmail, creds)
        l.debug("Done.\n")
        l.info("Please review the drafted email manually and make any changes necessary...")
        emailDecision4 = input("$: Would you like to send the email? (Y/n): ")
        if(emailDecision4 == "Y"):
            l.info("Sending email...")
            gmail.sendDraft("me", draft, creds)
        else:
            l.info("Email not sent. The draft is still in your inbox to be dealt with...")
        
        l.info("Done.\n")
        
        l.debug("Removing email from local machine...")
        os.remove('env/frCheckin.html')
        l.debug("Done.\n")
    else:
        #? Send Thank you email
        l.info("Creating thank you email...")
        dataGet.replaceHTMLTemplate('res/thankYou.html', "[leadName]", data["contactName"], 'env/thankYou.html')
        dataGet.replaceHTMLTemplate('env/thankYou.html', "[treasurerName]", settings["treasurerName"], 'env/thankYou.html')
        tYEmail = gmail.createEmailBody("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", data["contactEmail"], "Thank you for Working with IVCRC!", 'env/thankYou.html')
        draft = gmail.createDraft("me", tYEmail, creds)
        l.debug("Done.\n")
        l.info("Please review the drafted email manually and make any changes necessary...")
        emailDecision4 = input("$: Would you like to send the email? (Y/n): ")
        if(emailDecision4 == "Y"):
            l.info("Sending email...")
            gmail.sendDraft("me", draft, creds)
        else:
            l.info("Email not sent. The draft is still in your inbox to be dealt with...")
            
        l.info("Done.\n")
        
        l.debug("Removing email from local machine...")
        os.remove('env/thankYou.html')
        l.debug("Done.\n")
    
        #? Find where the FR is and upload to completed folder
        completedFRUrl = input("$: Please show me where the completed and compiled follow-up report is: ")
        completedFRUrl = completedFRUrl[1:-1]
        
        l.debug("Renaming file...")
        schoolYear = dataGet.getSchoolYear()
        frPDFFileName = schoolYear + " IVCRC F" + data["reqNum"] + " FR " + data["name"] + " ("  + data["recipient"] + ")"
        
        l.info("Uploading to Drive...")
        drive.driveUP(completedFRUrl, settings["completedReqsDriveFolderId"], frPDFFileName, creds)
        l.info("Done.\n")
        
        #? Remove from DB
        removeDB =input("$: This funding request will now be removed from the database?(Y/n)")
        if(removeDB == "Y"):
            sqlite.delRow("reqNo", "reqN", "requests", conn)
            
        l.info("Done.\n")
    
    l.info("\n")
    l.info("########################################")
    
    return 0

#? Handles the Funding Extension Conditions
def extension(settings, creds, conn):
    l.info("##########~[Funding Extension]~########## \n")
    #! step 14
    
    #? Fill out funding extension form and upload to imcomplete folder 
    
    #? Create email and link form to be signed
    l.critical("This feature is not yet implemented. Please use the manual method for now.\n")
    return 0

#? Drafts and sends emails informing denied funding request
def denied(settings, creds):
    l.info("##########~[Application Denial]~########## \n")
    
    l.info("Getting Required Information...")
    data = dataGet.deniedInfoInput()
    l.info("Thank you!...")
    l.info("\n")
    l.debug("Inputting information into rejection template...")
    dataGet.replaceHTMLTemplate("res/Rejection.html", "[contactName]", data["contactName"], "env/RejTemp.html")
    dataGet.replaceHTMLTemplate("env/RejTemp.html", "[projectName]", data["projectName"], "env/RejTemp.html")
    dataGet.replaceHTMLTemplate("env/RejTemp.html", "[decisionNotes]", data["reasons"], "env/RejTemp.html")
    dataGet.replaceHTMLTemplate("env/RejTemp.html", "[altsSources]", data["alternates"], "env/RejTemp.html")
    dataGet.replaceHTMLTemplate("env/RejTemp.html", "[treasurerName]", settings["treasurerName"], "env/RejTemp.html")
    l.debug("Done!...")
    l.info("\n")
    l.debug("Creating email body...")
    rejectionMessageBody = gmail.createEmailBody("IVCRC Treasurer <as-ivcrc.treasurer@ucsb.edu>", data["email"], "IVCRC Funding Request Update", "env/RejTemp.html")
    l.debug("Done!...")
    l.info("Creating draft in gmail account...")
    rejectionDraftId = gmail.createDraft("me", rejectionMessageBody, creds)
    l.debug("Done!...")
    confirmSend = input("$: Please review email before sending and edit anything you need. Send? (y/N): ")
    if(confirmSend == "y"):
        l.info("Sending email...")
        gmail.sendDraft("me", rejectionDraftId, creds)
    else:
        l.info("Aborting send...")

    l.info("Done!\n")    

    l.debug("Removing local copy of template...")
    os.remove("env/RejTemp.html")    
    l.debug("Done!\n")
    l.info("########################################")

#? Creates a filled out requesition form and saves it to a specific location (Does not fill out description)
def ReqFormFiller(settings, dataSet=None, cmdLine=False):
    #? Sanity check to see if we have the required @params for the function called
    if not cmdLine:
        l.debug("##########~[Requisition Filler]~########## \n")
        if type(dataSet) != dict:
            raise Exception("No data set dict was passed to the function when it was called!")
    else:
        l.info("##########~[Requisition Filler]~########## \n")
    
    fields = {}    
    #? Get the type of requisition
    # Button types are /Off or /Yes
    _type = input("$: What type of requisition is this? [0: Checks, 1: Journal Entries, 2: PO]: ")
    if _type == "0":
        fields["check"] = "/Yes"
    elif _type == "1":
        fields["je"] = "/Yes"
    elif _type == "2":
        fields["po"] = "/Yes"
        _poType = input("$: What type of PO is this? [0: Paper, 1: Paperless]: ")
        if _poType == "0":
            fields["p"] = "/Yes"
        elif _poType == "1":
            fields["pl"] = "/Yes"
        else:
            raise Exception("Invalid PO type!")
    else:
        raise Exception("Invalid requisition type!")
    
    fields["dateRequested"] = str(dt.now().strftime("%m/%d/%Y"))
    fields["payableTo"] = input("$: Who is this payable to?: ")
    fields["streetAddress"] = input("$: What is the street address?: ")
    fields["cSZip"] = input("$: What is the city, state, and zip code?: ")
    fields["phone"] = input("$: What is the phone number?: ")
    if cmdLine:
        fields["eventName"] = input("$: What is the name of the event?: ")
        fields["eventDate"] = input("$: What is the date of the event?: ")
        fields["meetingDate"] = input("$: What is the date of the meeting that this funding passed?: ")
    else:
        fields["eventName"] = dataSet["name"]
        fields["eventDate"] = dataSet["dateStart"]
        fields["meetingDate"] = dataSet["datePass"]
    fields["subtotal"] = input("$: What is the subtotal?: ")
    if fields["subtotal"] == "":
        fields["subtotal"] = 0
    fields["tax"] = input("$: What is the tax?: ")
    if fields["tax"] == "":
        fields["tax"] = 0
    fields["SandH"] = input("$: What is the shipping and handling?: ")
    if fields["SandH"] == "":
        fields["SandH"] = 0
    
    fields["total"] = str(round(float(fields["subtotal"]) + float(fields["tax"]) +float(fields["SandH"]), 2))
    if input("$: Is the treasurer signing this requesition? (Y/n): ") == "Y":
        fields["asName1"] = settings["treasurerName"]
        fields["asPhone1"] = settings["treasurerPhone"]
        fields["asEmail1"] = settings["treasurerEmail"]
        fields["asDate1"] = str(dt.now().strftime("%m/%d/%Y"))
    
    
    savedLoc = pdf.pdfFormFiller("res/RequisitionTemplate.pdf", "env", fields)
    
    #? If we're running this from the comdline, add the other parts to the requesition and save it to the desktop
    if cmdLine:
        recieptLoc = input("$: Please show me where the reciept pdf is: ")[1:-1]
        meetingLoc = input("$: Please show me where the meeting minutes pdf is: ")[1:-1]
        pdf.pdfMerge([savedLoc, recieptLoc, meetingLoc], os.path.expanduser('~') + "/Desktop")
        os.remove(savedLoc)
        l.info("Done. \n The requesition has been saved to the desktop.")

    return savedLoc

#? Prints out all the data in the database with only the revelant information
def viewAllDB(conn):
    l.info("##########~[Viewing Database]~########## \n")
    data = sqlite.getAllData(conn)
    l.info(data)
    l.info("########################################")
    
#? Dev option to add a test row to the database
def addTestDataRow(conn):
    l.info("##########~[DEV: Adding Test Row :DEV]~########## \n")
    confirm = input("$: Are you sure you want to add a test row? (y/n): ")
    if confirm.upper() == 'N':
        l.info("Aborting...")
        sys.exit(0)
    
    data = {"dateReq" : "4/26", "datePass" : "4/26", "dateStart" : "5/13", "dateEnd" : "5/13", 
             "name" : "Mega Shabbat", "recipient" : "CHABAD AT UCSB", "categoryNo" : "4", "amount" : "8000",
             "minutesId" : "1RDl_j5J82vKGhnkQtSKkbIgYXfakK2JPQ1qiU7Uu7Vo", "reqNum" : "21", "contactName":"Aya Zeplovitch", "contactEmail" : "miriloschak@gmail.com"}
    sData = ("69","TestinNmId", "TestingFaID", "TestingFriD", "TestingSlackTs", str(data))
    sqlite.addRow(sData, "requests(reqNo, mnId, faId, frId, SlackTs, data)", "VALUES(?,?,?,?,?,?)", conn)
    
    l.info("Added test data to request number 69...")
    l.info("Done.")
    l.info("########################################")

#? Prints out a single entry with all the information
def viewSingleRequest(conn):
    l.info("##########~[Viewing Single Request]~########## \n")
    no = input("$: What is the request number?: ")
    data1, data2 = sqlite.viewRow(conn, no)
    l.info("########################################")
    l.info(data1)
    l.info("########################################")
    l.info(data2)
    l.info("########################################")

#? Deletes a single request from DB with the request number
def deleteRequestMain(conn):
    l.info("##########~[Deleting Single Request]~########## \n")
    no = input("$: What is the request number?: ")
    requestDataRAW = []
    requestInfo = sqlite.selectRow("reqNo", no, "requests", conn)
    for r in requestInfo:
       r = list(r)
       data = dataGet.jsonFromSingleQuoteStr(r[-1])
       requestDataRAW.append(data)

    if len(requestDataRAW) != 1:
        l.critical("!!!!!SOMETHING HAS GONE WRONG WITH SELECTING A SINGLE ROW FROM DATABASE::deleteRequestMain()")
        sys.exit(1)
    
    confirm1 = input(f"$: Are you sure you want to delete {requestDataRAW[0]['name']} by {requestDataRAW[0]['recipient']}? (y/n): ")
    if confirm1.upper() == 'N':
        print("Aborting...")
        sys.exit(0)
        
    confirm2 = input(f"$: Are you REALLY sure? This action can't be undone and all related data will be gone!! (Y/n): ")
    if not confirm2 == 'Y':
        print("Aborting...")
        sys.exit(0)

    l.info(f"Deleting {requestDataRAW[0]['name']} by {requestDataRAW[0]['recipient']}...")
    sqlite.delRow("reqNo", no, "requests", conn)
    l.info("Done.\n")
    l.info("########################################")
    
#? Updates the data field of a singe runding request
def updateData(conn):
    l.info("##########~[Update Request Data]~########## \n")
    
    _dictNumToField = {"0": "Date Requested", "1": "Date Passed", "2": "Date Start", "3": "Date End", "4":"Event Name", "5":"Recipient", "6": "Amount", "7": "Contact Name", "8": "Contact Email"}
    _dictKeys = ["dateReq", "datePass", "dateStart", "dateEnd", "name", "recipient",  "amount", "contactName", "contactEmail"]
    
    no = input("$: Which funding request would you like to update?: ")
    requestDataRAW = []
   
    sqlData = sqlite.selectRow("reqNo", no, "requests", conn)
   
    for r in sqlData:
       r = list(r)
       data = dataGet.jsonFromSingleQuoteStr(r[-1])
       requestDataRAW.append(data)

    if len(requestDataRAW) != 1:
        l.critical("!!!!!SOMETHING HAS GONE WRONG WITH SELECTING A SINGLE ROW FROM DATABASE::updateData()")
        sys.exit(1)
    
    l.info("########################################")

    continueChoosing = True
    while continueChoosing:
        l.info("\n")
        l.info("What field would you like to update?")
        for x in _dictNumToField:
            l.info(x, "-", _dictNumToField[x], ":",data[_dictKeys[int(x)]])
        l.info("\n")
        
        updateNo = input("\n$: ")
        newData = input(f"$: What would you like to change the {_dictNumToField[updateNo]} to?: ")
        data[_dictKeys[int(updateNo)]] = newData
        
        continueIn = input("$: Would you like to change something else? (y/n): ")
        if continueIn.upper() == "N":
            continueChoosing = False
    
    l.info("Updating Database with new data...")
    sqlite.updateItem("reqNo", no, "data", str(data), "requests", conn)
    l.info("Done.\n")
    l.info("########################################")
    
    
#? Options for a new entry
def newEntryMainMenu(settings, slackClient, creds, conn):
    l.info("\n\n")
    l.info("What would you like to do? Choose a no:")
    l.info("""[1]New Entry
[2]Denied""")
    
    _option = input("$: ")
    
    if _option == "1":
        newEntry(settings, slackClient, creds, conn)
    elif _option == "2":
        denied(settings, creds)
    else:
        l.critical("INVALID OPTION. EXITING...")
        sys.exit(1)

#? Options for an existing entry
def existingEntryMainMenu(settings, slackClient, creds, conn):
    l.info("\n\n")
    l.info("What would you like to do? Choose a no:")
    l.info("""[1]Requisition Setup
[2]Send Requisition
[3]Payment Check-in
[4]Follow-up Report
[5]Follow-up Extension""")
    
    _option = input("$: ")
    
    if _option == "1":
        requisitionPre(settings, slackClient, creds, conn)
    elif _option == "2":
        requisitionPost(settings, slackClient, creds, conn)
    elif _option == "3":
        paymentCheckIn(settings, creds, conn)
    elif _option == "4":
        followUpReport(settings, creds, conn)
    elif _option == "5":
        extension(settings, creds, conn)
    else:
        l.critical("INVALID OPTION. EXITING...")
        sys.exit(1)

#? Options for database interactions
def dbMainMenu(settings, slackClient, creds, conn):
    l.info("\n\n")
    l.info("What would you like to do? Choose a no:")
    l.info("""[1]View All Requests
[2]View Single Request Details
[3]Delete Request
[4]Update Request""")
    
    _option = input("$: ")
    
    if _option == "1":
        viewAllDB(conn)
    elif _option == "2":
        viewSingleRequest(conn)
    elif _option == "3":
        deleteRequestMain(conn)
    elif _option == "4":
        updateData(conn)
    else:
        l.critical("INVALID OPTION. EXITING...")
        sys.exit(1)
    
#? Options for standalone utilities
def utilMainMenu(settings, slackClient, creds, conn):
    l.info("\n\n")
    l.info("What would you like to do? Choose a no:")
    l.info("""[1]Requisition Filler""")
    
    _option = input("$: ")
    
    if _option == "1":
        ReqFormFiller(cmdLine=True, settings=settings)
    else:
        l.critical("INVALID OPTION. EXITING...")
        sys.exit(1)
    
    
#After settings and db issues && user input checks: v1.0.0
def main():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://mail.google.com/", "https://www.googleapis.com/auth/drive"]
    
    l.debug("##########~Setting Up App~##########")
    
    #? Logging into database with table checks
    l.debug("Logging into database...")
    conn = sqlite.createConnection("env/fundingRequests.db")
    if(not sqlite.checkExist("table", "requests", conn)):
        newDBMaybe = input("NO EXISTING REQUESITION DB HAS BEEN FOUND. CREATE A NEW ONE? (Y/n)")
        if(newDBMaybe == 'Y'):
            tabelP = "requests(reqNo interger PRIMARY KEY, mnId text, faId text, frId text, SlackTs text, data text)"
            sqlite.createTable(tabelP, conn)
        else:
            print("Please create a requesition database or manually point to a database that fits the criteria.")
            sys.exit("ERROR: 42")
    l.debug("Done.\n")
    
    #?Logging in
    l.debug("Getting Google Auth Creds...")
    creds = auth.authToken(SCOPES)
    l.debug("Credentials Success...")
    
    #? Load in Settings 
    l.debug("Loading Settings...")
    with open("settings.json") as file:
        settings = js.load(file)
    l.debug("Done")
        
    #? Retrieve Slack Client
    l.debug("Starting Slack Client...")
    slackClient = auth.clientMake(settings)
    l.debug("Done \n \n")
    
    l.info("""                                                                                                                
                                                                                                                
                                                                                                                
 /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$
|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
       /$$   /$$  /$$$$$$   /$$$$$$  /$$$$$$$        /$$$$$$ /$$    /$$  /$$$$$$  /$$$$$$$   /$$$$$$            
      | $$  | $$ /$$__  $$ /$$__  $$| $$__  $$      |_  $$_/| $$   | $$ /$$__  $$| $$__  $$ /$$__  $$           
      | $$  | $$| $$  \__/| $$  \__/| $$  \ $$        | $$  | $$   | $$| $$  \__/| $$  \ $$| $$  \__/           
      | $$  | $$| $$      |  $$$$$$ | $$$$$$$         | $$  |  $$ / $$/| $$      | $$$$$$$/| $$                 
      | $$  | $$| $$       \____  $$| $$__  $$        | $$   \  $$ $$/ | $$      | $$__  $$| $$                 
      | $$  | $$| $$    $$ /$$  \ $$| $$  \ $$        | $$    \  $$$/  | $$    $$| $$  \ $$| $$    $$           
      |  $$$$$$/|  $$$$$$/|  $$$$$$/| $$$$$$$/       /$$$$$$   \  $/   |  $$$$$$/| $$  | $$|  $$$$$$/           
       \______/  \______/  \______/ |_______/       |______/    \_/     \______/ |__/  |__/ \______/            
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
 /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$ /$$$$$$
|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/|______/
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                
                                                                                                                \n\n\n""")
    
    l.info("What would you like to do? Choose a category:")
    l.info("""[1]New Funding Request
[2]Existing Funding Request
[3]Database
[4]Utils""")
    
    option = input("$: ")
    
    if option == "1":
        newEntryMainMenu(settings, slackClient, creds, conn)
    elif option == "2":
        existingEntryMainMenu(settings, slackClient, creds, conn)
    elif option == "3":
        dbMainMenu(settings, slackClient, creds, conn)
    elif option == "4":
        utilMainMenu(settings, slackClient, creds, conn)
    elif option == "420":
        addTestDataRow(conn)
    else:
        print("Input is not a valid option")
    