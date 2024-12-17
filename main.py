from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
import datetime as dt
import logging
import os
import ipaddress
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from binance_client import BinanceClient
from telegram_client import TelegramClient

# Fastapi
app = FastAPI()

# These are the official ip ranges of telegram servers.
# Our app will only accept requests from these ip ranges for extra protection.
ALLOWED_IP_RANGES = [
    "91.108.56.0/22",
    "91.108.4.0/22",
    "91.108.8.0/22",
    "91.108.16.0/22",
    "91.108.12.0/22",
    "149.154.160.0/20",
    "91.105.192.0/23",
    "91.108.20.0/22",
    "185.76.151.0/24",
    "2001:b28:f23d::/48",
    "2001:b28:f23f::/48",
    "2001:67c:4e8::/48",
    "2001:b28:f23c::/48",
    "2a0a:f280::/32"
]
# Convert the CIDR ranges to IP network objects
allowed_ip_networks = [ipaddress.ip_network(ip_range) for ip_range in ALLOWED_IP_RANGES]


# İnitialize the ip filter
class IPFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = ipaddress.ip_address(request.client.host)

        # Check if the client IP is in any of the allowed networks
        if not any(client_ip in network for network in allowed_ip_networks):
            # If the IP is not allowed, we will return a 403 response
            return JSONResponse(status_code=403, content={"detail": "Access denied"})
        
        # Proceed to process the request if the IP is allowed
        return await call_next(request)

app.add_middleware(IPFilterMiddleware)

binance_client = BinanceClient(api_key='x', api_secret='y')
telegram_client = TelegramClient(bot_token = "xx")

izin_listesi = ["username","of","admins"]

# Logger
error_log_path = os.path.expanduser('~')+'/main.log'
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.DEBUG)  # Set the logging level you need
error_file_handler = logging.FileHandler(error_log_path, mode='a')
error_file_handler.setLevel(logging.DEBUG)
error_logger.addHandler(error_file_handler)

# We will recieve post requests to "/webhook" endpoint for each request that comes to our bot
@app.post('/webhook')
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        update = await request.json()    
        background_tasks.add_task(process_webhook, update)
        return {'success': True}
    
    except Exception as e: 
        return {'success': True}
    
async def process_webhook(update):
    try:        
        command = "message"
        chat_id = update['message']['chat']['id']
        
        try: username = update['message']['chat']['username']
        except Exception as e: username = "" ; return
        
        # We will deconstruct the message to get the requested command
        message_text = update['message']['text']
        message_text = message_text.lower().strip()
        message_id = update['message']['message_id']
        
        # Logging the request
        log = f"{chat_id} - {username} ->  {message_text} "
        error_logger.info(log)
        
        # Only allowed users can use these commands
        if username in izin_listesi:   
            message_text = message_text.replace("/","")
            if message_text == "bot_status" or message_text == "status":
                await telegram_client.bot_status(chat_id,message_text)
                
            elif message_text == "help":
                await telegram_client.help_me(chat_id,message_text)     
           
            # # Removed
            # elif message_text == "balance":
            #     await telegram_client.balance(chat_id,message_text)    
                
            else:
                await telegram_client.bot_status(chat_id,message_text)
                
    except Exception as e:
        try:error_logger.warning("Webhook Error: "+ str(e) + " ||||  "+ str(dt.datetime.now()) + "    Request : " + str(username) +"  Telegram ID: "+ str(chat_id))
        except Exception as e: pass
    
if __name__ == "__main__":
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8443, log_level="info", workers=1, ssl_keyfile="/home/private.key", ssl_certfile="/home/public.pem")
        # # Alternatively, we can use Nginx as a proxy and redirect the requests coming to nginx to uvicorn
        # uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", workers = core_number)
    except Exception as e:
        error_logger.warning("uvicorn.run Error  "+ str(e) + " ||||  "+ str(dt.datetime.now()))