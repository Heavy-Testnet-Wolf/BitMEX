# Opens the database created with trollboxFetch.py and saves the trollbox history in readable text files
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

###########################################
# SETTINGS
###########################################

DATABASE_FILENAME  = 'trollbox.db'
#DATABASE_FILENAME = 'trollbox_testnet.db'

###########################################
# OPTIONAL SETTINGS
###########################################

DATABASE_ROOT_PATH = '' # Database file location if not in same folder as this script. Example: 'C:/BitMEX/trollbox/'
OUTPUT_FILE_PATH   = '' # Folder in which to place the output text files. Example: 'C:/BitMEX/trollbox/' If blank, same folder as this script
OUTPUT_TIMEFORMAT  = '%Y-%m-%d %H:%M:%S'

CHANNELS = [[1,'english'],
            [2,'chinese'],
            [3,'russian'],
            [4,'korean'],
            [5,'japanese'],
            [6,'spanish'],
            [7,'french']]

###########################################
# END OF SETTINGS
###########################################

db_file = DATABASE_ROOT_PATH+DATABASE_FILENAME

print('Opening local trollbox database and writing to text files. This could take a while!')

YEARS = [2014,2015,2016,2017,2018,2019]

for year in YEARS:
    date_start = datetime(year, 1, 1, 0, 0, 0, 000000)
    date_end = datetime(year, 12, 31, 23, 59, 59, 999999)
    for channel in CHANNELS:
        output_filename = OUTPUT_FILE_PATH+DATABASE_FILENAME+'_'+channel[1]+'_'+str(year)+'.txt'
        print('Writing to '+output_filename+'...')
        with open(output_filename, 'w+',encoding='utf-8-sig') as write_file:
            conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
            cursor = conn.cursor()
            for row in cursor.execute('SELECT date,user,message FROM messages WHERE channelID=? AND date>=? AND date <=? ORDER BY id ASC',(channel[0],date_start,date_end,)):
                timestamp = row[0]
                user      = row[1]
                message   = row[2]
                write_file.write(timestamp.strftime(OUTPUT_TIMEFORMAT)+' '+user+': '+message+'\n')
            conn.close()
print('Done.')