"""BitMEX API Connector."""
import requests
from time import sleep
import json
#from . import errors
import math
import uuid
from AccessTokenAuth import AccessTokenAuth
from APIKeyAuthWithExpires import APIKeyAuthWithExpires
#from .APIKeyAuth import generate_nonce, generate_signature,APIKeyAuth
import sys

# https://www.bitmex.com/api/explorer/

class AuthenticationError(Exception):
    pass

class BitMEX(object):

    """BitMEX API Connector."""

    def __init__(self, base_url=None, symbol=None, login=None, password=None, otpToken=None,
                 apiKey=None, apiSecret=None, orderIDPrefix=''):
        """Init connector."""
        self.base_url = base_url
        self.symbol = symbol
        self.token = None
        self.login = login
        self.password = password
        self.otpToken = otpToken
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        if len(orderIDPrefix) > 13:
            raise ValueError("settings.ORDERID_PREFIX must be at most 13 characters long!")
        self.orderIDPrefix = orderIDPrefix

        # Prepare HTTPS session
        self.session = requests.Session()
        # These headers are always sent
        self.session.headers.update({'user-agent': 'easy-data-scripts'})

# Public methods
    def ticker_data(self):
        """Get ticker data."""
        data = self.get_instrument()

        ticker = {
            # Rounding to tickLog covers up float error
            "last": data['lastPrice'],
            "buy": data['bidPrice'],
            "sell": data['askPrice'],
            "mid": (float(data['bidPrice']) + float(data['askPrice'])) / 2
        }

        return {k: round(float(v), data['tickLog']) for k, v in ticker.items()}

    def get_instrument(self):
        """Get an instrument's details."""
        path = "instrument"
        instruments = self._curl_bitmex(path=path, query={'filter': json.dumps({'symbol': self.symbol})})
        if len(instruments) == 0:
            print("Instrument not found: %s." % self.symbol)
            exit(1)

        instrument = instruments[0]
        if instrument["state"] != "Open":
            print("The instrument %s is no longer open. State: %s" % (self.symbol, instrument["state"]))
            exit(1)

        # tickLog is the log10 of tickSize
        instrument['tickLog'] = int(math.fabs(math.log10(instrument['tickSize'])))

        return instrument

    def market_depth(self):
        """Get market depth / orderbook."""
        path = "orderBook"
        return self._curl_bitmex(path=path, query={'symbol': self.symbol})

    def recent_trades(self):
        """Get recent trades.

        Returns
        -------
        A list of dicts:
              {u'amount': 60,
               u'date': 1306775375,
               u'price': 8.7401099999999996,
               u'tid': u'93842'},

        """
        path = "trade"
        return self._curl_bitmex(path=path)

    @property
    def snapshot(self):
        """Get current BBO."""
        order_book = self.market_depth()
        return {
            'bid': order_book[0]['bidPrice'],
            'ask': order_book[0]['askPrice'],
            'size_bid': order_book[0]['bidSize'],
            'size_ask': order_book[0]['askSize']
        }

# Authentication required methods
    def authenticate(self):
        """Set BitMEX authentication information."""
        if self.apiKey:
            return
        loginResponse = self._curl_bitmex(
            path="user/login",
            postdict={'email': self.login, 'password': self.password, 'token': self.otpToken})
        self.token = loginResponse['id']
        self.session.headers.update({'access-token': self.token})

    def authentication_required(fn):
        """Annotation for methods that require auth."""
        def wrapped(self, *args, **kwargs):
            if not (self.token or self.apiKey):
                msg = "You must be authenticated to use this method"
                print(msg)
                exit(1)
            else:
                return fn(self, *args, **kwargs)
        return wrapped

    @authentication_required
    def funds(self):
        """Get your current balance."""
        return self._curl_bitmex(path="user/margin")

    @authentication_required
    def buy(self, quantity, price):
        """Place a buy order.

        Returns order object. ID: orderID
        """
        return self.place_order(quantity, price)

    @authentication_required
    def sell(self, quantity, price):
        """Place a sell order.

        Returns order object. ID: orderID
        """
        return self.place_order(-quantity, price)

    @authentication_required
    def place_order(self, quantity, price):
        """Place an order."""
        if price < 0:
            raise Exception("Price must be positive.")

        endpoint = "order"
        # Generate a unique clOrdID with our prefix so we can identify it.
        clOrdID = self.orderIDPrefix + uuid.uuid4().bytes.encode('base64').rstrip('=\n')
        postdict = {
            'symbol': self.symbol,
            'quantity': quantity,
            'price': price,
            'clOrdID': clOrdID
        }
        return self._curl_bitmex(path=endpoint, postdict=postdict, verb="POST")

    @authentication_required
    def open_orders(self):
        """Get open orders."""
        path = "order"

        filter_dict = {'ordStatus.isTerminated': False}
        if self.symbol:
            filter_dict['symbol'] = self.symbol

        orders = self._curl_bitmex(
            path=path,
            query={'filter': json.dumps(filter_dict)},
            verb="GET"
        )
        # Only return orders that start with our clOrdID prefix.
        return [o for o in orders if str(o['clOrdID']).startswith(self.orderIDPrefix)]

    @authentication_required
    def cancel(self, orderID):
        """Cancel an existing order."""
        path = "order"
        postdict = {
            'orderID': orderID,
        }
        return self._curl_bitmex(path=path, postdict=postdict, verb="DELETE")

    def _curl_bitmex(self, path, query=None, postdict=None, timeout=3, verb=None):
#        print('Running _curl_bitmex')
        """Send a request to BitMEX Servers."""
        # Handle URL
        url = self.base_url + path

        # Default to POST if data is attached, GET otherwise
        if not verb:
            verb = 'POST' if postdict else 'GET'

        # Auth: Use Access Token by default, API Key/Secret if provided
        auth = AccessTokenAuth(self.token)
        if self.apiKey:
            auth = APIKeyAuthWithExpires(self.apiKey, self.apiSecret)
#            auth = APIKeyAuth(self.apiKey, self.apiSecret)

        # Make the request
#        print('url:',url,'\nverb:',verb,'\npostdict:',postdict,'\nquery:',query)
        try:
            req = requests.Request(verb, url, data=postdict, auth=auth, params=query)
            prepped = self.session.prepare_request(req)
            response = self.session.send(prepped, timeout=timeout)
            # Make non-200s throw
            response.raise_for_status()
#            try:
#                print('Response headers:')
#                for keys,values in response.headers.items():
#                    print(keys+':',values)
#            except:
#                print('Error printing response headers')

        except requests.exceptions.HTTPError as e:
            # 401 - Auth error. Re-auth and re-run this request.
            if response.status_code == 401:
                if self.token is None:
                    print("Login information or API Key incorrect, please check and restart.")
                    print("Error: " + response.text)
                    if postdict:
                        print(postdict)
                    exit(1)
                print("Token expired, reauthenticating...")
                sleep(1)
                self.authenticate()
                return self._curl_bitmex(path, query, postdict, timeout, verb)

            # 404, can be thrown if order canceled does not exist.
            elif response.status_code == 404:
                if verb == 'DELETE':
                    print("Order not found: %s" % postdict['orderID'])
                    return
                print("Unable to contact the BitMEX API (404). Request: %s \n %s" % (url, json.dumps(postdict)))
                exit(1)

            # 503 - BitMEX temporary downtime, likely due to a deploy. Try again
            elif response.status_code == 503:
                print("Unable to contact the BitMEX API (503), retrying. Request: %s \n %s" % (url, json.dumps(postdict)))
                sleep(1)
                return self._curl_bitmex(path, query, postdict, timeout, verb)
            # Unknown Error
            else:
                print("Unhandled Error:", e, response.text)
                print("Endpoint was: %s %s" % (verb, path))
                sys.exit()

        except requests.exceptions.Timeout as e:
            # Timeout, re-run this request
            print("Timed out, retrying...")
            return self._curl_bitmex(path, query, postdict, timeout, verb)

        except requests.exceptions.ConnectionError as e:
            print("Unable to contact the BitMEX API (ConnectionError). Please check the URL. Retrying. Request: %s \n %s" % (url, json.dumps(postdict)))
            sleep(1)
            return self._curl_bitmex(path, query, postdict, timeout, verb)

        return response.json()
