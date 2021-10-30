
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 19:58:01 2021

@author: User
"""

import datetime
from psaw import PushshiftAPI
import psycopg2
import psycopg2.extras
import streamlit as st

import config


@st.cache
def load_wsb(n_last_days):
    connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                                  password=config.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(""" 
                   SELECT * FROM stock 
    
                   """)
    rows = cursor.fetchall()

    stocks = {}
    for row in rows:
        stocks['$' + row['symbol']] = row['id']
        # print(row)

    # print(stocks)

    api = PushshiftAPI()

    now = datetime.datetime.now()
    n_delta = datetime.timedelta(n_last_days)
    start_time = int((now - n_delta).timestamp())
    # print(now)
    # print(n_delta)
    # print(start_time)

    submissions = api.search_submissions(after=start_time,
                                         subreddit='wallstreetbets',
                                         filter=['url', 'author', 'title', 'subreddit'])

    for submission in submissions:
        words = submission.title.split()
        cashtags = list(set(filter(lambda word: word.lower().startswith('$'), words)))

        if (len(cashtags) > 0):
            # print(cashtags)
            # print (submission.created_utc)
            # print (submission.title)
            # print (submission.url)

            for cashtag in cashtags:
                submitted_time = datetime.datetime.fromtimestamp(submission.created_utc).isoformat()
                try:
                    cursor.execute("""
                                   INSERT INTO mention (dt, stock_id, message, sourse, url)
                                   VALUES (%s, %s, %s, 'wallstreetbets', %s)
                                   """, (submitted_time, stocks[cashtag], submission.title, submission.url))
                    connection.commit()
                except Exception as e:
                    # print(e)
                    connection.rollback()



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
