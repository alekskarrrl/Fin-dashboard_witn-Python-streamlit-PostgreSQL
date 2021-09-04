# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 00:55:35 2021

@author: User
"""
from datetime import datetime, date, time

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
from dashboard_methods import wsb_from_db, show_portfolios
import altair as alt
import math
import tinvest
import tcs_api_modul as tcs
from collections import deque
import cbrf_currencies as cbr
import csv

# import plotly.graph_objects as go

# proxie={'https' : 'https://15.188.82.98:80'}
proxie = {'https': 'https://103.138.40.202:8080'}

st.image("top_img.jpg")

st.sidebar.title("Options")

option = st.sidebar.selectbox("Which Dashboards", ("wallstreetbets", "stocktwits", "Portfolio", "Tinkoff Invest", "Fundamental Data"))
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

    # By clicking on the button, we load posts from wsb into the database for the last n_last_days days

    n_last_days = st.sidebar.slider("Load mentions from wsb to db for N last days: ", 1, 30)
    loadBtn = st.sidebar.button("Load data", "loadBtn")

    if loadBtn:
        n_last_days_to_load = n_last_days
        with st.spinner("Loading in progress ..."):
            load_wsb(n_last_days_to_load)
        st.success("Done!")

    ticker = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5).upper()

    # ########################################################
    # displaying a chart of the top 10 most talked about stocks
    # ########################################################

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

    df_top['counts'] = df_top['counts'].astype('int64')
    df_top.sort_values(by='counts', ascending=True, inplace=True)
    #top_counts = px.bar(df_top, y='symbol', x='counts', orientation='h', color='counts')
    #st.plotly_chart(top_counts, use_container_width=True)

    st.write(alt.Chart(df_top).mark_bar().encode(alt.Y(field='symbol', type='nominal', sort='x'), x='counts', color='counts').properties(width=800, height=400))



    st.write(wsb_from_db(ticker)) # Method for Select from DB and displaying posts from wsb by ticker


# -------------------Portfolio---------------------------------------------------
# We have several brokerage accounts and these portfolios are accounted for separately.
# On this page, we can display one account separately, several accounts together or all together.
# To do this, select the required accounts on the side panel
#

if option == "Portfolio":
    st.subheader("My portfolio analysis")

    portfolios_select = st.sidebar.multiselect("Choose the portfolios you need: ",
                                               ['IIS_Tinkof_Cat', 'not_IIS_Tinkof_Cat', 'IIS_VTB_Hamster'], ['IIS_Tinkof_Cat', 'not_IIS_Tinkof_Cat', 'IIS_VTB_Hamster'])

    st.dataframe(show_portfolios(portfolios_select).style.format({'Average purchase price': "{:.2f}",
                                            'Purchase value': "{:.2f}",
                                            'Sales value': "{:.2f}"}), 1500, 700)

# -------------------Fundamental Data-------------------------------------------------
#

if option == "Fundamental Data":
    st.subheader("Fundamental Data")
    st.markdown(""" *The data on this page was obtained using the [Alpha Vantage API.](https://www.alphavantage.co/documentation/)*""")

# --------Enter the stock ticker that we want to analyze and the number of reporting quarters
    ticker = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5).upper()
    number_quarter = st.sidebar.slider("Set number of quarters to analyse: ", 1, 15, 5)

# ----- OVERVIEW  BLOCK ________________________________
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={config.AV_KEY}'
    r = requests.get(url)
    overview_data = r.json()
    st.subheader(overview_data["Name"])
    st.subheader(overview_data["Symbol"] + " | " + overview_data["Exchange"] + " | " + overview_data["Currency"] + " | "
                 + overview_data["Country"] + " | " + overview_data["Sector"])
    st.subheader("")
    with st.beta_expander("Company Description: "):
        st.markdown(overview_data["Description"])

    # -------- RATIOS ---------------------
    r_style = 'text-align:left; color: blue; border-style: solid; border-width: thin; border-color: #3F4E6A; ' \
              'border-radius: 10px; height: 60px; padding: 10px; font-size: 24px; color: #517FE1'

    listRatios = ['PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'DividendYield', 'EPS', 'ProfitMargin', 'DilutedEPSTTM',
                  'AnalystTargetPrice', 'EVToEBITDA', 'PayoutRatio', 'DividendDate']
    dictRatios = {'PERatio': 'P/E Ratio', 'PEGRatio': 'PEG Ratio', 'BookValue': 'Book Value', 'DividendPerShare': 'Dividend Per Share',
                  'DividendYield': 'Dividend Yield', 'EPS': 'EPS', 'ProfitMargin': 'Profit Margin', 'DilutedEPSTTM': 'Diluted EPS TTM',
                  'AnalystTargetPrice': 'Analyst Target Price', 'EVToEBITDA': 'EV To EBITDA', 'PayoutRatio': 'Payout Ratio', 'DividendDate': 'Dividend Date'}

    for i in range(0, math.ceil(len(listRatios)/3)):
        r1, r2, r3 = st.beta_columns(3)

        with r1:
            st.markdown(f"**{dictRatios[listRatios[i*3+0]]}**")
            st.markdown(f"<div style ='{r_style}'>{overview_data[listRatios[i*3+0]]}</div>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"**{dictRatios[listRatios[i*3+1]]}**")
            st.markdown(f"<div style ='{r_style}'>{overview_data[listRatios[i*3+1]]}</div>", unsafe_allow_html=True)
        with r3:
            st.markdown(f"**{dictRatios[listRatios[i*3+2]]}**")
            st.markdown(f"<div style ='{r_style}'>{overview_data[listRatios[i*3+2]]}</div>", unsafe_allow_html=True)

        st.subheader("")


# ----- OVERVIEW  BLOCK ________________________________


# Select Balance Sheet, Income Statement or CASH FLOW
    reports = st.selectbox("Select Balance Sheet, Income Statement or Financial Ratios", ('Balance Sheet', 'Income Statement', 'CASH FLOW'))

    if reports == 'Income Statement':
    # send API request with function=INCOME_STATEMENT
        reports_func = "INCOME_STATEMENT"
        list_of_field_default = ['totalRevenue', 'grossProfit', 'ebitda', 'operatingIncome', 'incomeBeforeTax', 'netIncome']

    elif reports == 'Balance Sheet':
    # send API request with function=BALANCE_SHEET
        reports_func = "BALANCE_SHEET"
        list_of_field_default = ['cashAndCashEquivalentsAtCarryingValue', 'totalCurrentAssets', 'totalAssets', 'inventory',
                                 'totalNonCurrentAssets', 'propertyPlantEquipment', 'totalLiabilities', 'totalCurrentLiabilities',
                                 'currentDebt', 'longTermDebt', 'totalNonCurrentLiabilities']
    elif reports == 'CASH FLOW':
    # send API request with function=CASH_FLOW
        reports_func = "CASH_FLOW"
        list_of_field_default = ['operatingCashflow', 'cashflowFromInvestment', 'cashflowFromFinancing', 'changeInOperatingLiabilities',
                                 'changeInOperatingAssets', 'changeInCashAndCashEquivalents']

    url = f'https://www.alphavantage.co/query?function={reports_func}&symbol={ticker}&apikey={config.AV_KEY}'
    r = requests.get(url)
    data = r.json()
    # st.write(data)
    # st.write(len(data))

#  Choose quarterly or annual reports
    reportsPeriod = st.radio("Choose quarterly or annual reports to show", ("Quarterly Reports", "Annual Reports"))
# number of periods: for quarters - set number by slider, for annual - get all available reports
    if reportsPeriod == "Quarterly Reports":
        periodNumber = number_quarter
        analyse_data = data["quarterlyReports"][0:periodNumber]

    elif reportsPeriod == "Annual Reports":
        periodNumber = len(data["annualReports"])
        analyse_data = data["annualReports"][0:periodNumber]


    #analyse_data = data["quarterlyReports"][0:periodNumber]
    #st.write(analyse_data)
    analyse_data_keys = list(analyse_data[0].keys())
    #st.write(analyse_data_keys)

    df_analyse_data = pd.DataFrame(columns=['Reporting date', 'Indicator', 'Value'])
    for i in range(0, periodNumber):
        for key in analyse_data_keys[1:]:
            #st.write(analyse_data[i][key])
            df_analyse_data = df_analyse_data.append({'Reporting date': datetime.strptime(analyse_data[i]['fiscalDateEnding'], "%Y-%m-%d").date(), 'Indicator': key, 'Value': analyse_data[i][key]}, ignore_index=True)



    df_pivot = df_analyse_data.pivot(index='Indicator', columns='Reporting date', values='Value')
    df_pivot.replace(to_replace='None', value=0, inplace=True)
    df_pivot.sort_index(axis=1, ascending=False, inplace=True)
    df_pivot.loc[df_pivot.index != 'reportedCurrency'] = df_pivot.loc[df_pivot.index != 'reportedCurrency'].astype('float64') / 1000000
    with st.beta_expander(f"Show {reports} dataframe"):
        st.dataframe(df_pivot)

    #st.write(df_pivot.transpose())
    df_pivot_T = df_pivot.transpose().reset_index()
    #st.write(df_pivot_T)
    st.text(""
            ""
            "")

    #st.write(alt.Chart(df_pivot_T).mark_bar().encode(alt.X('Reporting date:O', axis=alt.Axis(labelAngle=-45)), y='totalRevenue:Q', color='totalRevenue').properties(width=400, height=200))

    with st.beta_expander(f"Show {reports} visualization"):

        # list_of_field_default = ['totalRevenue', 'grossProfit', 'ebitda', 'operatingIncome', 'incomeBeforeTax', 'netIncome']
        list_of_field = st.multiselect("Select metrics to visualize: ", df_pivot_T.columns[1:].to_list(), default=list_of_field_default)

        for field in list_of_field:
            col1, col2 = st.beta_columns([2, 5])
            with col1:
                st.subheader(field)
            with col2:
                str_y = field + ':Q'
                st.write(alt.Chart(df_pivot_T).mark_bar().encode(alt.X('Reporting date:O', axis=alt.Axis(labelAngle=-45)),
                y=str_y, tooltip=field, color=alt.condition(f"datum.{field} > 0", alt.value('darkred'), alt.value('orange'))).properties(width=400, height=200).configure_axis(disable=True).configure_view(stroke=None))


# ----------------------Tinkoff Invest---------------------------------------


if option == "Tinkoff Invest":
    client = tinvest.SyncClient(config.TCS_API_token)  # create tinvest client
    accounts = client.get_accounts().payload.accounts # get all tcs accounts

    connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                                  password=config.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #st.write(accounts)

# Select time period for exploring operations
    #start_date = datetime(2021, 8, 1)
    input_start_date = st.date_input("Please input start of period for exploring operations: ", value=datetime(2021, 8, 1), min_value=datetime(2010, 1, 1))
    input_end_date = st.date_input("Please input end of period for exploring operations: ", value=datetime.today(), min_value=datetime(2010, 1, 1))
    start_date = datetime.combine(input_start_date, datetime.min.time())
    end_date = datetime.combine(input_end_date, datetime.min.time())
    #st.write(positions)

# Add selectbox for choose one of the accounts or "Combined" option

    selected_acc = st.selectbox("Please choose account for FIFO analysis: ",
                                ["Tinkoff (id 2029092513)", "TinkoffIis (id 2055779942)", "Combined"])

# Selectbox Done ########################################################################


# get positions by each accounts

    portfolios = []                                                         # list of portfolios
    portfolio_combined = pd.DataFrame()
    with st.beta_expander("Show portfolios"):

        # for acc, i in zip(accounts, range(len(accounts))):                  # run get_positions_by_acc for each portfolio
        #     st.write("Broker account type = ", acc.broker_account_type)     # Render on the page broker_account_type
        #     st.write("Broker account id = ", acc.broker_account_id)         # and broker_account_id
        #     portfolios.append(pd.DataFrame())
        #     portfolios[i] = tcs.get_positions_by_acc(acc.broker_account_id, client)           # get portfolio by broker_account_id and save
        #     portfolio_combined.append(portfolios[i], ignore_index=True)
        #     #st.dataframe(portfolios[i])

        portfolio_iis = tcs.get_positions_by_acc('2055779942', client)          # get portfolio by broker_account_id and save
        portfolio_simple = tcs.get_positions_by_acc('2029092513', client)
        portfolio_combined = portfolio_combined.append(portfolio_iis, ignore_index=True).append(portfolio_simple, ignore_index=True)

        if selected_acc == "Tinkoff (id 2029092513)":
            st.write("Broker account type = Tinkoff")                       # Render on the page broker_account_type
            st.write("Broker account id = 2029092513")                      # and broker_account_id
            st.dataframe(portfolio_simple)

        elif selected_acc == "TinkoffIis (id 2055779942)":
            st.write("Broker account type = TinkoffIis")
            st.write("Broker account id = 2055779942")
            st.dataframe(portfolio_iis)

        elif selected_acc == "Combined":
            st.dataframe(portfolio_combined)


# get list of all tickers in our portfolios
    ticker_list = []

    for n in range(portfolio_combined.shape[0]):
        if list(portfolio_combined.Ticker)[n] not in ticker_list:
            ticker_list.append(list(portfolio_combined.Ticker)[n])

# add 'All' option for selectbox
    ticker_list_with_All = []
    ticker_list_with_All = ticker_list
    ticker_list_with_All.append('All')

    selected_ticker = st.selectbox("Select ticker for FIFO analysis: ", options=ticker_list_with_All)
    figi_by_ticker = client.get_market_search_by_ticker(selected_ticker).payload.instruments[0].figi


# get list of operations separated by operation type


    with st.beta_expander("Show operations in json"):


# -----------------------------------------------------------
# get operations depending on the selected account and ticker
# -----------------------------------------------------------
        if selected_acc == "Tinkoff (id 2029092513)":
            st.write("Broker account type = Tinkoff")
            st.write("Broker account id = 2029092513")
            if selected_ticker != 'All':
                operations = client.get_operations(from_=start_date, to=end_date, figi=figi_by_ticker, broker_account_id='2029092513').payload
                #st.write(json.loads(operations.json()))
                #st.write(operations.json())
            else:
                operations = client.get_operations(from_=start_date, to=end_date, broker_account_id='2029092513').payload


        elif selected_acc == "TinkoffIis (id 2055779942)":
            st.write("Broker account type = TinkoffIis")
            st.write("Broker account id = 2055779942")
            if selected_ticker != 'All':
                operations = client.get_operations(from_=start_date, to=end_date, figi=figi_by_ticker, broker_account_id='2055779942').payload
                #st.write(json.loads(operations.json()))
            else:
                operations = client.get_operations(from_=start_date, to=end_date, broker_account_id='2055779942').payload

        elif selected_acc == "Combined":
            if selected_ticker != 'All':
                operations_simple = client.get_operations(from_=start_date, to=end_date, figi=figi_by_ticker,
                                                   broker_account_id='2029092513').payload
                operations_iis = client.get_operations(from_=start_date, to=end_date, figi=figi_by_ticker,
                                                          broker_account_id='2055779942').payload
                operations = operations_simple.copy(exclude=None)
                operations.operations.extend(operations_iis.operations)
                #st.write(json.loads(operations.json()))

            else:
                operations_simple = client.get_operations(from_=start_date, to=end_date,
                                                          broker_account_id='2029092513').payload
                operations_iis = client.get_operations(from_=start_date, to=end_date,
                                                       broker_account_id='2055779942').payload
                operations = operations_simple.copy(exclude=None)
                operations.operations.append(operations_iis.operations)
                #st.write(json.loads(operations.json()))
# -----------------------------------------------------------------------


        list_buy = []
        list_sell = []
        list_br_commission = []
        list_dvd = []
        list_margin = []
        list_other_oper = []
        list_payIn = []
        list_service = []
        list_payOut = []
        list_taxBack = []
        list_taxDvd = []
        list_buyCard = []  # buy cyrrencys ????

        dict_operation_types = {'BrokerCommission': list_br_commission, 'Sell': list_sell, 'Buy': list_buy,
                                'Dividend': list_dvd, 'MarginCommission': list_margin, 'PayIn': list_payIn,
                                'ServiceCommission': list_service, 'PayOut': list_payOut, 'TaxBack': list_taxBack,
                                'TaxDividend': list_taxDvd, 'BuyCard': list_buyCard, 'Other': list_other_oper}


# split_operations_by_type(operations, dict)

        dict_operation_types = tcs.split_operations_by_type(operations.operations, dict_operation_types)  # returns a filled dictionary

# Show operations by type
        for op_type in dict_operation_types.keys():
            st.subheader(f"{op_type} by ticker {selected_ticker}")
            list_op = dict_operation_types.get(op_type)
            for i in range(len(list_op)):
                st.write(json.loads(list_op[i].json()))


# FIFO by Ticker, start from 2019-01-01
    with st.beta_expander(f"FIFO by ticker {selected_ticker}"):
        if selected_ticker != "All":

            df_buy_sell = pd.DataFrame(columns=['operation_type', 'date', 'figi', 'ticker', 'price', 'currency', 'payment', 'quantity_executed'])
            list_buy_sell = list_buy
            if len(list_sell) > 0:
                list_buy_sell.extend(list_sell)
            temp = json.loads(list_buy_sell[i].json())
            #st.write(temp.get('commission'))
            #st.write(list_buy_sell)

            # fill Buy Sell table
            for i in range(len(list_buy_sell)):
                #st.write("Step number  ", i)

                temp = json.loads(list_buy_sell[i].json())
                if temp.get('status') == 'Done':

                    df_buy_sell = df_buy_sell.append({'operation_type': temp.get('operation_type'), 'date': temp.get('date'),
                                                      'figi': temp.get('figi'), 'ticker': selected_ticker, 'price': temp.get('price'),
                                                      'currency': temp.get('currency'), 'payment': temp.get('payment'),
                                                      'quantity_executed': temp.get('quantity_executed')}, ignore_index=True)

            df_buy_sell = df_buy_sell.sort_values(by='date', ignore_index=True)
            st.dataframe(df_buy_sell)

# Create deque for FIFO
            deque_fifo = deque()
            df_fifo_table = pd.DataFrame(columns=['buy_operation', 'buy_date', 'figi', 'ticker', 'buy_price',
                                                  'buy_quantity', 'currency', 'sell_operation', 'sell_date',
                                                  'sell_price', 'sell_quantity'])
            action_dict = {}
            sell_counter = 0
            for row_number in range(df_buy_sell.shape[0]):
                if df_buy_sell.operation_type.iloc[row_number] == 'Buy':

                    action_dict.update({'operation_type': df_buy_sell.operation_type.iloc[row_number],
                                        'date': df_buy_sell.date.iloc[row_number],
                                        'figi': df_buy_sell.figi.iloc[row_number],
                                        'ticker': df_buy_sell.ticker.iloc[row_number],
                                        'price': df_buy_sell.price.iloc[row_number],
                                        'currency': df_buy_sell.currency.iloc[row_number]
                                        })
                    for i in range(df_buy_sell.quantity_executed.iloc[row_number]):
                        deque_fifo.append(action_dict)
                    df_fifo_table = df_fifo_table.append({'buy_operation': action_dict.get('operation_type'),
                                          'buy_date': action_dict.get('date'),
                                         'figi': action_dict.get('figi'),
                                         'ticker': action_dict.get('ticker'),
                                         'buy_price': action_dict.get('price'),
                                          'buy_quantity': df_buy_sell.quantity_executed.iloc[row_number],
                                          'currency': action_dict.get('currency')
                                          }, ignore_index=True)
                    action_dict = {}

                elif df_buy_sell.operation_type.iloc[row_number] == 'Sell':
                    for i in range(df_buy_sell.quantity_executed.iloc[row_number]):
                        action_dict = deque_fifo.pop()

                    #sell_counter = sell_counter + 1
                    #st.write(action_dict)

                    #st.write(df_fifo_table.at[sell_counter - 1, 'sell_operation'])
                    df_fifo_table['sell_operation'] = df_fifo_table['sell_operation'].astype('str')
                    df_fifo_table['sell_date'] = df_fifo_table['sell_date'].astype('str')
                    df_fifo_table['sell_price'] = df_fifo_table['sell_price'].astype('float')
                    df_fifo_table['buy_quantity'] = df_fifo_table['buy_quantity'].astype('int')


                    if df_fifo_table.at[sell_counter, 'buy_quantity'] == df_buy_sell.quantity_executed.iloc[row_number]:
                        df_fifo_table.at[sell_counter, 'sell_quantity'] = df_buy_sell.quantity_executed.iloc[row_number]
                        df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                        df_fifo_table.at[sell_counter, 'sell_date'] = df_buy_sell.date.iloc[row_number]
                        df_fifo_table.at[sell_counter, 'sell_price'] = df_buy_sell.price.iloc[row_number]
                        sell_counter += 1

                    elif df_fifo_table.at[sell_counter, 'buy_quantity'] > df_buy_sell.quantity_executed.iloc[row_number]:


                        #insert buy  saldo
                        #new_index = list(range(0, sell_counter)).extend(list(range(sell_counter, df_fifo_table.shape[0] + 1)))  # create new index
                        # new_index_part_1 = [i for i in range(0, sell_counter)]
                        # new_index_part_2 = [n for n in range(sell_counter+1, df_fifo_table.shape[0] + 1)]
                        # new_index_part_1.extend(new_index_part_2)
                        #
                        # #df_fifo_table = df_fifo_table.reindex(new_index_part_1)  # reindex dataframe
                        # df_fifo_table.index = new_index_part_1
                        #
                        # df_fifo_table.loc[sell_counter] = pd.Series(df_fifo_table.loc[sell_counter - 1])
                        #
                        # df_fifo_table = df_fifo_table.sort_index()
                        #
                        #
                        # df_fifo_table.at[sell_counter - 1, 'sell_operation'] = 'Sell'
                        # df_fifo_table.at[sell_counter - 1, 'sell_date'] = df_buy_sell.date.iloc[row_number]
                        # df_fifo_table.at[sell_counter - 1, 'sell_price'] = df_buy_sell.price.iloc[row_number]
                        #
                        # df_fifo_table.at[sell_counter - 1, 'sell_quantity'] = df_buy_sell.quantity_executed.iloc[row_number]  # set the sell_quantity
                        #
                        # df_fifo_table.at[sell_counter, 'buy_quantity'] = df_fifo_table.at[sell_counter - 1, 'buy_quantity'] - df_fifo_table.at[sell_counter - 1, 'sell_quantity']   # residual to buy
                        # df_fifo_table.at[sell_counter - 1, 'buy_quantity'] = df_fifo_table.at[sell_counter - 1, 'sell_quantity']  # change buy_quantity = sell_quantity

                        df_fifo_table = tcs.split_buy_fifo(sell_counter, df_fifo_table, df_buy_sell.date.iloc[row_number], df_buy_sell.price.iloc[row_number], df_buy_sell.quantity_executed.iloc[row_number])
                        sell_counter += 1


                    elif df_fifo_table.at[sell_counter, 'buy_quantity'] < df_buy_sell.quantity_executed.iloc[row_number]:
                        quantity_temp = df_buy_sell.quantity_executed.iloc[row_number]
                        while df_fifo_table.at[sell_counter, 'buy_quantity'] < quantity_temp:

                            df_fifo_table.at[sell_counter, 'sell_quantity'] = df_fifo_table.at[sell_counter, 'buy_quantity']
                            df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                            df_fifo_table.at[sell_counter, 'sell_date'] = df_buy_sell.date.iloc[row_number]
                            df_fifo_table.at[sell_counter, 'sell_price'] = df_buy_sell.price.iloc[row_number]
                            quantity_temp -= df_fifo_table.at[sell_counter, 'sell_quantity']
                            sell_counter += 1

                        if df_fifo_table.at[sell_counter, 'buy_quantity'] == quantity_temp:
                            df_fifo_table.at[sell_counter, 'sell_quantity'] = quantity_temp
                            df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                            df_fifo_table.at[sell_counter, 'sell_date'] = df_buy_sell.date.iloc[row_number]
                            df_fifo_table.at[sell_counter, 'sell_price'] = df_buy_sell.price.iloc[row_number]
                            sell_counter += 1

                        elif df_fifo_table.at[sell_counter, 'buy_quantity'] > quantity_temp:
                            df_fifo_table = tcs.split_buy_fifo(sell_counter, df_fifo_table,
                                                               df_buy_sell.date.iloc[row_number],
                                                               df_buy_sell.price.iloc[row_number],
                                                               quantity_temp)
                            sell_counter += 1





            df_fifo_table['Profit'] = df_fifo_table.buy_quantity * (df_fifo_table.sell_price - df_fifo_table.buy_price).astype('float').round(4)

            current_profit = 0
            current_profit_RUB = 0
            expected_profit = 0
            expected_profit_RUB = 0
            df_fifo_table = df_fifo_table.assign(buy_price_RUB='', sell_price_RUB='', Profit_RUB='', ex_rates_buy_date='', ex_rates_sell_date='')
            for i in range(df_fifo_table.shape[0]):
                if str(df_fifo_table.loc[i, 'buy_date']) != 'nan':
                    char_code = df_fifo_table.loc[i, 'currency']
                    buy_price = df_fifo_table.loc[i, 'buy_price']
                    date = datetime.strptime(df_fifo_table.loc[i, 'buy_date'], '%Y-%m-%dT%H:%M:%S.%f%z').date()
                    df_fifo_table.loc[i, 'ex_rates_buy_date'] = cbr.get_currency_value(cursor, char_code, date)
                    df_fifo_table.loc[i, 'buy_price_RUB'] = round(buy_price * cbr.get_currency_value(cursor, char_code, date), 2)
                if str(df_fifo_table.loc[i, 'sell_date']) != 'nan':
                    char_code = df_fifo_table.loc[i, 'currency']
                    sell_price = df_fifo_table.loc[i, 'sell_price']
                    date = datetime.strptime(df_fifo_table.loc[i, 'sell_date'], '%Y-%m-%dT%H:%M:%S.%f%z').date()
                    df_fifo_table.loc[i, 'ex_rates_sell_date'] = cbr.get_currency_value(cursor, char_code, date)
                    df_fifo_table.loc[i, 'sell_price_RUB'] = round(sell_price * cbr.get_currency_value(cursor, char_code, date), 2)

                if str(df_fifo_table.loc[i, 'buy_date']) != 'nan' and str(df_fifo_table.loc[i, 'sell_date']) != 'nan':
                    df_fifo_table.loc[i, 'Profit_RUB'] = round((df_fifo_table.loc[i, 'sell_price_RUB'] - df_fifo_table.loc[i, 'buy_price_RUB']) * df_fifo_table.loc[i, 'buy_quantity'], 2)
                    current_profit += df_fifo_table.loc[i, 'Profit']
                    current_profit_RUB += df_fifo_table.loc[i, 'Profit_RUB']
                else:
                    sell_price = float(client.get_market_orderbook(figi_by_ticker, depth=20).payload.last_price)
                    date = datetime.today().date()
                    char_code = df_fifo_table.loc[i, 'currency']
                    df_fifo_table.loc[i, 'sell_price'] = sell_price
                    df_fifo_table.loc[i, 'ex_rates_sell_date'] = cbr.get_currency_value(cursor, char_code, date)
                    df_fifo_table.loc[i, 'sell_price_RUB'] = round(sell_price * cbr.get_currency_value(cursor, char_code, date), 2)
                    df_fifo_table.loc[i, 'Profit'] = df_fifo_table.loc[i, 'buy_quantity'] * (df_fifo_table.loc[i, 'sell_price'] - df_fifo_table.loc[i, 'buy_price']).astype('float').round(4)
                    df_fifo_table.loc[i, 'Profit_RUB'] = round((df_fifo_table.loc[i, 'sell_price_RUB'] - df_fifo_table.loc[i, 'buy_price_RUB']) * df_fifo_table.loc[i, 'buy_quantity'], 2)
                    expected_profit += df_fifo_table.loc[i, 'Profit']
                    expected_profit_RUB += df_fifo_table.loc[i, 'Profit_RUB']



            st.dataframe(df_fifo_table)



            st.subheader(f"Current Profit by {selected_ticker} in {df_fifo_table.loc[i, 'currency']} and RUB: ")
            st.write(f'{round(current_profit, 2)} {df_fifo_table.loc[i, "currency"]}')
            st.write(f'{round(current_profit_RUB, 2)}  RUB')
            st.subheader("")

            st.subheader(f"Expected (additional) Profit by {selected_ticker} in {df_fifo_table.loc[i, 'currency']} and RUB: ")
            st.write(f'{round(expected_profit, 2)} {df_fifo_table.loc[i, "currency"]}')
            st.write(f'{round(expected_profit_RUB, 2)}  RUB')


            file_name = f'fifo_{selected_acc}_{selected_ticker}_{end_date.strftime("%d-%m-%Y")}.csv'
            if st.button(f"Save report to csv file {file_name}?"):

                df_fifo_table.to_csv(file_name)

                Profit_info = {'Current Profit': round(current_profit, 2),
                               'Current Profit RUB': round(current_profit_RUB, 2),
                               'Expected (additional) Profit': round(expected_profit, 2),
                               'Expected (additional) Profit RUB': round(expected_profit_RUB, 2)}
                with open(file_name, 'a', newline='') as f:
                    columns = ['Current Profit', 'Current Profit RUB', 'Expected (additional) Profit',
                               'Expected (additional) Profit RUB']
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer_space = csv.writer(f)
                    writer_space.writerow(['\n', '\n', '\n'])
                    writer.writeheader()
                    writer.writerow(Profit_info)






        else:
            st.subheader("Please choose ticker")





