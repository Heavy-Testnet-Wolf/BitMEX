# Examples on how to read from the SQLite database created with trollboxFetch.py
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

import sqlite3
from datetime import datetime
#Custom
from UsefulFunctions import extractSubstringFromRight

DATABASE_FILENAME  = 'trollbox.db'
#DATABASE_FILENAME  = 'trollbox_testnet.db'
DATABASE_ROOT_PATH = '' # Database file location if not in same folder as this script. Example: 'C:/BitMEX/trollbox/'
OUTPUT_TIMEFORMAT  = '%Y-%m-%d %H:%M:%S'

CHANNELS = [[1,'english'],
            [2,'chinese'],
            [3,'russian'],
            [4,'korean'],
            [5,'japanese'],
            [6,'spanish'],
            [7,'french']]

db_file = DATABASE_ROOT_PATH+DATABASE_FILENAME

###########################################
# EXAMPLE 1: PRINT ALL MESSAGES FROM A SPECIFIC USER
###########################################

USER = 'Jeezus'

conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()
for row in cursor.execute('SELECT date,user,message FROM messages WHERE user=? ORDER BY id ASC',(USER,)):
    timestamp = row[0]
    user      = row[1]
    message   = row[2]
    print(timestamp.strftime(OUTPUT_TIMEFORMAT)+' '+user+': '+message)
conn.close()
print('Done.')

###########################################
# EXAMPLE 2: PRINT ALL MESSAGES IN A SPECIFIC CHANNEL DURING A SPECIFIC TIME PERIOD
###########################################

DATE_START = datetime(2017, 12, 17, 12, 0, 0, 00000)
DATE_END   = datetime(2017, 12, 17, 12, 17, 58, 000000)
CHANNEL_ID = 1

conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()
for row in cursor.execute('SELECT date,user,message FROM messages WHERE date>=? AND date <=? AND channelID=? ORDER BY id ASC',(DATE_START,DATE_END,CHANNEL_ID,)):
    timestamp = row[0]
    user      = row[1]
    message   = row[2]
    print(timestamp.strftime(OUTPUT_TIMEFORMAT)+' '+user+': '+message)
conn.close()
print('Done.')

###########################################
# EXAMPLE 3: PRINT ALL /POSITIONS in a certain instrument larger than a certain number of contracts
###########################################

INSTRUMENT = 'XBTUSD'
MINIMUM_NUMBER_OF_CONTRACTS = 10000000
STRING_TO_LOOK_FOR = '/position%<pre><code><img class="emoji" src="%" /> '+INSTRUMENT+':%</pre>'

conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()
for row in cursor.execute('SELECT date,user,message,html FROM messages WHERE html LIKE ? ORDER BY id ASC',(STRING_TO_LOOK_FOR,)):
    timestamp = row[0]
    user      = row[1]
    message   = row[2]
    message_html = row[3]
    if message_html[0:16].lower() == '/position '+INSTRUMENT.lower():
        numberOfContracts_string = extractSubstringFromRight(message_html,'/> '+INSTRUMENT+': ',' Cont @ ')
        numberOfContracts = int(numberOfContracts_string.replace(',',''))
        price_string = extractSubstringFromRight(message_html,'/> '+INSTRUMENT+': '+numberOfContracts_string+' Cont @ ','\n')
        price = float(price_string)
        if numberOfContracts > abs(MINIMUM_NUMBER_OF_CONTRACTS):
            print(timestamp.strftime(OUTPUT_TIMEFORMAT)+' '+user+': '+str(numberOfContracts)+' contracts in '+INSTRUMENT+' @ '+str(price))
conn.close()
print('Done.')

###########################################
# EXAMPLE 4: Print PNLs that were flashed in the trollbox using /pnl, /rpnl or /upnl (over a certain size)
###########################################

MINIMUM_BTC = 500
STRING_TO_LOOK_FOR = '/%pnl%<pre><code><img class="emoji" src="%" />%</pre>'

conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()
for row in cursor.execute('SELECT date,user,message,html FROM messages WHERE html LIKE ? ORDER BY id ASC',(STRING_TO_LOOK_FOR,)):
    timestamp = row[0]
    user      = row[1]
    message   = row[2]
    message_html = row[3]
    if message[0:5] == '/upnl':
        upnl_string = extractSubstringFromRight(message_html,': ',' XBT UPNL\n</code></pre>')
        rpnl_string = ''
    elif message[0:5] == '/rpnl':
        rpnl_string = extractSubstringFromRight(message_html,': ',' XBT RPNL\n</code></pre>')
        rpnl_string = ''
    elif message[0:5] == '/pnl ':
        upnl_string = extractSubstringFromRight(message_html,', ',' XBT UPNL\n</code></pre>')
        rpnl_string = extractSubstringFromRight(message_html,': ',' XBT RPNL, ')
    
    upnl = float(upnl_string) if upnl_string != '' else 0
    rpnl = float(rpnl_string) if rpnl_string != '' else 0
    if abs(upnl) > MINIMUM_BTC or abs(rpnl) > MINIMUM_BTC:
        print(timestamp.strftime(OUTPUT_TIMEFORMAT)+' '+user+': rpnl='+str(rpnl)+' upnl='+str(upnl))
conn.close()
print('Done.')