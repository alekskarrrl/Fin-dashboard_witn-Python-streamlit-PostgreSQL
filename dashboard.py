# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 00:55:35 2021

@author: User
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import json
import plotly.express as px
from loading_wsb_to_db import load_wsb
# import tweepy  # for twitter API
import config
import psycopg2, psycopg2.extras

# import plotly.graph_objects as go

# proxie={'https' : 'https://15.188.82.98:80'}
proxie = {'https': 'https://103.138.40.202:8080'}

st.image("top_img.jpg")

st.sidebar.title("Options")

option = st.sidebar.selectbox("Which Dashboards&", ("wallstreetbets", "stocktwits", "Portfolio", "pattern"))
# st.header(option)


connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                              password=config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

# ----------------stocktwits -  Works only with proxie -----------------------
if option == "stocktwits":
    # pass
    symbol = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5)
    # st.subheader("Stocktwits")
    r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json", proxies=proxie)
    # r = requests.get("https://api.stocktwits.com/api/2/streams/symbol/AAPL.json")

    data = r.json()

    for message in data['messages']:
        st.image(message['user']['avatar_url'])
        st.write(message['user']['username'])
        st.write(message['created_at'])
        st.write(message['body'])

# ----------------wallstreetbets -------------------------------------------------------

if option == "wallstreetbets":
    st.subheader("Wallstreetbets dashboard")

    n_last_days = st.sidebar.slider("Load mentions from wsb to db for N last days: ", 1, 30)
    loadBtn = st.sidebar.button("Load data", "loadBtn")

    if loadBtn:
        n_last_days_to_load = n_last_days
        with st.spinner("Loading in progress ..."):
            load_wsb(n_last_days_to_load)
        st.success("Done!")

    ticker = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5).upper()

    st.subheader("Wallstreetbets: Top 10 most popular stocks for last 14 days")
    # st.subheader("")

    cursor.execute(""" 
                   SELECT Count(*) as num_mentions, symbol 
                   FROM mention JOIN stock ON stock.id = mention.stock_id 
                   Where date(dt) > current_date - interval '14 day'
                   Group by stock_id, symbol
                   Order by num_mentions DESC LIMIT 10

                   """)
    counts = cursor.fetchall()
    df_top = pd.DataFrame(columns=['symbol', 'counts'])
    for count in counts:
        # st.write(count[1], ': ', count[0],  ' comments')
        df_top = df_top.append({'symbol': count[1], 'counts': count[0]}, ignore_index=True)

    df_top['counts'].astype('int64')
    top_counts = px.bar(df_top, y='symbol', x='counts', color='symbol', orientation='h')
    st.plotly_chart(top_counts, use_container_width=True)

    cursor.execute("""
                    Select symbol, message, url, dt, sourse
                    From mention JOIN stock on stock.id = mention.stock_id
                    where symbol = %s
                    Order by dt Desc Limit 150 
    
    """, (ticker,))  # There must be a comma to make that a tuple.

    mentions = cursor.fetchall()
    for mention in mentions:
        st.text(mention['dt'])
        st.text(mention['symbol'])
        st.text(mention['message'])
        st.text(mention['url'])
        st.text(mention['sourse'])
        st.text("* * * \t\t * * * \t\t * * *")

    rows = cursor.fetchall()
    st.write(rows)

#
#

# -------------------Chart dashboard---------------------------------------------------

if option == "Portfolio":
    st.subheader("My portfolio analysis")
    df_portfolio = pd.DataFrame(columns=['Ticker', 'Name', 'Shares', 'Average purchase price', 'Purchase value',
                                         'Sales value', 'Portfolio'])

    portfolios_select = st.sidebar.multiselect("Choose the portfolios you need: ",
                                               ['IIS_Tinkof_Cat', 'not_IIS_Tinkof_Cat', 'IIS_VTB_Hamster'], ['IIS_Tinkof_Cat', 'not_IIS_Tinkof_Cat', 'IIS_VTB_Hamster'])
    tuple_portfolio = tuple(portfolios_select)

    if len(tuple_portfolio) ==0:
        rows = []
    elif len(tuple_portfolio) == 1:
        cursor.execute(f""" 
                               Select symbol, name, shares, avg_purchase_price, purchase_value, sales_value, portfolio
                               from stock JOIN  portfolios ON stock.id = portfolios.stock_id
                               Where dt='2021-06-08' and portfolio = %s;

                               """, (portfolios_select[0], ))
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

    st.dataframe(df_portfolio.style.format({'Average purchase price': "{:.2f}",
                                            'Purchase value': "{:.2f}",
                                            'Sales value': "{:.2f}"}), 1500, 700)

# -------------------Pattern dashboard-------------------------------------------------
#

if option == "pattern":
    st.subheader("Pattern dashboard")
#
# ------------------------------------------------------------------------------------
