
from alpaca_trade_api.rest import REST, TimeFrame
import config
#import alpaca_trade_api as tradeapi
import json
import datetime, time
import aiohttp, asyncpg, asyncio
import requests


api = REST(config.API_KEY, config.API_SECRET, config.API_URL)
# assets = api.list_assets()

# for asset in assets:
#     print(asset)
    # print(f"Inserting stock: {asset.name} {asset.symbol}")
#
# barset = api.get_bars('AAPL', TimeFrame.Minute, "2021-05-11", "2021-05-12", adjustment='raw')
# print(barset[0])
# print(barset[0].o)
# print(barset[0].v)
# print(type(barset[0].t))
# print(datetime.datetime.fromisoformat(barset[0].t.strftime("%Y-%m-%d %H:%M:%S")))
# print(datetime.datetime.fromisoformat(barset[1].t.strftime("%Y-%m-%d %H:%M:%S")))

# pool = await asyncpg.create_pool(user=config.DB_USER, password=config.DB_PASS, database=config.DB_NAME, host=config.DB_HOST, command_timeout=60)

async def write_to_db(connection, params):
    await connection.copy_records_to_table('stock_price', records=params)


async def get_price(pool, stock_id, stock_symbol):

    try:
        async with pool.acquire() as connection:
            barset = api.get_bars(stock_symbol, TimeFrame.Hour, "2021-01-01", "2021-05-18", adjustment='raw')
            params = [(stock_id, datetime.datetime.fromisoformat(bar.t.strftime("%Y-%m-%d %H:%M:%S")), round(bar.o, 2),
                       round(bar.h, 2), round(bar.l, 2), round(bar.c, 2), bar.v) for bar in
                      barset]
            await write_to_db(connection, params)
            print(params)

    except Exception as e:
        print("Unable to get stocks {} due to {}.".format(stock_symbol, e.__class__))


async def get_prices(pool, stock_symbols):
    try:
        # schedule get requests to run concurrently for all symbols
        ret = await asyncio.gather(*[get_price(pool, stock_id, stock_symbols[stock_id]) for stock_id in stock_symbols])
        print("Finalized all. Returned  list of {} outputs.".format(len(ret)))
    except Exception as e:
        print(e)


async def get_stocks():
    # create database connection pool
    pool = await asyncpg.create_pool(user=config.DB_USER, password=config.DB_PASS, database=config.DB_NAME,
                                     host=config.DB_HOST, command_timeout=60)

    # get a connection
    async with pool.acquire() as connection:
        stocks = await connection.fetch("SELECT * FROM stock WHERE id IN (SELECT holding_id FROM etf_holding)")

        stock_symbols = {}
        for stock in stocks:
            stock_symbols[stock['id']] = stock['symbol']

    await get_prices(pool, stock_symbols)


start = time.time()
asyncio.run(get_stocks())
#asyncio.get_event_loop().run_until_complete(get_stocks())
end = time.time()
print("Took {} seconds.".format(end - start))
