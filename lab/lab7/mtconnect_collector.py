import time
import sys
import requests
import pymysql.cursors
from xml.etree import ElementTree as ET

## Credential
HOST = 'MySQL HOST DNS' # MySQL server host DNS
PORT = 3306 # MySQL server port number
USER = 'your account' # MySQL account name
PASSWORD = 'your password' # Password of the account
DB = 'Database information' # DB name
TABLE = 'your table name' # table name
## Credential

## MTConnect info.
agent = "agent host"
agent_port = "agent port number"
url_current = "http://"+agent+":"+agent_port+"/current"
MTCONNECT_STR = ET.fromstring(requests.get(url_current).content).tag.split("}")[0]+"}"
print("MTConnect string header is {}.".format(MTCONNECT_STR))
## MTConnect info.

url = 'http://'+agent+':'+agent_port+'/sample' # sample request to MTConnect agent
url_updated = url # repeating request, url_updated

## mysql connection
connection = pymysql.connect(host=HOST,user=USER,password=PASSWORD,db=DB,port=PORT) # mysql connection object
cursor = connection.cursor() # Open cursur to execute SQL Query
cursor.execute("SET time_zone='+00:00'") # Set time zone of the connected session as UTC
connection.commit() # commit time zone setting
print("== Successful database connecton! ==")
time.sleep(5) # while loop starts in 10 seconds
while True: # reapeating continuously, infinitely
    try:
        response = requests.get(url_updated) # XML response
        root = ET.fromstring(response.content) # Get root of XML response
        header = root.find("./"+MTCONNECT_STR+"Header") # get header of XML reponse
        header_attribs = header.attrib # get header attribute
        nextSeq = header_attribs["nextSequence"] # find next sequence for url update

        # Read data and INSERT to database by XML parsing from agent
        for device in root.iter(MTCONNECT_STR+'DeviceStream'):
            deviceName = device.get('name')
            for sample in device.iter(MTCONNECT_STR+'Samples'): # for Sample category
                for tags in sample:
                    tagName = tags.tag # get tag info
                    tagName = tagName[40:] # tagname
                    dataItemId = tags.get('dataItemId') # get dataitem id info
                    timestamp = tags.get('timestamp') # get timestamp info
                    timestamp_reformat = timestamp[0:10]+" "+timestamp[11:] # reformat timestmap according to MySQL
                    timestamp_mysql = timestamp_reformat.replace("Z","") # remove Z in timestamp
                    # print(timestamp, timestamp_mysql)
                    name = tags.get('name') # get name info
                    if name is None or name == " ": # in case name attribute is empty
                        name = "NULL"
                    sequence = tags.get('sequence') # get sequence info
                    value = tags.text # get value (text)
                    # insert data into MySQL table
                    query = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp_mysql+"','"+deviceName+"','"+name+"','"+value+"');"
                    cursor.execute(query) # execute the query
                    print(query)
                connection.commit() # commit all query

            for event in device.iter(MTCONNECT_STR+'Events'): # for Events category
                for tags in event:
                    tagName = tags.tag # get tag info
                    tagName = tagName[40:] # tagname
                    dataItemId = tags.get('dataItemId') # get dataitem id info
                    timestamp = tags.get('timestamp') # get timestamp info
                    timestamp_reformat = timestamp[0:10]+" "+timestamp[11:] # reformat timestmap according to MySQL
                    timestamp_mysql = timestamp_reformat.replace("Z","") # remove Z in timestamp
                    name = tags.get('name') # get name info
                    if name is None or name == " ": # in case name attribute is empty
                        name = "NULL"
                    sequence = tags.get('sequence') # get sequence info
                    value = tags.text # get value (text)
                    # insert data into MySQL table
                    query = "INSERT INTO "+TABLE+" (timestamp, sensor, measurement, value) VALUE('"+timestamp_mysql+"','"+deviceName+"','"+name+"','"+value+"');"
                    cursor.execute(query) # execute the query
                    print(query)
                connection.commit() # commit all query
            
        url_updated = url+'?from='+nextSeq # update url for the next sequence
        print('== Collection is DONE ==: Next sequence is', nextSeq,'\n')
        time.sleep(3) # 3 seconds time sleep.CHANGE THIS depneding on your system requirement

    except KeyboardInterrupt: # When interrupt the loop by keyboard (Ctrl + c)
        connection.rollback()
        connection.close()
        sys.exit()

    except Exception as e: # When any error happens
        connection.rollback()
        connection.close()
        print(e)
        raise e
