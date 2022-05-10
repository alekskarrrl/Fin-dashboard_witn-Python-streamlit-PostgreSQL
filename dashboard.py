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
import psycopg2, psycopg2.extras
import altair as alt
import math
import tinvest
import csv

import tinkoff_invest as tcs
import cbrf_currencies as cbr
import wallstreetbets as wsb
import fundamental
import config

# proxie={'https' : 'https://15.188.82.98:80'}
proxie = {'https': 'https://103.138.40.202:8080'}

st.image("top_img.jpg")

st.sidebar.title("Options")

option = st.sidebar.selectbox("Select module",
                              ("Wallstreetbets", "Tinkoff Invest", "Fundamental Data"))
# st.header(option)


connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                              password=config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

# ----------------wallstreetbets -------------------------------------------------------

if option == "Wallstreetbets":
    st.subheader("Wallstreetbets dashboard")

    # By clicking on the button, we load posts from wsb into the database for the last n_last_days days

    n_last_days = st.sidebar.slider("Load mentions from wsb to db for N last days: ", 1, 30)
    loadBtn = st.sidebar.button("Load data", "loadBtn")

    if loadBtn:
        n_last_days_to_load = n_last_days
        with st.spinner("Loading in progress ..."):
            wsb.load_wsb(n_last_days_to_load)
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
    # top_counts = px.bar(df_top, y='symbol', x='counts', orientation='h', color='counts')
    # st.plotly_chart(top_counts, use_container_width=True)

    st.write(alt.Chart(df_top).mark_bar().encode(alt.Y(field='symbol', type='nominal', sort='x'), x='counts',
                                                 color='counts').properties(width=800, height=400))

    st.write(wsb.wsb_from_db(ticker))  # Method for Select from DB and displaying posts from wsb by ticker


# -------------------Fundamental Data-------------------------------------------------


if option == "Fundamental Data":
    st.subheader("Fundamental Data")
    st.markdown(""" *The data on this page was obtained using
     the [Alpha Vantage API.](https://www.alphavantage.co/documentation/)*""")

    # --------Enter the stock ticker that we want to analyze and the number of reporting quarters
    ticker = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5).upper()
    number_quarter = st.sidebar.slider("Set number of quarters to analyse: ", 1, 15, 5)

    # ----- OVERVIEW  BLOCK ________________________________
    fundamental.show_header(ticker)
    st.subheader("")
    with st.beta_expander("Company Description: "):
        fundamental.show_description(ticker)

    fundamental.show_ratios(ticker)
    st.subheader("")

    # ----- Reports DataFrame ________________________________

    # Select Balance Sheet, Income Statement or Cash Flow
    reports = st.selectbox("Select Balance Sheet, Income Statement or Financial Ratios",
                           ('Balance Sheet', 'Income Statement', 'Cash Flow'))

    # --------------Choose quarterly or annual reports------------------------------
    reportsPeriod = st.radio("Choose quarterly or annual reports to show", ("Quarterly Reports", "Annual Reports"))

    if reportsPeriod == "Quarterly Reports":
        period = 'quarter'

    elif reportsPeriod == "Annual Reports":
        period = 'annual'

    df_pivot = fundamental.dataframe_reports(ticker, reports, number_quarter, period)

    with st.beta_expander(f"Show {reports} dataframe"):
        st.dataframe(df_pivot)

    st.text(""
            ""
            "")

    # ------------------Reports visualization ------------------------------
    if reports == 'Income Statement':
        list_of_fields_default = ['totalRevenue', 'grossProfit', 'ebitda', 'operatingIncome', 'incomeBeforeTax',
                                  'netIncome']

    elif reports == 'Balance Sheet':
        list_of_fields_default = ['cashAndCashEquivalentsAtCarryingValue', 'totalCurrentAssets', 'totalAssets',
                                  'inventory',
                                  'totalNonCurrentAssets', 'propertyPlantEquipment', 'totalLiabilities',
                                  'totalCurrentLiabilities',
                                  'currentDebt', 'longTermDebt', 'totalNonCurrentLiabilities']
    elif reports == 'Cash Flow':
        list_of_fields_default = ['operatingCashflow', 'cashflowFromInvestment', 'cashflowFromFinancing',
                                  'changeInOperatingLiabilities',
                                  'changeInOperatingAssets', 'changeInCashAndCashEquivalents']

    df_pivot_T = df_pivot.transpose().reset_index()

    with st.beta_expander(f"Show {reports} visualization"):

        list_of_fields = st.multiselect("Select metrics to visualize: ", df_pivot_T.columns[1:].to_list(),
                                        default=list_of_fields_default)

        fundamental.show_reports_visualization(list_of_fields, df_pivot_T)

# ----------------------Tinkoff Invest---------------------------------------

if option == "Tinkoff Invest":
    TCS_client = tinvest.SyncClient(config.TCS_API_token)  # create tinvest client
    accs_info = tcs.get_user_accs_info(TCS_client)

    connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER,
                                  password=config.DB_PASS)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    select_acc = ["Combined"]
    for item in accs_info.items():
        str = item[0] + " " + item[1]
        select_acc.append(str)

    # Select time period for exploring operations
    input_start_date = st.date_input("Please input start of period for exploring operations: ",
                                     value=datetime(2020, 1, 1), min_value=datetime(2010, 1, 1))
    input_end_date = st.date_input("Please input end of period for exploring operations: ", value=datetime.today(),
                                   min_value=datetime(2010, 1, 1))
    start_date = datetime.combine(input_start_date, datetime.min.time())
    end_date = datetime.combine(input_end_date, datetime.max.time())

    # Add selectbox for choose one of the accounts or "Combined" option

    selected_acc = st.selectbox("Please choose account for FIFO analysis: ", select_acc)

    portfolio = pd.DataFrame()
    with st.beta_expander("Show portfolios"):
        str_query = """Select distinct(symbol) from operations, stock Where stock_id is not null and 
                        stock_id = stock.id"""

        if selected_acc != "Combined":
            acc_id = selected_acc.split(" ")[0]
            portfolio = tcs.get_positions_by_acc(acc_id, TCS_client)  # get portfolio by broker_account_id and save
            st.write(f"Broker account type = {accs_info.get(acc_id)}")  # Render on the page broker_account_type
            st.write(f"Broker account id = {acc_id}")  # and broker_account_id
            st.dataframe(portfolio)
            st.subheader("Cash position: ")
            st.dataframe(tcs.get_currency_balance_by_acc(acc_id, TCS_client))
            str_query = """Select distinct(symbol) from operations, stock Where stock_id is not null and stock_id = stock.id and account_id = %s"""
            cursor.execute(str_query, (acc_id,))

        elif selected_acc == "Combined":
            for item in accs_info.items():
                portfolio = portfolio.append(tcs.get_positions_by_acc(item[0], TCS_client), ignore_index=True)
            st.dataframe(portfolio)
            cursor.execute(str_query)

        fetched_rows = cursor.fetchall()
        ticker_list = []
        for row in fetched_rows:
            ticker_list.append(row[0])

    # ----------------- Operations analysis ---------------------------------------

    # add 'All' option for selectbox
    ticker_list_with_All = []
    ticker_list_with_All = ticker_list
    ticker_list_with_All.append('All')

    selected_ticker = st.selectbox("Select ticker for FIFO analysis: ", options=ticker_list_with_All)
    figi_by_ticker = TCS_client.get_market_search_by_ticker(selected_ticker).payload.instruments[0].figi

    with st.beta_expander("Show reports by operations type"):
        operation_types_list = ['BrokerCommission', 'Sell', 'Buy', 'Dividend', 'MarginCommission', 'PayIn',
                                'ServiceCommission', 'PayOut', 'TaxBack', 'TaxDividend', 'BuyCard', 'Other']

        selected_type = st.selectbox("Select the type of transactions to view information for the selected period: ",
                                     options=operation_types_list)
        df_report = pd.DataFrame(
            columns=['operation_type', 'account_id', 'account_type', 'date', 'operation_id', 'commission',
                     'currency', 'ticker', 'stock_name', 'instrument_type', 'price', 'quantity', 'quantity_executed',
                     'payment'])

        basic_query = """ SELECT operation_type, account_id, broker_accounts.type as account_type, date, operations.id, commission,
                                char_code, symbol, stock.name, instrument_type, price, quantity, quantity_executed, payment
                        FROM currencies_catalog, broker_accounts, operations left join  stock on stock_id = stock.id
                        WHERE operation_type = %s and operations.currency = currencies_catalog.currency_id 
                            and account_id = broker_accounts.id and date >= %s and date <= %s
                        GROUP BY operation_type, account_id, account_type, date, operations.id, commission, char_code, symbol, 
                                stock.name, instrument_type, price, quantity, quantity_executed, payment
                        ORDER BY account_id, date;"""
        query_filter_acc = """ SELECT operation_type, account_id, broker_accounts.type as account_type, date, operations.id, commission,
                                char_code, symbol, stock.name, instrument_type, price, quantity, quantity_executed, payment
                        FROM currencies_catalog, broker_accounts, operations left join  stock on stock_id = stock.id
                        WHERE operation_type = %s and operations.currency = currencies_catalog.currency_id 
                            and account_id = broker_accounts.id and date >= %s and date <= %s and account_id = %s
                        GROUP BY operation_type, account_id, account_type, date, operations.id, commission, char_code, symbol, 
                                stock.name, instrument_type, price, quantity, quantity_executed, payment
                        ORDER BY account_id, date;"""
        query_filter_ticker = """ SELECT operation_type, account_id, broker_accounts.type as account_type, date, operations.id, commission,
                                char_code, symbol, stock.name, instrument_type, price, quantity, quantity_executed, payment
                        FROM currencies_catalog, broker_accounts, operations left join  stock on stock_id = stock.id
                        WHERE operation_type = %s and operations.currency = currencies_catalog.currency_id 
                            and account_id = broker_accounts.id and date >= %s and date <= %s and symbol = %s
                        GROUP BY operation_type, account_id, account_type, date, operations.id, commission, char_code, symbol, 
                                stock.name, instrument_type, price, quantity, quantity_executed, payment
                        ORDER BY account_id, date;"""
        query_filter_acc_ticker = """ SELECT operation_type, account_id, broker_accounts.type as account_type, date, operations.id, commission,
                                char_code, symbol, stock.name, instrument_type, price, quantity, quantity_executed, payment
                        FROM currencies_catalog, broker_accounts, operations left join  stock on stock_id = stock.id
                        WHERE operation_type = %s and operations.currency = currencies_catalog.currency_id 
                            and account_id = broker_accounts.id and date >= %s and date <= %s and account_id = %s and symbol = %s
                        GROUP BY operation_type, account_id, account_type, date, operations.id, commission, char_code, symbol, 
                                stock.name, instrument_type, price, quantity, quantity_executed, payment
                        ORDER BY account_id, date;"""
        if selected_acc != "Combined":
            acc_id = selected_acc.split(" ")[0]

            if selected_ticker != 'All':
                cursor.execute(query_filter_acc_ticker, (selected_type, start_date, end_date, acc_id, selected_ticker))
            else:
                cursor.execute(query_filter_acc, (selected_type, start_date, end_date, acc_id))

        elif selected_acc == "Combined":
            if selected_ticker != 'All':
                cursor.execute(query_filter_ticker, (selected_type, start_date, end_date, selected_ticker))
            else:
                cursor.execute(basic_query, (selected_type, start_date, end_date))

        fetched_output = cursor.fetchall()
        for row in fetched_output:
            df_report = df_report.append(
                {'operation_type': row[0], 'account_id': row[1], 'account_type': row[2], 'date': row[3],
                 'operation_id': row[4], 'commission': row[5], 'currency': row[6], 'ticker': row[7],
                 'stock_name': row[8], 'instrument_type': row[9], 'price': row[10],
                 'quantity': row[11], 'quantity_executed': row[12], 'payment': row[13]}, ignore_index=True)
        st.write(df_report)

    with st.beta_expander(f"FIFO by ticker {selected_ticker}"):
        if selected_ticker != 'All':

            # Create df_sell_buy table from DB
            df_sell_buy_db = pd.DataFrame(
                columns=['operation_type', 'date', 'figi', 'ticker', 'price', 'currency', 'payment',
                         'quantity_executed'])
            query_sell_buy_filter_acc = """ Select operation_type, date, figi, symbol, price, char_code, payment, quantity_executed
                                    from currencies_catalog, operations, stock
                                    Where operations.currency = currencies_catalog.currency_id and stock_id = stock.id and 
                                    operation_type in ('Buy', 'Sell') and date >= %s and date <= %s and symbol = %s and account_id = %s and 
                                    quantity_executed > 0
                                    Order by date asc """
            query_sell_buy = """ Select operation_type, date, figi, symbol, price, char_code, payment, quantity_executed
                                    from currencies_catalog, operations, stock
                                    Where operations.currency = currencies_catalog.currency_id and stock_id = stock.id and 
                                    operation_type in ('Buy', 'Sell') and date >= %s and date <= %s and symbol = %s and 
                                    quantity_executed > 0
                                    Order by date asc """

            if selected_acc != "Combined":
                acc_id = selected_acc.split(" ")[0]
                cursor.execute(query_sell_buy_filter_acc, (start_date, end_date, selected_ticker, acc_id))

            elif selected_acc == "Combined":
                cursor.execute(query_sell_buy, (start_date, end_date, selected_ticker))

            fetched_sell_buy = cursor.fetchall()
            for row in fetched_sell_buy:
                df_sell_buy_db = df_sell_buy_db.append({'operation_type': row[0], 'date': row[1], 'figi': row[2],
                                                        'ticker': row[3], 'price': row[4], 'currency': row[5],
                                                        'payment': row[6],
                                                        'quantity_executed': row[7]}, ignore_index=True)

            st.subheader("Buy and Sell table: ")

            st.dataframe(df_sell_buy_db)

            # FIFO table

            df_fifo_table = pd.DataFrame(columns=['buy_operation', 'buy_date', 'figi', 'ticker', 'buy_price',
                                                     'buy_quantity', 'currency', 'sell_operation', 'sell_date',
                                                     'sell_price', 'sell_quantity', 'account'])

            sell_counter = 0
            for i, row in df_sell_buy_db.iterrows():
                if row['operation_type'] == "Buy":
                    buy_operation = row['operation_type']
                    buy_date = row['date']
                    figi = row['figi']
                    ticker = row['ticker']
                    buy_price = float(row['price'])
                    buy_quantity = row['quantity_executed']
                    currency = row['currency']
                    df_fifo_table = df_fifo_table.append(
                        {'buy_operation': buy_operation, 'buy_date': buy_date, 'figi': figi,
                         'ticker': ticker, 'buy_price': buy_price, 'buy_quantity': buy_quantity,
                         'currency': currency, 'account': selected_acc}, ignore_index=True)

                elif row['operation_type'] == "Sell":
                    df_fifo_table['sell_operation'] = df_fifo_table['sell_operation'].astype('str')
                    df_fifo_table['sell_price'] = df_fifo_table['sell_price'].astype('float')
                    df_fifo_table['buy_quantity'] = df_fifo_table['buy_quantity'].astype('int')

                    if df_fifo_table.at[sell_counter, 'buy_quantity'] == row['quantity_executed']:
                        df_fifo_table.at[sell_counter, 'sell_quantity'] = row['quantity_executed']
                        df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                        df_fifo_table.at[sell_counter, 'sell_date'] = row['date']
                        df_fifo_table.at[sell_counter, 'sell_price'] = row['price']
                        sell_counter += 1

                    elif df_fifo_table.at[sell_counter, 'buy_quantity'] > row['quantity_executed']:

                        # df_fifo_table = tcs.split_buy_fifo(sell_counter, df_fifo_table,
                        #                                       row['date'], row['price'], row['quantity_executed'])

                        df_fifo_table = tcs.split_buy_fifo(sell_counter, df_fifo_table)

                        df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                        df_fifo_table.at[sell_counter, 'sell_date'] = row['date']
                        df_fifo_table.at[sell_counter, 'sell_price'] = row['price']
                        df_fifo_table.at[sell_counter, 'sell_quantity'] = row['quantity_executed']
                        df_fifo_table.at[sell_counter + 1, 'buy_quantity'] = \
                            df_fifo_table.at[sell_counter, 'buy_quantity'] - df_fifo_table.at[sell_counter, 'sell_quantity']         # residual to buy
                        df_fifo_table.at[sell_counter, 'buy_quantity'] = \
                            df_fifo_table.at[sell_counter, 'sell_quantity']  # change buy_quantity = sell_quantity
                        sell_counter += 1


                    elif df_fifo_table.at[sell_counter, 'buy_quantity'] < row['quantity_executed']:
                        quantity_temp = row['quantity_executed']
                        while df_fifo_table.at[sell_counter, 'buy_quantity'] < quantity_temp:
                            df_fifo_table.at[sell_counter, 'sell_quantity'] = df_fifo_table.at[
                                sell_counter, 'buy_quantity']
                            df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                            df_fifo_table.at[sell_counter, 'sell_date'] = row['date']
                            df_fifo_table.at[sell_counter, 'sell_price'] = row['price']
                            quantity_temp -= df_fifo_table.at[sell_counter, 'sell_quantity']
                            sell_counter += 1

                        if df_fifo_table.at[sell_counter, 'buy_quantity'] == quantity_temp:
                            df_fifo_table.at[sell_counter, 'sell_quantity'] = quantity_temp
                            df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                            df_fifo_table.at[sell_counter, 'sell_date'] = row['date']
                            df_fifo_table.at[sell_counter, 'sell_price'] = row['price']
                            sell_counter += 1

                        elif df_fifo_table.at[sell_counter, 'buy_quantity'] > quantity_temp:
                            # df_fifo_table = tcs.split_buy_fifo(sell_counter, df_fifo_table,
                            #                                       row['date'], row['price'], quantity_temp)

                            df_fifo_table = tcs.split_buy_fifo(sell_counter, df_fifo_table)
                            df_fifo_table.at[sell_counter, 'sell_operation'] = 'Sell'
                            df_fifo_table.at[sell_counter, 'sell_date'] = row['date']
                            df_fifo_table.at[sell_counter, 'sell_price'] = row['price']
                            df_fifo_table.at[sell_counter, 'sell_quantity'] = quantity_temp
                            df_fifo_table.at[sell_counter + 1, 'buy_quantity'] = \
                                df_fifo_table.at[sell_counter, 'buy_quantity'] - df_fifo_table.at[sell_counter, 'sell_quantity']  # residual to buy
                            df_fifo_table.at[sell_counter, 'buy_quantity'] = \
                                df_fifo_table.at[sell_counter, 'sell_quantity']   # change buy_quantity = sell_quantity
                            sell_counter += 1

            df_fifo_table['Profit'] = df_fifo_table.buy_quantity * (
                    df_fifo_table.sell_price - df_fifo_table.buy_price).astype('float').round(4)

            current_profit_db = 0
            current_profit_RUB_db = 0
            expected_profit_db = 0
            expected_profit_RUB_db = 0
            df_fifo_table = df_fifo_table.assign(buy_price_RUB='', sell_price_RUB='', Profit_RUB='',
                                                       ex_rates_buy_date='', ex_rates_sell_date='')

            for i, row in df_fifo_table.iterrows():
                if row['buy_date'] == row['buy_date'] and row['buy_date'] != 'nan':
                    char_code = row['currency']
                    buy_price = row['buy_price']
                    date = row['buy_date']
                    df_fifo_table.loc[i, 'ex_rates_buy_date'] = cbr.get_currency_value(connection, char_code, date) if char_code != 'RUB' else 1
                    df_fifo_table.loc[i, 'buy_price_RUB'] = round(buy_price * df_fifo_table.loc[i, 'ex_rates_buy_date'], 2)
                if row['sell_date'] == row['sell_date'] and row['sell_date'] != 'nan':
                    char_code = row['currency']
                    sell_price = row['sell_price']
                    date = row['sell_date']
                    df_fifo_table.loc[i, 'ex_rates_sell_date'] = cbr.get_currency_value(connection, char_code, date) if char_code != 'RUB' else 1
                    df_fifo_table.loc[i, 'sell_price_RUB'] = round(sell_price * df_fifo_table.loc[i, 'ex_rates_sell_date'], 2)

                if row['buy_date'] != 'nan' and row['buy_date'] == row['buy_date'] and row['sell_date'] != 'nan' and \
                        row['sell_date'] == row['sell_date']:
                    df_fifo_table.loc[i, 'Profit_RUB'] = round(((df_fifo_table.loc[i, 'sell_price_RUB'] -
                                                                    df_fifo_table.loc[i, 'buy_price_RUB']) *
                                                                   df_fifo_table.loc[i, 'buy_quantity']), 2)
                    current_profit_db += df_fifo_table.loc[i, 'Profit']
                    current_profit_RUB_db += df_fifo_table.loc[i, 'Profit_RUB']
                else:
                    sell_price = float(TCS_client.get_market_orderbook(figi_by_ticker, depth=20).payload.last_price)
                    date = datetime.today()
                    char_code = row['currency']
                    df_fifo_table.loc[i, 'sell_price'] = sell_price
                    df_fifo_table.loc[i, 'ex_rates_sell_date'] = cbr.get_currency_value(connection, char_code, date) if char_code != 'RUB' else 1
                    df_fifo_table.loc[i, 'sell_price_RUB'] = round(sell_price * df_fifo_table.loc[i, 'ex_rates_sell_date'], 2)
                    df_fifo_table.loc[i, 'Profit'] = round(df_fifo_table.loc[i, 'buy_quantity'] *
                                                              (df_fifo_table.loc[i, 'sell_price'] -
                                                               df_fifo_table.loc[i, 'buy_price']), 4)
                    df_fifo_table.loc[i, 'Profit_RUB'] = round((df_fifo_table.loc[i, 'sell_price_RUB'] -
                                                                   df_fifo_table.loc[i, 'buy_price_RUB']) *
                                                                  df_fifo_table.loc[i, 'buy_quantity'], 2)
                    expected_profit_db += df_fifo_table.loc[i, 'Profit']
                    expected_profit_RUB_db += df_fifo_table.loc[i, 'Profit_RUB']

            st.subheader("FIFO table: ")
            st.dataframe(df_fifo_table)

            st.subheader(f"Current Profit by {selected_ticker} in {df_fifo_table.loc[0, 'currency']} and RUB: ")
            st.write(f'{round(current_profit_db, 2)} {df_fifo_table.loc[0, "currency"]}')
            st.write(f'{round(current_profit_RUB_db, 2)}  RUB')
            st.subheader("")

            st.subheader(
                f"Expected (additional) Profit by {selected_ticker} in {df_fifo_table.loc[0, 'currency']} and RUB: ")
            st.write(f'{round(expected_profit_db, 2)} {df_fifo_table.loc[0, "currency"]}')
            st.write(f'{round(expected_profit_RUB_db, 2)}  RUB')

            file_name = f'fifo_{selected_acc}_{selected_ticker}_{end_date.strftime("%d-%m-%Y")}.csv'
            if st.button(f"Save report to csv file {file_name}?"):
                df_fifo_table.to_csv(file_name, sep=';')

                Profit_info = {'Current Profit': round(current_profit_db, 2),
                               'Current Profit RUB': round(current_profit_RUB_db, 2),
                               'Expected (additional) Profit': round(expected_profit_db, 2),
                               'Expected (additional) Profit RUB': round(expected_profit_RUB_db, 2)}
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
