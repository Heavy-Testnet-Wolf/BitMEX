# Downloads the BitMEX trollbox history and saves it to a local sqlite database.
# Each time this script is run, it will update the local sqlite database.
#
# DATABASE STUCTURE:
# table: messages
#  id        integer     Unique id with 1 being the oldest entry in the database
#  id_bmex   integer     BitMEX message id (would have been identical to id if BitMEX never deleted any messages)
#  date      timestamp   Timestamp of the message
#  user      text        Username
#  message   text        Message in plain text
#  html      text        Message in HTML
#  fromBot   bool        True if message was posted via API (i think)
#  channelID integer     Channel number where 0=unknown,1=english,2=chinese,3=russian,4=korean,5=japanese,6=spanish,7=french

# Contact: reddit.com/u/Heavy-Testnet-Wolf or HeavyTestnetWolf@yandex.com
# Donate: BTC 3H1DsoRZAcSBhJV8gZUopAMCLDLCy3M7qT
#         ETH 0xd5e3c50f6a7eb05fb56442ad49b23ad3906d4e49

import APIConnector
import sqlite3
from time import sleep
import os
import sys
from datetime import datetime
from math import ceil
#Custom
from UsefulFunctions import seconds2str,clearConsole

clearConsole()

###########################################
# OPTIONAL SETTINGS
###########################################
TESTNET                          = False
DATABASE_FILENAME                = 'trollbox.db'
DATABASE_FILENAME_TESTNET        = 'trollbox_testnet.db'
SECONDS_TO_WAIT_BETWEEN_REQUESTS = 2.1
MESSAGES_PER_BATCH               = 500
DATABASE_ROOT_PATH               = '' # Database file location if not in same folder as this script. Example: 'C:/BitMEX/trollbox/'

###########################################
# END OF OPTIONAL SETTINGS
###########################################

if TESTNET:
    api_base_url = 'https://testnet.bitmex.com/api/v1/'
    db_file = DATABASE_ROOT_PATH+DATABASE_FILENAME_TESTNET
else:
    api_base_url = 'https://www.bitmex.com/api/v1/'
    db_file = DATABASE_ROOT_PATH+DATABASE_FILENAME

API_ENDPOINT    = 'chat'    
API_TIMEFORMAT  = '%Y-%m-%dT%H:%M:%S.%fZ'

connector = APIConnector.BitMEX(base_url=api_base_url)

###########################################
# Create local database file or open the existing one to find out where to start downloading
###########################################
if not os.path.isfile(db_file):
    print('Did not find existing database file. Creating one...')
    conn = sqlite3.connect(db_file,detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute('''CREATE TABLE messages
                 (id integer PRIMARY KEY UNIQUE,
                 id_bmex integer,
                 date timestamp, 
                 user text,
                 message text,
                 html text,
                 fromBot bool,
                 channelID integer)''')
    conn.commit()
    conn.close()
    start_message_id = 0
    message_id_prev = -1
else:
    print('Found existing database file.')
    conn = sqlite3.connect(db_file,detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT id_bmex FROM messages ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    if result == None:
        start_message_id = 0
        message_id_prev = -1
        print('Local database file is empty!')
    else:
        start_message_id = result[0]+1
        message_id_prev = start_message_id-1
        print('Last message in the local database has id='+str(result[0]))
    conn.commit()
    conn.close()
    
###########################################
# Find the last message id on the servers (used only to estimate time remaining)
###########################################
query = {
        'reverse': 'true',
        'start': 0,
        'count': 1,
        'filter': ''
    }
batch = connector._curl_bitmex(path=API_ENDPOINT, verb="GET", query=query, timeout=10)
if not batch or len(batch) == 0:
    sys.exit('Error finding the latest trollbox message ID')
latest_message_id = batch[0]['id']
print('Last message on BitMEX\' servers has    id='+str(latest_message_id))
sleep(SECONDS_TO_WAIT_BETWEEN_REQUESTS)

###########################################
# Download trollbox messages from the API
###########################################
print('Downloading, starting at message with  id='+str(start_message_id)+'...')
conn = sqlite3.connect(db_file,detect_types=sqlite3.PARSE_DECLTYPES)
c = conn.cursor()
number_of_messages_downloaded = 0 
number_of_missing_messages = 0
while True:
    query = {
        'reverse': 'false',
        'start': start_message_id,
        'count': MESSAGES_PER_BATCH,
        'filter': ''
    }
#    print('Downloading a new batch starting at message id='+str(start_message_id)+'...')
    batch = connector._curl_bitmex(path=API_ENDPOINT, verb="GET", query=query, timeout=10)
    if len(batch) == 0:
        print('No new messages')
        break
    if not batch:
        sys.exit('Something went wrong while downloading!')
    # Loop through message entries in the batch
    for entry in batch:
        channelID  = entry['channelID']
        date       = entry['date']
        date_n     = datetime.strptime(date, API_TIMEFORMAT)
        fromBot    = entry['fromBot']
        html       = entry['html']
        message_id = entry['id']
        message    = entry['message']
        user       = entry['user']
        
        # Check if current ID is last id +1
        if message_id != message_id_prev+1 and message_id_prev > -1:
            number_of_missing_messages += message_id-message_id_prev-1
            print(' Detected '+str(message_id-message_id_prev-1)+' missing message(s).')
        
        # Place in database
        c.execute('''INSERT INTO messages(id_bmex, date, user, message, html, fromBot, channelID)
        VALUES(?,?,?,?,?,?,?)''', (message_id, date_n, user, message, html, fromBot, channelID))
        
        number_of_messages_downloaded += 1
        message_id_prev = message_id
    conn.commit()
    
    if len(batch) < MESSAGES_PER_BATCH:
        print('Downloaded '+str(number_of_messages_downloaded)+' messages.')
        if number_of_missing_messages > 0:
              print('Number of messages missing (probably deleted by mods): '+str(number_of_missing_messages))
        print('Done.')
        break
        # In the next batch, start on next message id
    start_message_id = batch[-1]['id']+1
    print('Approximate time remaining: '+seconds2str(ceil((latest_message_id-start_message_id)/MESSAGES_PER_BATCH)*SECONDS_TO_WAIT_BETWEEN_REQUESTS))
    sleep(SECONDS_TO_WAIT_BETWEEN_REQUESTS)
conn.close()