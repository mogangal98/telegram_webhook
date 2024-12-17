"""
Custom binance client
"""

import requests
import hmac
import hashlib
import sys
import logging
import datetime as dt
import os

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://fapi.binance.com/", recv_window: int = 10000):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.recv_window = recv_window
        
        # Logging
        error_log_path = os.path.expanduser('~')+'/BinanceClient.log'
        self.error_logger = logging.getLogger('error_logger')
        self.error_logger.setLevel(logging.DEBUG)  # Set the logging level you need
        error_file_handler = logging.FileHandler(error_log_path, mode='a')
        error_file_handler.setLevel(logging.DEBUG)
        self.error_logger.addHandler(error_file_handler)

    # Api key needs to be hashed on request
    # Private func
    def _hashing(self, query_string: str) -> str:
        return hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
    
    # Turn params to string to send alongside the request
    def _params_to_str(self, params_dic):
        params = list(params_dic.keys())
        return_string = ""
        for i in params:
            return_string = return_string + i + "=" + str(params_dic[i]) + "&"    
        return return_string[:-1]
    
    # Checks for open position for the given pair
    def pos_check(self, pair = "BTCUSDT"):
        try:
            for i in range(3): # 3 Tries
                timestamp = str(int(dt.datetime.now().timestamp()*1000)) # Binance timestamp format is in miliseconds
                params = {"timestamp": timestamp, "symbol" : pair, "recvWindow" : self.recv_window}
                params["signature"] = self._hashing(self._params_to_str(params))
                get_data = requests.get(self.base_url+"fapi/v2/positionRisk",
                                   params = params,
                                   headers = {"X-MBX-APIKEY": self.api_key}, timeout = 2)    
                if (get_data.status_code == 200): 
                    verijson = get_data.json()
                    return verijson
                    break
                else:
                    error_text = "Pos_check error: " + str(get_data.status_code) + " --- "+ str(get_data.reason)
                    self.error_logger.warning(error_text)
        except Exception as e: 
            e = sys.exc_info()[0:2]
            self.error_logger.warning("Pos_check error: " + str(e))
    
    # Checks open orders for the given pair
    def all_orders(self, pair: str = "BTCUSDT"): 
        timestamp = str(int(dt.datetime.now().timestamp()*1000))
        params = {"symbol": pair, "timestamp": timestamp, "recvWindow" : self.recv_window}
        params["signature"] = self._hashing(self._params_to_str(params))
        get_data = requests.get(self.base_url+"fapi/v1/openOrders",
                          params = params,
                          headers = {"X-MBX-APIKEY": self.api_key}, timeout = 2)    
        if (get_data.status_code == 200):   
            try:
                verijson = get_data.json()
                all_orders = verijson 
            except Exception as e: 
                e = sys.exc_info()[0:2]
                self.error_logger.warning("all_orders error: " + e)
            return all_orders    

        else:
            error_text = str(get_data.status_code) + " --- "+ str(get_data.reason) 
            self.error_logger.warning("all_orders error: " + error_text)
            
    # Returns the current price (exchange rate) of the given pair
    def ticker_price(self, pair: str ="BTCUSDT",borsa: str = "SPOT"):
        try: 
            if borsa == "SPOT":
                url = 'https://api.binance.com/api/v3/ticker/price'
                params = {'symbol': pair}
                get_data = requests.get(url, params=params)
            else:
                timestamp = str(int(dt.datetime.now().timestamp()*1000))
                params = {"timestamp": timestamp, "symbol" : pair}
                params["signature"] = self._hashing(self._params_to_str(params))
                get_data = requests.get(self.base_url+"fapi/v1/ticker/price",
                                   params = params,
                                   headers = {"X-MBX-APIKEY": self.api_key}, timeout = 2)    
            if get_data.status_code == 200: 
                verijson = get_data.json()
            else: 
                error_text = str(get_data.status_code)
                self.error_logger.warning(error_text)
                
            pair_ticker_price = float(verijson['price']) 
            return pair_ticker_price
                
        except Exception as e: 
            e = sys.exc_info()[0:2]
            self.error_logger.warning("ticker_price error: " + str(e))
            return "ERROR"