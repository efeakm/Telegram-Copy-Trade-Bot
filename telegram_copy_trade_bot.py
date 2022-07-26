import asyncio
from metaapi_cloud_sdk import MetaApi
import time
from telethon import TelegramClient, events
import pandas as pd


###INPUT PARAMETERS
#==========================================================================================
TELEGRAM_ID = None
TELEGRAM_HASH = ''


settings = pd.read_csv('settings.csv')
settings = settings.set_index('Item')


META_TOKEN = str(settings.loc['API_TOKEN','Value'])
META_ACCOUNT_ID = str(settings.loc['ACCOUNT_ID','Value'])


DOW_SIZE = float(settings.loc['DOW_SIZE','Value'])
NASDAQ_SIZE = float(settings.loc['NASDAQ_SIZE','Value'])
DAX_SIZE = float(settings.loc['DAX_SIZE','Value'])
FTSE_SIZE = float(settings.loc['FTSE_SIZE','Value'])



api = MetaApi(token=META_TOKEN)
async def main():
    
    ###CONNECTION
    #==========================================================================
    account = await api.metatrader_account_api.get_account(account_id=META_ACCOUNT_ID)
    account_access_token = account.access_token
    print(account_access_token)
        
    connection = account.get_streaming_connection()
    await connection.connect()
    print('connected')
    await account.deploy()
    print('deployed')

    # not_deployed = True
    # while not_deployed:
    #     try:
    #         await account.deploy()
    #         not_deployed = False
    #     except:
    #         print('Wait 15 min due to free account restriction of metaapi')
    #         time.sleep(960)



    # access local copy of terminal state
    terminalState = connection.terminal_state
    await connection.wait_synchronized()
    print('ACCOUNT BALANCE:',terminalState.account_information['balance'])
    print('If the account balance is correct then, the bot has connected succesfully.')
    

    ###TELEGRAM MESSAGE FUNCTIONS
    #===========================================================================

    #Enter Trade Function
    #-----------------------------------------------------------------------
    def read_entry_order_message(message):
        
        message = message.replace(':','')
        message = message.replace('-','')
        
        if ('ENTRY' in message) and ('STOP' in message):
                        
            #BUY ORDER
            if 'BOUGHT' in message:
                                
                DIRECTION = 'BUY'
                words = message.split()
                symbols = words[:words.index('BOUGHT')]
            
                
            #SELL ORDER
            if 'SOLD' in message:
                                
                DIRECTION = 'SELL'
                words = message.split()
                symbols = words[:words.index('SOLD')]
            
            
            #SYMBOL
            for word in symbols:
                if 'DOW' in word.upper():
                    SYMBOL = '.US30.'
                    STOPLOSS = 100
                    LOT = DOW_SIZE
                    break
                elif 'NASDAQ' in word.upper():
                    SYMBOL = '.USTEC.'
                    STOPLOSS = 50
                    LOT = NASDAQ_SIZE
                    break
                elif 'FTSE' in word.upper():
                    SYMBOL = '.UK100.'
                    STOPLOSS = 25
                    LOT = FTSE_SIZE
                    break
                elif 'DAX' in word.upper():
                    SYMBOL = '.DE40.'
                    STOPLOSS = 50
                    LOT = DAX_SIZE
                    break
                
            #POSITION SIZE
            for word in words:
                if '%' in word:
                    POSITION_SIZE = float(word.replace('%',''))/100
                    POSITION_SIZE = int(POSITION_SIZE * LOT)
                    POSITION_SIZE = max(POSITION_SIZE,1)
                    break
        

        else:
            pass

        return DIRECTION, SYMBOL, STOPLOSS, POSITION_SIZE
    
    
    
    #Close Trade Function
    #-------------------------------------------------------------------------------
    def close_trade_message(message):

        words = message.split()
                
        #SYMBOL
        for word in words:
            if 'DOW' in word.upper():
                return '.US30.'
                
            if 'NASDAQ' in word.upper():
                return '.USTEC.'
                
            if 'FTSE' in word.upper():
                return '.UK100.'
                
            if 'DAX' in word.upper():
                return '.DE40.'

        return
        

                   
    
    
    ###TELEGRAM BOT
    #=============================================================================
    client = TelegramClient('anon', TELEGRAM_ID, TELEGRAM_HASH)
    channel_name = 'TraderTom Live Day Trading'
    START = time.time()

    @client.on(events.NewMessage(chats=channel_name))
    async def my_event_handler(event):
        
        
        message = str(event.raw_text)
        print("==============================================================")
        print(message)
        print()
        
        ###ENTER TRADE MESSAGE
        #=============================================================================
        try:
            DIRECTION, SYMBOL, STOPLOSS, POSITION_SIZE = read_entry_order_message(message)
            print('############## ENTERING LONG POSITION ##############')
            print(f'TRADE PARAMETERS: DIRECTION = {DIRECTION}, SYMBOL = {SYMBOL}, POSITION_SIZE = {POSITION_SIZE}')
            
            if DIRECTION == 'BUY':
                
                #Get market price
                # await connection.subscribe_to_market_data(symbol=SYMBOL)
                price = terminalState.price(symbol=SYMBOL)['ask']

                await connection.create_market_buy_order(symbol=SYMBOL,
                                    volume=POSITION_SIZE, stop_loss= price - STOPLOSS)
                print('############## ENTERING SHORT POSITION ##############')
                print(f'Buying {SYMBOL} at {price} with stoploss = {price - STOPLOSS} and position size = {POSITION_SIZE}')


                
            elif DIRECTION == 'SELL':
                
                #Get Market Price
                # await connection.subscribe_to_market_data(symbol=SYMBOL)
                price = terminalState.price(symbol=SYMBOL)['bid']

                await connection.create_market_sell_order(symbol=SYMBOL,
                                    volume=POSITION_SIZE, stop_loss=price + STOPLOSS)

                print(f'Selling {SYMBOL} at {price} with stoploss = {price + STOPLOSS} and position size = {POSITION_SIZE}')

            else:
                pass
            
        except:
            0
            
            
        ###CLOSE TRADE MESSAGE
        #=============================================================================
        if 'CLOSE TRADE ALERT' in message:
            try:
                CLOSE_SYMBOL = close_trade_message(message)
                print(f'############## CLOSING {CLOSE_SYMBOL} POSITIONS ##############')
                await connection.close_positions_by_symbol(symbol=CLOSE_SYMBOL)
        
            except:
                0

        print() 

        return 
            



    await client.start()
    await client.run_until_disconnected()
    
    
    

asyncio.run(main())




