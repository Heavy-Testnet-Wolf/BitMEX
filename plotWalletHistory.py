# Plots your BitMEX wallet transaction history, i.e., deposits, affiliate
# payouts, withdrawals, realizations but most importantly your notional profit
# and ROE as they would be calculated on the leaderboard.
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
API_KEY = 'b7fsdRffF55u2FFhLOL_rOfl'
API_SECRET = 'sDFSDFSdfSDfSDFsdfFSdfSDabcSFSDFDFSFSSDF-342Fsdf'

# API KEYS: Testnet account
#TESTNET    = True
#API_KEY = 'b2hnfgRffF55u2FFhDDD_sdfd'
#API_SECRET = 'sVbFGDdgDSFGDFgfSDFGDgdFGSDGDFGdgDFGDF-342sdfsF'

# CSV FILE (needed only if USE_API=False):
WALLET_CSV_FILE = 'Wallet History  2019-8-22.csv'

###########################################
# OPTIONAL SETTINGS
###########################################

# Plot against indeces
INDEX_1_TICKER    = '.BXBT' # '' or '.BXBT' or '.BETH' or '.BETHXBT' etc.
INDEX_1_Y_AXIS_UNIT = '[USD/XBT]'
INDEX_1_BIN_SIZE   = '1d' # '1d' or '1h'

INDEX_2_TICKER    = '.BETHXBT' # '' or '.BXBT' or '.BETH' or '.BETHXBT' etc.
INDEX_2_Y_AXIS_UNIT = '[XBT/ETH]'
INDEX_2_BIN_SIZE   = '1d' # '1d' or '1h'

PLOT_UNIT           = 'XBT' # XBT, mXBT, uXBT or XBt
PLOT_TITLE          = 'Heavy-Testnet-Wolf\'s BitMEX trading history'
PLOT_X_LABEL        = 'Date (UTC) [YYYY MM-DD]'
DATE_FORMAT_PLOT    = '%Y\n%m-%d' # %m-%d\n%Y
DATE_FORMAT_SUMMARY = '%Y-%m-%d %H:%M:%S'
LEGEND_ALPHA        = 0.9 # 0 is transparent
LEGEND_LOCATION     = 'upper left' # E.g., 'upper left', 'upper center', etc.

LINESTYLE_INDEX1,           COLOR_INDEX1           = '-', 'dodgerblue'
LINESTYLE_INDEX2,           COLOR_INDEX2           = '-', 'red'
LINESTYLE_ROE,              COLOR_ROE              = '-', 'red'
LINESTYLE_Deposits,         COLOR_Deposits         = '--', '#4DAF4A'
LINESTYLE_AffiliatePayouts, COLOR_AffiliatePayouts = '-', '#f442e2'
LINESTYLE_Withdrawals,      COLOR_Withdrawals      = '--', '#999999'
LINESTYLE_RealisedPNL,      COLOR_RealisedPNL      = '-', '#000000'
LINESTYLE_walletBalance,    COLOR_walletBalance    = '-', '#FF7F00'

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

if PLOT_UNIT == 'XBt':
    btc_factor = 1
elif PLOT_UNIT == 'uXBT':
    btc_factor = 100
elif PLOT_UNIT == 'mXBT':
    btc_factor = 100000
else:
    btc_factor = 100000000

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
        
# Sort by index
walletHistoryItems.sort(key=lambda item:item.data['i'], reverse=True)

# Accumulated values
walletHistoryAccumulated = {}
walletHistoryAccumulated['Deposit'] = 0
walletHistoryAccumulated['AffiliatePayout'] = 0
walletHistoryAccumulated['Withdrawal'] = 0
walletHistoryAccumulated['RealisedPNL'] = 0

# Lists for plotting
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
        print('Error while sorting')
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

indexPrices = []
for i, ticker in enumerate([INDEX_1_TICKER,INDEX_2_TICKER]):
    indexPrices.append({})
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
        indexPrices[i]['timestamp'] = []
        indexPrices[i]['close']     = []
        indexPrices[i]['high']      = []
        indexPrices[i]['low']       = []
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

print('Plotting...')

plt.close('all')
fig, host = plt.subplots()
fig.subplots_adjust(right=0.75)

host.set_title(PLOT_TITLE)
host.set_xlabel(PLOT_X_LABEL)
host.set_ylabel('ROE [%]')
host.grid(color=COLOR_ROE, linestyle=':',alpha=0.4,zorder=1)
host.tick_params('y', which='both', colors=COLOR_ROE)
host.step(walletHistory['transactTime'],walletHistory['roe'],color=COLOR_ROE,linestyle=LINESTYLE_ROE,linewidth=1,marker='',markersize=2, alpha=1,label='ROE [%]'.ljust(16)+pct2str(walletHistory['roe'][-1],2))
host.yaxis.label.set_color(COLOR_ROE)
host.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
host.xaxis.set_major_formatter(mdates.DateFormatter(DATE_FORMAT_PLOT)) 
host.spines['left'].set_color(COLOR_ROE)

par1 = host.twinx()
par1.set_ylabel('[XBT]')
par1.grid(color='black', linestyle='--',alpha=0.6)
par1.step(walletHistory['transactTime'],walletHistory['Deposit']        ,color=COLOR_Deposits,         alpha=1.0, linestyle=LINESTYLE_Deposits,         linewidth=1, label='Deposited'.ljust(16)+btc2str(walletHistory['Deposit'][-1],PLOT_UNIT))
par1.step(walletHistory['transactTime'],walletHistory['AffiliatePayout'],color=COLOR_AffiliatePayouts, alpha=1.0, linestyle=LINESTYLE_AffiliatePayouts, linewidth=1, label='Affiliate'.ljust(16)+btc2str(walletHistory['AffiliatePayout'][-1],PLOT_UNIT))
par1.step(walletHistory['transactTime'],walletHistory['Withdrawal']     ,color=COLOR_Withdrawals,      alpha=1.0, linestyle=LINESTYLE_Withdrawals,      linewidth=1, label='Withdrawn'.ljust(16)+btc2str(walletHistory['Withdrawal'][-1],PLOT_UNIT))
par1.step(walletHistory['transactTime'],walletHistory['walletBalance']  ,color=COLOR_walletBalance,    alpha=1.0, linestyle=LINESTYLE_walletBalance,    linewidth=1, label='Balance'.ljust(16)+btc2str(walletHistory['walletBalance'][-1],PLOT_UNIT))
par1.step(walletHistory['transactTime'],walletHistory['RealisedPNL']    ,color=COLOR_RealisedPNL,      alpha=1.0, linestyle=LINESTYLE_RealisedPNL,      linewidth=3, label='Notional profit'.ljust(16)+btc2str(walletHistory['RealisedPNL'][-1],PLOT_UNIT))
par1.yaxis.label.set_color('k')

plotIndex1 = 'close' in indexPrices[0] and len(indexPrices[0]['close']) >0
plotIndex2 = 'close' in indexPrices[1] and len(indexPrices[1]['close']) >0

if plotIndex1:
    par2 = host.twinx()
    par2.set_ylabel(INDEX_1_TICKER+' '+INDEX_1_Y_AXIS_UNIT)
    par2.yaxis.label.set_color(COLOR_INDEX1)
    par2.tick_params('y', which='both', colors=COLOR_INDEX1)
#    par2.set_yscale('log')
#    par2.yaxis.set_major_formatter(FormatStrFormatter("%.0f"))
#    par2.yaxis.set_minor_formatter(FormatStrFormatter("%.0f"))
    par2.fill_between(indexPrices[0]['timestamp'],indexPrices[0]['low'], indexPrices[0]['high'], facecolor=COLOR_INDEX1, alpha=0.4)
    par2.fill_between(indexPrices[0]['timestamp'],0,indexPrices[0]['low'], facecolor=COLOR_INDEX1, alpha=0.2)
    par2.spines["right"].set_position(("axes", 1.05))
    par2.spines["right"].set_visible(True)
    par2.spines["right"].set_color(COLOR_INDEX1)
    par2.plot(indexPrices[0]['timestamp'],indexPrices[0]['close'],COLOR_INDEX1,alpha=0.4, label=INDEX_1_TICKER.ljust(16)+str(round(indexPrices[0]['close'][-1])))
#    par2.patch.set_visible(False)
    par2.set_zorder(3)
if plotIndex2:
    par3 = host.twinx()
    par3.set_ylabel(INDEX_2_TICKER+' '+INDEX_2_Y_AXIS_UNIT)
    par3.yaxis.label.set_color(COLOR_INDEX2)
    par3.tick_params('y', which='both', colors=COLOR_INDEX2)
#    par3.set_yscale('log')
#    par3.yaxis.set_major_formatter(FormatStrFormatter("%.0f"))
#    par3.yaxis.set_minor_formatter(FormatStrFormatter("%.0f"))
    par3.fill_between(indexPrices[1]['timestamp'],indexPrices[1]['low'], indexPrices[1]['high'], facecolor=COLOR_INDEX2, alpha=0.4)
    par3.fill_between(indexPrices[1]['timestamp'],0,indexPrices[1]['low'], facecolor=COLOR_INDEX2, alpha=0.2)
    par3.spines["right"].set_position(("axes", 1.11))
    par3.spines["right"].set_visible(True)
    par3.spines["right"].set_color(COLOR_INDEX2)
    par3.plot(indexPrices[1]['timestamp'],indexPrices[1]['close'],COLOR_INDEX2,alpha=0.4, label=INDEX_2_TICKER.ljust(16)+str(round(indexPrices[1]['close'][-1])))
#    par3.patch.set_visible(False)
    par3.set_zorder(2)
lines1, labels1 = par1.get_legend_handles_labels() # Value [XBT]
lines2, labels2 = host.get_legend_handles_labels() # ROE [%]

if plotIndex1:
    lines3, labels3 = par2.get_legend_handles_labels() # Index1
    par1.set_xlim([walletHistory['transactTime'][0],indexPrices[0]['timestamp'][-1]])
elif plotIndex2:
    lines4, labels4 = par3.get_legend_handles_labels() # Index2
    par1.set_xlim([walletHistory['transactTime'][0],indexPrices[1]['timestamp'][-1]])
else:
    par1.set_xlim([walletHistory['transactTime'][0],walletHistory['transactTime'][-1]])

leg = host.legend(lines1+lines2, labels1+labels2, loc=LEGEND_LOCATION,prop={'family': 'monospace'})
#if plotIndex1 and plotIndex2:
#    leg = host.legend(lines1+lines2+lines3+lines4, labels1+labels2+labels3+labels4, loc=LEGEND_LOCATION,prop={'family': 'monospace'})
leg.get_frame().set_alpha(LEGEND_ALPHA)
leg.set_title('All time statistics ['+PLOT_UNIT+']', prop={'size': 10, 'weight': 'heavy','family': 'monospace'})

host.patch.set_visible(False)
par1.patch.set_visible(False)
host.set_zorder(5)
par1.set_zorder(4)

plt.show()
fig.tight_layout()