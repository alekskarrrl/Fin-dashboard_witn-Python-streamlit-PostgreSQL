
import datetime

import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import json
import plotly.express as px
from loading_wsb_to_db import load_wsb

import config
import psycopg2, psycopg2.extras
import streamlit as st

# ###########################################################################
# Method for Select from DB and displaying posts from wsb, parameters - symbol
# ###########################################################################

# ПЕРЕДЕЛАТЬ
def wsb_from_db(symbol):
    connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                                  password=config.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
                        Select symbol, message, url, dt, sourse
                        From mention JOIN stock on stock.id = mention.stock_id
                        where symbol = %s
                        Order by dt Desc Limit 150 

        """, (symbol,))  # There must be a comma to make that a tuple.

    mentions = cursor.fetchall()
    for mention in mentions:
        st.text(mention['dt'])
        st.text(mention['symbol'])
        st.text(mention['message'])
        st.text(mention['url'])
        st.text(mention['sourse'])
        st.text("* * * \t\t * * * \t\t * * *")

    rows = cursor.fetchall()
    return rows
#
#
# #############################################################################
# Show selected portfolios as DataFrame (as of fixed date 2021-06-08, later it will be possible to select a date)
# data on portfolios as of date is stored in the database
# parameters -  selected accounts on the side panel as a list
# ###############################################################################

def show_portfolios(selected_portfolios):

    connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                                  password=config.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    df_portfolio = pd.DataFrame(columns=['Ticker', 'Name', 'Shares', 'Average purchase price', 'Purchase value',
                                         'Sales value', 'Portfolio'])

    tuple_portfolio = tuple(selected_portfolios)

    if len(tuple_portfolio) == 0:
        rows = []
    elif len(tuple_portfolio) == 1:
        cursor.execute(f""" 
                                   Select symbol, name, shares, avg_purchase_price, purchase_value, sales_value, portfolio
                                   from stock JOIN  portfolios ON stock.id = portfolios.stock_id
                                   Where dt='2021-06-08' and portfolio = %s;

                                   """, (selected_portfolios[0],))
        rows = cursor.fetchall()

    elif len(tuple_portfolio) > 1:
        cursor.execute(""" 
                                           Select symbol, name, shares, avg_purchase_price, purchase_value, sales_value, portfolio
                                           from stock JOIN  portfolios ON stock.id = portfolios.stock_id
                                           Where dt='2021-06-08' and portfolio in {s};

                                           """.format(s=tuple_portfolio))
        rows = cursor.fetchall()

    for row in rows:
        df_portfolio = df_portfolio.append(
            {'Ticker': row[0], 'Name': row[1], 'Shares': row[2], 'Average purchase price': row[3],
             'Purchase value': row[4],
             'Sales value': row[5], 'Portfolio': row[6]}, ignore_index=True)

    connection.commit()

    df_portfolio['Shares'] = df_portfolio['Shares'].astype('int')
    df_portfolio['Average purchase price'] = round(df_portfolio['Average purchase price'].astype('float'), 2)
    df_portfolio['Purchase value'] = round(df_portfolio['Purchase value'].astype('float64'), 2)
    df_portfolio['Sales value'] = df_portfolio['Sales value'].astype('float')

    return df_portfolio


