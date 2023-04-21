import datetime
# from psaw import PushshiftAPI
# from pmaw import PushshiftAPI
import psycopg2
import psycopg2.extras
import streamlit as st
import os
from enum import Enum
import requests
from dotenv import load_dotenv


load_dotenv()

class Search_subject(Enum):
    SUBMISSIONS = "submission"
    COMMENTS = "comment"


def get_reddit_submissions(search_where: str, subreddit: str, search_window: int = 1):
    base_url = "https://api.pushshift.io/reddit/search/"
    try:

        url = f"{base_url}{search_where}/?fields=url,author,title,subreddit&subreddit={subreddit}&after={search_window}d&size=500"
        print(url)
        request = requests.get(url=url)
        response = request.json()['data']

    except KeyError as e:
        print("KeyError in get_reddit_submissions", e)
    else:
        return [sub for sub in response if (sub['removed_by'] is None and sub['removed_by_category'] is None)]


# @st.cache
def load_wsb(n_last_days):
    connection = psycopg2.connect(host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
                              password=os.getenv('DB_PASS'))
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(""" 
                   SELECT * FROM stock
                   """)
    rows = cursor.fetchall()

    stocks = {}
    for row in rows:
        stocks['$' + row['symbol']] = row['id']

    submissions = get_reddit_submissions(Search_subject.SUBMISSIONS.value,
                                         subreddit="StockMarket",
                                         search_window=n_last_days)

    for submission in submissions:
        words = submission['title'].split()
        cash_words = list(set(filter(lambda word: word.lower().startswith('$'), words)))
        cashtags = [cashtag for cashtag in cash_words if cashtag in stocks]

        if (len(cashtags) > 0):
            # print(cashtags)
            # print (submission.created_utc)
            # print (submission.title)
            # print (submission.url)

            for cashtag in cashtags:
                submitted_time = datetime.datetime.fromtimestamp(submission['created_utc']).isoformat()
                try:

                    # st.write(f"{submitted_time}, {stocks[cashtag]}, {submission['title']}, {submission['url']}")
                    cursor.execute("""
                                   INSERT INTO mention (dt, stock_id, message, sourse, url)
                                   VALUES (%s, %s, %s, 'wallstreetbets', %s)
                                   """, (submitted_time, stocks[cashtag], submission['title'], submission['url']))
                    connection.commit()
                except Exception as e:
                    st.error(f"Data not written to database {os.getenv('DB_NAME')}, {e}")
                    connection.rollback()



# ###########################################################################
# Method for Select from DB and displaying posts from wsb, parameters - symbol
# ###########################################################################

# ПЕРЕДЕЛАТЬ
def wsb_from_db(symbol):
    connection = psycopg2.connect(host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
                              password=os.getenv('DB_PASS'))
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
