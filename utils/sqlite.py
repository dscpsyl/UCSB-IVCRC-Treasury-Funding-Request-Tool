import sqlite3
import sys
from sqlite3 import Error
import pandas as pd
from utils import dataGet

import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

#? @params is a path to a db file and returns the db connection
def createConnection(dbFile):
    conn = sqlite3.connect(dbFile)
    return conn

#? Checks if a type exists 
def checkExist(type, typeName, conn):
    c = conn.cursor()
    c.execute("SELECT count(name) FROM sqlite_master WHERE type=\'" + type + "\' AND name=\'" + typeName + "\'")

    return True if c.fetchone()[0] == 1 else False

#? Creates a table from the tableParams with format: tablename(params) as str
def createTable(tableParams, conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS " + tableParams + ";")

#? Takes in the data, tableParams and value placeholders with conn to add row
def addRow(data, tableParams, valueParams, conn):
    c = conn.cursor()
    
    sql = "INSERT INTO " + tableParams + " " + valueParams
    
    c.execute(sql, data)
    conn.commit()
    
#? @params to delete a row from search condition    
def delRow(searchField, searchValue, table, conn):
    sql = "DELETE FROM " + table + " WHERE " + searchField + "=?"
    cur = conn.cursor()
    cur.execute(sql, (searchValue,))
    conn.commit()
    
#? @params to return all rows as a list
def selectAll(table, conn, options=None):
    cur = conn.cursor()
    if not options:
        options = ""    
    cur.execute("SELECT * FROM " + table + options)
    rows = cur.fetchall()
    return rows

def selectEnds(table, conn, option=1):
    c = conn.cursor()
    if option == 0:
        sql = "SELECT *, MIN(reqNo) FROM requests"
    else:
        sql = "SELECT *, MAX(reqNo) FROM requests"
    data = c.execute(sql)
    r = data.fetchall()
    
    i=0
    for x in r:
        i+=1
    if i != 1:
        l.critical("!!!!!SOMETHING HAS GONE WRONG WITH SELECTING END FROM DATABASE")
        exit(1)
    
    return r[0]

#? @params to return a list of rows from search condition  
def selectRow(searchField, searchValue, table, conn):
    sql = "SELECT * FROM " + table + " WHERE " + searchField + "=?"
    cur = conn.cursor()
    cur.execute(sql, (searchValue,))
    rows = cur.fetchall()
    return rows

#? @params returns a list of items from search conditions and item requested
def findItem(searchField, searchValue, item, table, conn):
    sql = "SELECT " + item + " FROM " + table + " WHERE " + searchField + "=?"
    c = conn.cursor()
    c.execute(sql, (searchValue,))
    item = c.fetchall()
    return item

#? @params to return a pandas dataframe of all rows
def getAllData(conn):
    _columns = ["No", "Name", "Recipient", "Amount", "Contact Name", "Contact Email"]
    requests = []
    
    sqlData = selectAll("requests", conn)
    
    for r in sqlData:
        r = list(r)
        data = dataGet.jsonFromSingleQuoteStr(r[-1])
        requests.append([r[0], data["name"], data["recipient"], data["amount"], data["contactName"], data["contactEmail"]]) 
    
    _i = ["-" for i in range(len(requests))]
    d = pd.DataFrame(requests, columns=_columns).set_index(pd.Index(_i))
    
    return d
    
#? @params to return two pandas dataframe of a single row with all data
def viewRow(conn, requestNo):
   #reqNo, mnId, faId, frId, SlackTs, data
   # "name" : "Mega Shabbat", "recipient" : "CHABAD AT UCSB", "categoryNo" : "4", "amount" : "8000", "minutesId" : "1RDl_j5J82vKGhnkQtSKkbIgYXfakK2JPQ1qiU7Uu7Vo", "reqNum" : "21", "contactName":"Aya Zeplovitch", "contactEmail" : "miriloschak@gmail.com"
    _column1 = ["No", "Minutes Google ID", "Funding Agreement Google ID", "Followup Report GoogleID", "SlackTS ID"]
    _column2 = [ "Event Name", "Recipient", "Category No", "Amount", "Contact Name", "Contact Email"] 
    requests = []
    requestDataRAW = []
   
    sqlData = selectRow("reqNo", requestNo, "requests", conn)
   
    for r in sqlData:
       r = list(r)
       data = dataGet.jsonFromSingleQuoteStr(r[-1])
       requests.append(r[:-1])
       requestDataRAW.append(data)

    if len(requests) != 1 or len(requestDataRAW) != len(requests):
        l.critical("!!!!!SOMETHING HAS GONE WRONG WITH SELECTING A SINGLE ROW FROM DATABASE::sqlite.viewRow")
        sys.exit(1)
    
    requestData = [[requestDataRAW[0]["name"], requestDataRAW[0]["recipient"], requestDataRAW[0]["categoryNo"], requestDataRAW[0]["amount"], requestDataRAW[0]["contactName"], requestDataRAW[0]["contactEmail"]]]
    
    _i = ["-" for i in range(len(requests))]
    _j = ["-" for i in range(len(requestData))]
    
    rinfo = pd.DataFrame(requests, columns=_column1).set_index(pd.Index(_i))
    rDinfo = pd.DataFrame(requestData, columns=_column2).set_index(pd.Index(_j))
    
    return rinfo, rDinfo
       
#? @params to update a specific row of the db
def updateItem(searchField, searchValue, itemtoReplace, itemValue, table, conn):
    sql = "UPDATE " + table + " SET " + itemtoReplace + "=? " + " WHERE " + searchField + "=?"
    c = conn.cursor()
    c.execute(sql, (itemValue, searchValue))
    conn.commit()