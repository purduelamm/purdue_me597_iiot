import datetime
import time
import random
import pymysql.cursors

## Credential
HOST = 'mepotrb16.ecn.purdue.edu' # MySQL server host DNS
PORT = 3306 # MySQL server port number
USER = 'yourname' # MySQL account name
PASSWORD = 'password' # Password of the account
DB = 'ME597Spring24' # DB name
TABLE = 'yourname_lab6' # table name
## Credential

sensor = 'sensor3' # sensor name
measurement1 = 'acceleration1' # measurement name 1
measurement2 = 'acceleration2' # measurement name 2
measurement3 = 'acceleration3' # measurement name 3

connection = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, port=PORT) # make a connection to MySQL server
cursor = connection.cursor() # Open cursur to execute SQL query

duration = 60 # collection time in second unit
start_time = time.time() # get current time

while time.time() - start_time < duration:
    value1 = str(random.uniform(0,2)) # random value for measurement1
    value2 = str(random.uniform(-2,0)) # random value for measurement2
    value3 = str(random.uniform(9.7,9.9)) # random value for measurement3
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # get datetime as MySQL timestamp format
    
    print(timestamp)
    print("{}={}".format(measurement1,value1)) # value1
    print("{}={}".format(measurement2,value2)) # value2
    print("{}={}".format(measurement3,value3)) # value2
    
    query1 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor+"','"+measurement1+"','"+value1+"');" #SQL query1 for value1
    query2 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor+"','"+measurement2+"','"+value2+"');" #SQL query2 for value2
    query3 = "INSERT INTO "+TABLE+" (timestamp,sensor,measurement,value) VALUE('"+timestamp+"','"+sensor+"','"+measurement3+"','"+value3+"');" #SQL query3 for value3
    
    cursor.execute(query1) # execute query 1
    cursor.execute(query2) # execute query 2
    cursor.execute(query3) # execute query 3
    connection.commit() # commit all SQL queries
    
    print("==INSERT QUERIES DONE==\n")
    
    time.sleep(3) # wait for 3 seconds

connection.close() # gently close connection
print("==Program DONE==")
