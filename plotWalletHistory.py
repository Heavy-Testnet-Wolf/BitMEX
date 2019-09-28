# Plots your BitMEX wallet transaction history, i.e., deposits, affiliate
# payouts, withdrawals, realizations but most importantly your notional profit
# and ROE as they would be calculated on the leaderboard. Also plots the USD
# value of your account balance (based on .BXBT).
#
# HOW TO USE?
# Alternative 1: API keys:
#  a) Make sure USE_API is set to True.
#  b) Edit the API_KEY and API_SECRET variables with your own keys
#  c) Run the script.
#
# Alternative 2: CSV file:
#  a) Got to https://testnet.bitmex.com/app/wallet and export your wallet 
#    history by clicking "Save" in the top right corner. Note that this will 
#    only save one page at a time, so you if you have a lengthy history, you 
#    will neeed to export several files. Open them using Notepad and edit them 
#    together in one file. The oldest transactions must be at the bottom.
#  b) Place the resulting CSV file in the same directory as the python script
#  c) Make sure USE_API is set to False.
#  d) Edit WALLET_CSV_FILE to match the file name of your CSV file
#  c) Run the script.
#
# Contact: reddit.com/u/Heavy-Testnet-Wolf or HeavyTestnetWolf@yandex.com
# Donate: BTC 3H1DsoRZAcSBhJV8gZUopAMCLDLCy3M7qT
#         ETH 0xd5e3c50f6a7eb05fb56442ad49b23ad3906d4e49

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import csv
from datetime import datetime,timedelta
from time import sleep
import matplotlib.ticker as mticker
#Custom
import APIConnector
from UsefulFunctions import btc2str,pct2str,clearConsole
#from matplotlib.ticker import FormatStrFormatter

class WalletHistoryItem:
    def __init__(self):
        self.data = {}
        self.data['transactTime'] = datetime(2000, 1, 1, 0, 0)
        self.data['walletBalance'] = 0
        self.data['Deposit'] = 0
        self.data['AffiliatePayout'] = 0
        self.data['Withdrawal'] = 0
        self.data['RealisedPNL'] = 0
        self.data['i'] = 0
    
clearConsole()

###########################################
# SETTINGS THAT MUST BE EDITED
###########################################

USE_API  = True # True: read from API, False: read from CSV file

# API KEYS: Main account
TESTNET = False
API_KEY = 'AAAAAAAAAAAAAAAAAAAAAAAA'
API_SECRET = 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB'

# API KEYS: Testnet account
#TESTNET    = True
#API_KEY    = 'CCCCCCCCCCCCCCCCCCCCCCCC'
#API_SECRET = 'DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD'

# CSV FILE (needed only if USE_API=False):
WALLET_CSV_FILE = 'Wallet History  2019-8-22.csv'

###########################################
# OPTIONAL SETTINGS
###########################################

PLOT_NOTIONAL_PROFIT = True
PLOT_DEPOSITS        = True
PLOT_AFFILIATE       = True
PLOT_WITHDRAWALS     = True
PLOT_BALANCE         = True
PLOT_INDEX_1         = True
PLOT_INDEX_2         = False
PLOT_BALANCE_USD     = True # Uses index 1 (.BXBT) to calculate USD value

# Plot against indices
INDEX_1_TICKER    = '.BXBT'
INDEX_1_Y_AXIS_UNIT = '[USD/XBT]'
INDEX_1_BIN_SIZE   = '1d' # '1d' or '1h'

INDEX_2_TICKER    = '.BETHXBT' # '' or '.BXBT' or '.BETH' or '.BETHXBT' etc.
INDEX_2_Y_AXIS_UNIT = '[XBT/ETH]'
INDEX_2_BIN_SIZE   = '1d' # '1d' or '1h'

PLOT_UNIT           = 'XBT' # XBT, mXBT, uXBT or XBt
PLOT_TITLE          = 'My BitMEX gains'
PLOT_X_LABEL        = 'Date (UTC) [YYYY MM-DD]'
DATE_FORMAT_PLOT    = '%Y\n%m-%d' # %m-%d\n%Y
DATE_FORMAT_SUMMARY = '%Y-%m-%d %H:%M:%S'
LEGEND_ALPHA        = 0.9 # 0 is transparent
LEGEND_LOCATION     = 'upper center' # E.g., 'upper left', 'upper center', etc.

LINESTYLE_INDEX1,           COLOR_INDEX1           = '-', 'dodgerblue'
LINESTYLE_INDEX2,           COLOR_INDEX2           = '-', 'red'
LINESTYLE_ROE,              COLOR_ROE              = '-', 'red'
LINESTYLE_Deposits,         COLOR_Deposits         = '--', '#4DAF4A'
LINESTYLE_AffiliatePayouts, COLOR_AffiliatePayouts = '-', '#f442e2'
LINESTYLE_Withdrawals,      COLOR_Withdrawals      = '--', '#999999'
LINESTYLE_RealisedPNL,      COLOR_RealisedPNL      = '-', '#000000'
LINESTYLE_walletBalance,    COLOR_walletBalance    = '-', '#FF7F00'
LINESTYLE_walletBalanceUSD, COLOR_walletBalanceUSD = '-', 'blue'

AXIS_X_POS_INDEX_1     = 1.03
AXIS_X_POS_INDEX_2     = 1.08
AXIS_X_POS_BALANCE_USD = 1.13

###########################################
# END OF OPTIONAL SETTINGS
###########################################
API_ENDPOINT    = 'user/walletHistory'
API_TIMEFORMAT  = '%Y-%m-%dT%H:%M:%S.%fZ'
CSV_TIMEFORMAT = '%m/%d/%Y, %I:%M:%S %p'
API_TIMEFORMAT_INDEX  = '%Y-%m-%d %H:%M'

if USE_API:
    source_timeformat = API_TIMEFORMAT
else:
    source_timeformat = CSV_TIMEFORMAT

if TESTNET:
    api_base_url = 'https://testnet.bitmex.com/api/v1/'
else:
    api_base_url = 'https://www.bitmex.com/api/v1/'

if PLOT_UNIT == 'XBt':
    btc_factor = 1
elif PLOT_UNIT == 'uXBT':
    btc_factor = 100
elif PLOT_UNIT == 'mXBT':
    btc_factor = 100000
else:
    btc_factor = 100000000

if USE_API:
    print('Downloading from API...')
    connector = APIConnector.BitMEX(base_url=api_base_url, apiKey=API_KEY, apiSecret=API_SECRET)
    try:
        data = connector._curl_bitmex(path=API_ENDPOINT, verb="GET", query='', timeout=10)
    except Exception as ex:
        print('Error: ',ex)
else:
    print('Opening local CSV file...')
    with open(WALLET_CSV_FILE,encoding='utf-8-sig') as f:
        records = csv.DictReader(f)
        data = []
        for row in records:
             data.append(row)

walletHistoryItems = []    
for i,line in enumerate(data):
    if line['transactTime'] != None and line['transactStatus'] == 'Completed':
        item = WalletHistoryItem()
        item.data['transactTime']  = datetime.strptime(line['transactTime'], source_timeformat)
        item.data['walletBalance'] = int(line['walletBalance'])/btc_factor
        amount = int(line['amount'])/btc_factor
        if line['transactStatus'] == 'Completed':
#            print(item.data['transactTime'],line['transactType'],line['text'],btc2str(amount),line['transactStatus'])
            if line['transactType'] =='Deposit':
                item.data['Deposit'] = amount
            elif line['transactType'] =='RealisedPNL' or line['transactType'] =='CashRebalance' :
                item.data['RealisedPNL'] = amount
            elif line['transactType'] =='UnrealisedPNL':
                print('Skipping line with transactType=\'UnrealisedPNL\'')
            elif line['transactType'] =='Withdrawal':
                item.data['Withdrawal'] = abs(amount)
            elif line['transactType'] =='AffiliatePayout':
                item.data['AffiliatePayout'] = amount
            elif line['transactType'] =='Transfer' and (TESTNET or ('text' in line and line['text'] == 'Signup bonus')):
                item.data['Deposit'] = amount
            else:
                print('Unknown transactType: ', line)
        else:
            print('Skipping line with transactStatus=\''+line['transactStatus']+'\'')
        item.data['i'] = i
        walletHistoryItems.append(item)
        i+=1

# Sort
walletHistoryItems.sort(key=lambda item:item.data['i'], reverse=True)

# Accumulated values
walletHistoryAccumulated = {}
walletHistoryAccumulated['Deposit'] = 0
walletHistoryAccumulated['AffiliatePayout'] = 0
walletHistoryAccumulated['Withdrawal'] = 0
walletHistoryAccumulated['RealisedPNL'] = 0

walletHistory = {}
walletHistory['transactTime']    = []
walletHistory['walletBalance']   = []
walletHistory['Deposit']         = []
walletHistory['Withdrawal']      = []
walletHistory['RealisedPNL']     = []
walletHistory['AffiliatePayout'] = []
walletHistory['roe']             = []

date_tmp_prev = datetime(1970,1,1)
for item in walletHistoryItems:
    if item.data['transactTime'] < date_tmp_prev:
        print('Error while sorting wallet transactions')
    date_tmp_prev = item.data['transactTime']
    walletHistoryAccumulated['Deposit']         += item.data['Deposit']
    walletHistoryAccumulated['AffiliatePayout'] += item.data['AffiliatePayout']
    walletHistoryAccumulated['Withdrawal']      += item.data['Withdrawal']
    walletHistoryAccumulated['RealisedPNL']     += item.data['RealisedPNL']
    walletHistory['transactTime'].append(item.data['transactTime'])
    walletHistory['walletBalance'].append(item.data['walletBalance'])
    walletHistory['Deposit'].append(walletHistoryAccumulated['Deposit'])
    walletHistory['Withdrawal'].append(walletHistoryAccumulated['Withdrawal'])
    walletHistory['AffiliatePayout'].append(walletHistoryAccumulated['AffiliatePayout'])
    walletHistory['RealisedPNL'].append(walletHistoryAccumulated['RealisedPNL'])
    roe = 100*(item.data['walletBalance']+walletHistoryAccumulated['Withdrawal']-(walletHistoryAccumulated['Deposit']+walletHistoryAccumulated['AffiliatePayout']))/(walletHistoryAccumulated['Deposit']+walletHistoryAccumulated['AffiliatePayout']) if (walletHistoryAccumulated['Deposit']+walletHistoryAccumulated['AffiliatePayout']) > 0 else 0
    walletHistory['roe'].append(roe)
del walletHistoryItems

print('Loaded ',len(walletHistory['transactTime']), 'wallet transactions.')
print('First transaction: ',walletHistory['transactTime'][0].strftime(DATE_FORMAT_SUMMARY))
print('Last transaction:  ',walletHistory['transactTime'][-1].strftime(DATE_FORMAT_SUMMARY))

###############################################################
# Download indices from API
###############################################################
indexPrices = []
for i, ticker in enumerate([INDEX_1_TICKER,INDEX_2_TICKER]):
    indexPrices.append({})
    indexPrices[i]['timestamp'] = []
    if ticker != '':
        print('Downloading '+ticker+' data...')
        connector = APIConnector.BitMEX(base_url=api_base_url, apiKey=API_KEY, apiSecret=API_SECRET)
        COUNT = 500
        query = {'reverse': 'false',
                 'symbol': ticker,
                 'count': COUNT,
                 'binSize': INDEX_1_BIN_SIZE,
                 'startTime': (walletHistory['transactTime'][0]-timedelta(days=1)).strftime(API_TIMEFORMAT_INDEX),
#                 'endTime': (walletHistory['transactTime'][-1]+timedelta(days=1)).strftime(API_TIMEFORMAT_INDEX),
                 'filter': ''}
        indexPrices[i]['close'] = []
        indexPrices[i]['high']  = []
        indexPrices[i]['low']   = []
        while True:
            index_data = connector._curl_bitmex(path='trade/bucketed', verb="GET", query=query, timeout=10)
            if len(index_data) == 0:
                print('Error: no data')
                break
            for line in index_data:
                timestamp = datetime.strptime(line['timestamp'], API_TIMEFORMAT)
                if line['close'] != 0:
                    indexPrices[i]['timestamp'].append(timestamp)
                    indexPrices[i]['close'].append(line['close'])
                    indexPrices[i]['high'].append(line['high'])
                    indexPrices[i]['low'].append(line['low'])
                else:
                    print('price is zero. Skipping this line')
            if len(index_data) < COUNT:
                print(' Finished.')
                break
            sleep(2)
            query['startTime'] = (timestamp+timedelta(days=1)).strftime(API_TIMEFORMAT_INDEX)
        # Get the latest single data point as well
        query = {'reverse': 'true',
                 'symbol': ticker,
                 'count': 1,
                 'filter': ''}
        index_data = connector._curl_bitmex(path='trade', verb="GET", query=query, timeout=10)
        if len(index_data) == 0:
            print('Error: no data')
            break
        timestamp = datetime.strptime(index_data[0]['timestamp'], API_TIMEFORMAT)
        indexPrices[i]['timestamp'].append(timestamp)
        indexPrices[i]['close'].append(line['close'])
        indexPrices[i]['low'].append(line['close'])
        indexPrices[i]['high'].append(line['close'])

###############################################################
# Define first and last timestamp of the data to be plotted
###############################################################
firstDateTime  = min(walletHistory['transactTime'][0], indexPrices[0]['timestamp'][0] if len(indexPrices[0]['timestamp']) > 0  else datetime(2070, 1, 1), indexPrices[1]['timestamp'][0] if len(indexPrices[1]['timestamp']) > 0  else datetime(2070, 1, 1))
latestDateTime = max(datetime.now(), walletHistory['transactTime'][-1], indexPrices[0]['timestamp'][-1] if len(indexPrices[0]['timestamp']) > 0  else datetime(1970, 1, 1), indexPrices[1]['timestamp'][-1] if len(indexPrices[1]['timestamp']) > 0  else datetime(1970, 1, 1))

###############################################################
# Dollar values of the wallet balance based on the .BXBT index
###############################################################
walletHistory_USD = {}
walletHistory_USD['timestamp']    = []
walletHistory_USD['walletBalance']   = []
walletHistory_USD['Deposit']         = []
walletHistory_USD['Withdrawal']      = []
myList= indexPrices[0]['timestamp']
j = 0
for i in range(0,len(myList)):
    indexPriceDate = indexPrices[0]['timestamp'][i]
    
    while j+1 < len(walletHistory['transactTime']) and walletHistory['transactTime'][j+1] < indexPriceDate:
        j+=1
#    print(i,'Index date ',indexPriceDate, ' Latest transaction', walletHistory['transactTime'][j])
    walletHistory_USD['timestamp'].append(indexPriceDate)
    walletHistory_USD['walletBalance'].append(walletHistory['walletBalance'][j]*indexPrices[0]['close'][i])
    walletHistory_USD['Deposit'].append(walletHistory['Deposit'][j]*indexPrices[0]['close'][i])
    walletHistory_USD['Withdrawal'].append(walletHistory['Withdrawal'][j]*indexPrices[0]['close'][i])

###############################################################
# Extrapolate to current day in case there haven't been any transactions lately
###############################################################
walletHistory['transactTime'].append(latestDateTime)
walletHistory['walletBalance'].append(walletHistory['walletBalance'][-1])
walletHistory['Deposit'].append(walletHistory['Deposit'][-1])
walletHistory['Withdrawal'].append(walletHistory['Withdrawal'][-1])
walletHistory['AffiliatePayout'].append(walletHistory['AffiliatePayout'][-1])
walletHistory['RealisedPNL'].append(walletHistory['RealisedPNL'][-1])
walletHistory['roe'].append(walletHistory['roe'][-1])

###############################################################
# Plot
###############################################################
print('Plotting...')
plt.close('all')
fig, axis_host = plt.subplots()
fig.subplots_adjust(right=0.75)

legend_lines1, legend_labels1= [],[]
legend_lines2, legend_labels2= [],[]
legend_lines3, legend_labels3= [],[]
legend_lines4, legend_labels4= [],[]
legend_lines5, legend_labels5= [],[]

# ROE
axis_host.set_title(PLOT_TITLE)
axis_host.set_xlabel(PLOT_X_LABEL)
axis_host.set_ylabel('ROE [%]')
axis_host.grid(color=COLOR_ROE, linestyle=':',alpha=0.4,zorder=1)
axis_host.tick_params('y', which='both', colors=COLOR_ROE)
axis_host.step(walletHistory['transactTime'],walletHistory['roe'],color=COLOR_ROE,zorder=15, clip_on=False, linestyle=LINESTYLE_ROE,linewidth=1,marker='',markersize=2, alpha=1,where='post',label='ROE [%]'.ljust(16)+pct2str(walletHistory['roe'][-1],2))
axis_host.plot(walletHistory['transactTime'][-1], walletHistory['roe'][-1], marker='o', markersize=5, zorder=50, clip_on=False, color=COLOR_ROE)
axis_host.yaxis.label.set_color(COLOR_ROE)
axis_host.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
axis_host.xaxis.set_major_formatter(mdates.DateFormatter(DATE_FORMAT_PLOT)) 
axis_host.spines['left'].set_color(COLOR_ROE)
axis_host.yaxis.set_major_formatter(mticker.ScalarFormatter())
axis_host.yaxis.get_major_formatter().set_scientific(False)
axis_host.yaxis.get_major_formatter().set_useOffset(False)
legend_lines1, legend_labels1 = axis_host.get_legend_handles_labels()

# Wallet transacitons (in bitcoins)
axis_xbt = axis_host.twinx()
axis_xbt.set_ylabel('Bitcoins [XBT]')
axis_xbt.grid(color='black', linestyle='--',alpha=0.6)
if PLOT_DEPOSITS:
    axis_xbt.step(walletHistory['transactTime'],walletHistory['Deposit']        ,color=COLOR_Deposits,         alpha=1.0, zorder=10, clip_on=False, linestyle=LINESTYLE_Deposits,         linewidth=1, where='post', label='Deposited'.ljust(16)+btc2str(walletHistory['Deposit'][-1],PLOT_UNIT))
    axis_xbt.plot(walletHistory['transactTime'][-1], walletHistory['Deposit'][-1],         marker='o', markersize=5, zorder=16, clip_on=False, color=COLOR_Deposits)
if PLOT_AFFILIATE:
    axis_xbt.step(walletHistory['transactTime'],walletHistory['AffiliatePayout'],color=COLOR_AffiliatePayouts, alpha=1.0, zorder=10, clip_on=False, linestyle=LINESTYLE_AffiliatePayouts, linewidth=1, where='post', label='Affiliate'.ljust(16)+btc2str(walletHistory['AffiliatePayout'][-1],PLOT_UNIT))
    axis_xbt.plot(walletHistory['transactTime'][-1], walletHistory['AffiliatePayout'][-1], marker='o', markersize=5, zorder=16, clip_on=False, color=COLOR_AffiliatePayouts)
if PLOT_WITHDRAWALS:
    axis_xbt.step(walletHistory['transactTime'],walletHistory['Withdrawal']     ,color=COLOR_Withdrawals,      alpha=1.0, zorder=10, clip_on=False, linestyle=LINESTYLE_Withdrawals,      linewidth=1, where='post', label='Withdrawn'.ljust(16)+btc2str(walletHistory['Withdrawal'][-1],PLOT_UNIT))
    axis_xbt.plot(walletHistory['transactTime'][-1], walletHistory['Withdrawal'][-1],      marker='o', markersize=5, zorder=16, clip_on=False, color=COLOR_Withdrawals)
if PLOT_BALANCE:
    axis_xbt.step(walletHistory['transactTime'],walletHistory['walletBalance']  ,color=COLOR_walletBalance,    alpha=1.0, zorder=10, clip_on=False, linestyle=LINESTYLE_walletBalance,    linewidth=1, where='post', label='Balance'.ljust(16)+btc2str(walletHistory['walletBalance'][-1],PLOT_UNIT))
    axis_xbt.plot(walletHistory['transactTime'][-1], walletHistory['walletBalance'][-1],   marker='o', markersize=5, zorder=16, clip_on=False, color=COLOR_walletBalance)
if PLOT_NOTIONAL_PROFIT:
    axis_xbt.step(walletHistory['transactTime'],walletHistory['RealisedPNL']    ,color=COLOR_RealisedPNL,      alpha=1.0, zorder=10, clip_on=False, linestyle=LINESTYLE_RealisedPNL,      linewidth=3, where='post', label='Notional profit'.ljust(16)+btc2str(walletHistory['RealisedPNL'][-1],PLOT_UNIT))
    axis_xbt.plot(walletHistory['transactTime'][-1], walletHistory['RealisedPNL'][-1],     marker='o', markersize=5, zorder=16, clip_on=False, color=COLOR_RealisedPNL)
axis_xbt.yaxis.label.set_color('k')
legend_lines2, legend_labels2 = axis_xbt.get_legend_handles_labels()

if PLOT_INDEX_1:
    axis_index1 = axis_host.twinx()
#    axis_index1.set_ylabel(INDEX_1_TICKER+' '+INDEX_1_Y_AXIS_UNIT)
    axis_index1.yaxis.label.set_color(COLOR_INDEX1)
    axis_index1.tick_params('y', which='both', colors=COLOR_INDEX1)
    axis_index1.fill_between(indexPrices[0]['timestamp'],indexPrices[0]['low'], indexPrices[0]['high'], facecolor=COLOR_INDEX1, alpha=0.4)
    axis_index1.fill_between(indexPrices[0]['timestamp'],0,indexPrices[0]['low'], facecolor=COLOR_INDEX1, alpha=0.2)
    axis_index1.spines["right"].set_position(("axes", AXIS_X_POS_INDEX_1))
    axis_index1.spines["right"].set_visible(True)
    axis_index1.spines["right"].set_color(COLOR_INDEX1)
    axis_index1.plot(indexPrices[0]['timestamp'],indexPrices[0]['close'],COLOR_INDEX1,alpha=0.4, label=INDEX_1_TICKER.ljust(16)+str(indexPrices[0]['close'][-1]))
    axis_index1.plot(indexPrices[0]['timestamp'][-1],indexPrices[0]['close'][-1], marker='o', markersize=5, zorder=10, clip_on=False, color=COLOR_INDEX1)
    axis_index1.set_ylim([0,20000])
    legend_lines3, legend_labels3 = axis_index1.get_legend_handles_labels()
    
if PLOT_INDEX_2:
    axis_index2 = axis_host.twinx()
#    axis_index2.set_ylabel(INDEX_2_TICKER+' '+INDEX_2_Y_AXIS_UNIT)
    axis_index2.yaxis.label.set_color(COLOR_INDEX2)
    axis_index2.tick_params('y', which='both', colors=COLOR_INDEX2)
    axis_index2.fill_between(indexPrices[1]['timestamp'],indexPrices[1]['low'], indexPrices[1]['high'], facecolor=COLOR_INDEX2, alpha=0.4)
    axis_index2.fill_between(indexPrices[1]['timestamp'],0,indexPrices[1]['low'], facecolor=COLOR_INDEX2, alpha=0.2)
    axis_index2.spines["right"].set_position(("axes", AXIS_X_POS_INDEX_2))
    axis_index2.spines["right"].set_visible(True)
    axis_index2.spines["right"].set_color(COLOR_INDEX2)
    axis_index2.plot(indexPrices[1]['timestamp'],indexPrices[1]['close'],COLOR_INDEX2,alpha=0.4, label=INDEX_2_TICKER.ljust(16)+str(indexPrices[1]['close'][-1]))
    axis_index2.plot(indexPrices[0]['timestamp'][-1],indexPrices[1]['close'][-1], marker='o', markersize=5, zorder=10, clip_on=False, color=COLOR_INDEX2)
    axis_index2.set_ylim([0,max(indexPrices[1]['close'])])
    legend_lines4, legend_labels4 = axis_index2.get_legend_handles_labels()

if PLOT_BALANCE_USD:
    axis_usd = axis_host.twinx()
    axis_usd.set_ylabel('Balance [USD]')
    axis_usd.yaxis.label.set_color(COLOR_walletBalanceUSD)
    axis_usd.tick_params('y', which='both', colors=COLOR_walletBalanceUSD)
    
    axis_usd.spines["right"].set_position(("axes", AXIS_X_POS_BALANCE_USD))
    axis_usd.spines["right"].set_visible(True)
    axis_usd.spines["right"].set_color(COLOR_walletBalanceUSD)
    axis_usd.step(walletHistory_USD['timestamp'],walletHistory_USD['walletBalance']  ,color=COLOR_walletBalanceUSD,    alpha=1.0, zorder=10, clip_on=False, linestyle=LINESTYLE_walletBalanceUSD,    linewidth=1, where='post', label='Balance [USD]'.ljust(16)+str(round(walletHistory_USD['walletBalance'][-1])))
    axis_usd.plot(walletHistory_USD['timestamp'][-1], walletHistory_USD['walletBalance'][-1], marker='o', markersize=5, zorder=16, clip_on=False, color=COLOR_walletBalanceUSD)
    
    axis_usd.yaxis.set_major_formatter(mticker.ScalarFormatter())
    axis_usd.yaxis.get_major_formatter().set_scientific(False)
    axis_usd.yaxis.get_major_formatter().set_useOffset(False)
    legend_lines5, legend_labels5 = axis_usd.get_legend_handles_labels()

leg = axis_host.legend(legend_lines2+legend_lines1+legend_lines5+legend_lines3+legend_lines4, legend_labels2+legend_labels1+legend_labels5+legend_labels3+legend_labels4, loc=LEGEND_LOCATION,prop={'family': 'monospace'})
leg.get_frame().set_alpha(LEGEND_ALPHA)
leg.set_title('All time statistics ['+PLOT_UNIT+']', prop={'size': 10, 'weight': 'heavy','family': 'monospace'})

axis_host.patch.set_visible(False)
axis_xbt.patch.set_visible(False)
axis_host.set_zorder(5)
axis_xbt.set_zorder(4)
axis_xbt.set_xlim([firstDateTime,latestDateTime])

plt.show()
fig.tight_layout()
