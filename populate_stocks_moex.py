
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 20:03:52 2021

@author: User
"""

import config
import psycopg2
import psycopg2.extras
import csv

connection = psycopg2.connect(host =config.DB_HOST, database = config.DB_NAME, user = config.DB_USER, password = config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

with open("rates.csv", encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        print(row)
        ticker = row[0]

        if ticker:
            name = row[2]
            cursor.execute("""
                           INSERT INTO stock (name, symbol, exchange, is_etf)
                           VALUES (%s, %s, 'MOEX', false)

                           """, (name, ticker))


connection.commit()

