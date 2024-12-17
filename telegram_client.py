import aiohttp
import logging
import datetime as dt
import mysql.connector as mysql
import os

from binance_client import BinanceClient

class TelegramClient:
    def __init__(self, bot_token: str, timeout: int = 3):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.db = mysql.connect(host = "1", database = "2", user = "3", password = "4", auth_plugin = "mysql_native_password") 
        self.binance_client = BinanceClient(api_key='x', api_secret='y')
        
        # Logging
        error_log_path = os.path.expanduser('~')+'/TelegramClient.log'
        self.error_logger = logging.getLogger('error_logger')
        self.error_logger.setLevel(logging.DEBUG)  # Set the logging level you need
        error_file_handler = logging.FileHandler(error_log_path, mode='a')
        error_file_handler.setLevel(logging.DEBUG)
        self.error_logger.addHandler(error_file_handler)
        
    async def async_send_message(self, chat_id: int, text: str):
        try:
            payload = {
                'chat_id': chat_id,
                'text': text
            }
            async with aiohttp.ClientSession(timeout = 2, connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.post(f"{self.api_url}/sendMessage", json=payload) as response:
                    await response.json()
                    return 
        except Exception as e: 
            self.error_logger.warning("async_send_message error while sending message || "+str(dt.datetime.now())+" ||  Telegram ID: " + str(chat_id))
            
    async def bot_status(self, chat_id: int,text: str) -> None:
        try:
            # We will check the open position and its data. And text it back to user
            open_pos = self.binance_client.pos_check()

            posAmt = float(open_pos[0]["positionAmt"])
            
            if posAmt != 0:
                posAmt_dolar = abs(float(open_pos[0]["notional"]))
                giris_fiyati = float(open_pos[0]["entryPrice"])
                anlik_fiyat = float(open_pos[0]["markPrice"])
                kar = float(open_pos[0]["unRealizedProfit"])
                base_para = float(open_pos[0]["isolatedWallet"])
                kaldirac = float(open_pos[0]["leverage"])
                anlik_fiyat = float(open_pos[0]["markPrice"])
                stop_price = float(open_pos[0]["liquidationPrice"])
                pos_giris_zaman = float(open_pos[0]["updateTime"])
                if posAmt > 0: pos_side = "Long"
                elif posAmt < 0: pos_side = "Short"
                
                text += f"---------- POSITION ----------\n\nSide:   {pos_side}\nBase:   {base_para}\Leverage:    {kaldirac}\nEntry Pice:   {giris_fiyati}\n"
                
                # We will also send the order data
                emirler = self.binance_client.all_orders()
                for emir in emirler:
                    fiyat = emir['price']
                    tip = emir['origType'].lower()
                    if tip == "trailing_stop_market":
                        fiyat = emir['activatePrice']
                        pr = emir['priceRate']
                        text += f"{tip}: activation price:   {fiyat} | price rate: {pr}\n"
                    else:
                        if tip == "stop_market": fiyat = emir['stopPrice'] # stop market için stopPrice almamız gerekiyor
                        text += f"{tip}:   {fiyat}\n"
                    
                text += "\n\n"
                text += f"Current price: {anlik_fiyat:.2f}"
                text += f"\nProfit: $ {kar:.2f}"
            else: text += "No open positions"
            
            await self.async_send_message(chat_id,text)
                    
        except Exception as e:
             self.error_logger.warning("bot_status error || "+str(dt.datetime.now())+" ||  Telegram ID: " + str(chat_id))
             await self.async_send_message(chat_id,"ERROR")

             
    async def help_me(self, chat_id:int,text: str) -> None:
        try:        
            text = """/bot_status -- Give status report
/help -- Show commands
    """
            await self.async_send_message(chat_id,text)                
        except Exception as e:
             self.error_logger.warning("help error: " + str(e))
             await self.async_send_message(chat_id,"HATA")
