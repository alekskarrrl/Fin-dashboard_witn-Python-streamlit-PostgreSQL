<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 23:11:49 2021

@author: User
"""

import config
import psycopg2
import psycopg2.extras
import csv


connection = psycopg2.connect(host =config.DB_HOST, database = config.DB_NAME, user = config.DB_USER, password = config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
# cursor.execute("SELECT * FROM stock WHERE is_etf = TRUE")
# etfs = cursor.fetchall()

dates = ['2021-06-06', '2021-06-08']
portfolios = ['IIS_Tinkof_Cat', 'not_IIS_Tinkof_Cat', 'IIS_VTB_Hamster']  # IIS_VTB_Hamster doesnt work
#portfolios = ['IIS_VTB_Hamster']
ticker_not_found = []


for current_date in dates:
    for portfolio in portfolios:
        print(portfolio)
        with open(f"data/portfolio/{current_date}/{portfolio}.csv", encoding='UTF-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                ticker = row[0]

                if ticker:
                    shares = row[2]
                    avg_purchase_price = row[3]
                    purchase_value = row[5]
                    sales_value = row[6]
                    cursor.execute("""
                                   SELECT * FROM stock WHERE symbol=%s
                                   
                                   """, (ticker,))
                    stock = cursor.fetchone()
                    if stock:
                        cursor.execute("""
                                       INSERT INTO portfolios (portfolio, stock_id, dt, shares, avg_purchase_price, purchase_value, sales_value)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                                       """, (portfolio, stock['id'], current_date, shares, avg_purchase_price, purchase_value, sales_value))
                    else:
                        ticker_not_found.append(ticker)
                                       
connection.commit()

if len(ticker_not_found)==0:
    print("All tickers have been successfully added!")
else:
    print("Tickers is not found: ", ticker_not_found)
    
    
=======
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 23:11:49 2021

@author: User
"""

import config
import psycopg2
import psycopg2.extras
import csv


connection = psycopg2.connect(host =config.DB_HOST, database = config.DB_NAME, user = config.DB_USER, password = config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
# cursor.execute("SELECT * FROM stock WHERE is_etf = TRUE")
# etfs = cursor.fetchall()

dates = ['2021-06-06', '2021-06-08']
portfolios = ['IIS_Tinkof_Cat', 'not_IIS_Tinkof_Cat', 'IIS_VTB_Hamster']  # IIS_VTB_Hamster doesnt work
#portfolios = ['IIS_VTB_Hamster']
ticker_not_found = []


for current_date in dates:
    for portfolio in portfolios:
        print(portfolio)
        with open(f"data/portfolio/{current_date}/{portfolio}.csv", encoding='UTF-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                ticker = row[0]

                if ticker:
                    shares = row[2]
                    avg_purchase_price = row[3]
                    purchase_value = row[5]
                    sales_value = row[6]
                    cursor.execute("""
                                   SELECT * FROM stock WHERE symbol=%s
                                   
                                   """, (ticker,))
                    stock = cursor.fetchone()
                    if stock:
                        cursor.execute("""
                                       INSERT INTO portfolios (portfolio, stock_id, dt, shares, avg_purchase_price, purchase_value, sales_value)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                                       """, (portfolio, stock['id'], current_date, shares, avg_purchase_price, purchase_value, sales_value))
                    else:
                        ticker_not_found.append(ticker)
                                       
connection.commit()

if len(ticker_not_found)==0:
    print("All tickers have been successfully added!")
else:
    print("Tickers is not found: ", ticker_not_found)
    
    
>>>>>>> 5e12f69a0b3fe4e192d4dbb9640da803624873af
