<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 20:03:52 2021

@author: User
"""

import config
import alpaca_trade_api as tradeapi
import psycopg2
import psycopg2.extras

connection = psycopg2.connect(host =config.DB_HOST, database = config.DB_NAME, user = config.DB_USER, password = config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
#cursor.execute("SELECT * FROM stock")
#stocks = cursor.fetchall()
#for stock in stocks:
#    print(stock['name'])

api = tradeapi.REST(config.API_KEY, config.API_SECRET, config.API_URL)
assets = api.list_assets()



for asset in assets:
    print(f"Inserting stock: {asset.name} {asset.symbol}")
    cursor.execute("""
                    INSERT INTO stock (name, symbol, exchange, is_etf)
                    VALUES (%s, %s, %s, false)
                    """, (asset.name, asset.symbol, asset.exchange))
                   
connection.commit()

=======
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 20:03:52 2021

@author: User
"""

import config
import alpaca_trade_api as tradeapi
import psycopg2
import psycopg2.extras

connection = psycopg2.connect(host =config.DB_HOST, database = config.DB_NAME, user = config.DB_USER, password = config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
#cursor.execute("SELECT * FROM stock")
#stocks = cursor.fetchall()
#for stock in stocks:
#    print(stock['name'])

api = tradeapi.REST(config.API_KEY, config.API_SECRET, config.API_URL)
assets = api.list_assets()



for asset in assets:
    print(f"Inserting stock: {asset.name} {asset.symbol}")
    cursor.execute("""
                    INSERT INTO stock (name, symbol, exchange, is_etf)
                    VALUES (%s, %s, %s, false)
                    """, (asset.name, asset.symbol, asset.exchange))
                   
connection.commit()

>>>>>>> 5e12f69a0b3fe4e192d4dbb9640da803624873af
