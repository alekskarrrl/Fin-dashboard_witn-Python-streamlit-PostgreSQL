import pandas as pd
from datetime import datetime, date, time
import numpy as np
import math
import requests
import streamlit as st
import altair as alt

import config


@st.cache
def get_overview_data(ticker):
    # ---------------------------------------------
    # Get overview from API.The overview contains a brief description
    # of the company's activities and the main fundamental ratios.
    # ticker - string
    # ---------------------------------------------

    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={config.AV_KEY}'
    r = requests.get(url)
    return r.json()


def show_header(ticker):
    # -----------------------------------------
    # Display the Name, ticker, exchange, currency, country and sector of the company
    # -----------------------------------------
    overview_data = get_overview_data(ticker)
    name = overview_data["Name"]
    symbol = overview_data["Symbol"]
    exchange = overview_data["Exchange"]
    currency = overview_data["Currency"]
    country = overview_data["Country"]
    sector = overview_data["Sector"]

    st.subheader(name)
    st.subheader(symbol + " | " + exchange + " | " + currency + " | "
                 + country + " | " + sector)

    return 0


def show_description(ticker):
    # Display description of the company's activities

    overview_data = get_overview_data(ticker)
    description = overview_data["Description"]
    st.markdown(description)
    return 0


def show_ratios(ticker):
    # ---------------------------------------------
    # Display some fundamental ratios
    # ---------------------------------------------
    overview_data = get_overview_data(ticker)
    r_style = 'text-align:left; color: blue; border-style: solid; border-width: thin; border-color: #3F4E6A; ' \
              'border-radius: 10px; height: 60px; padding: 10px; font-size: 24px; color: #517FE1'

    list_ratios = ['PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'DividendYield', 'EPS', 'ProfitMargin',
                  'DilutedEPSTTM',
                  'AnalystTargetPrice', 'EVToEBITDA', 'PayoutRatio', 'DividendDate']
    dict_ratios = {'PERatio': 'P/E Ratio', 'PEGRatio': 'PEG Ratio', 'BookValue': 'Book Value',
                  'DividendPerShare': 'Dividend Per Share',
                  'DividendYield': 'Dividend Yield', 'EPS': 'EPS', 'ProfitMargin': 'Profit Margin',
                  'DilutedEPSTTM': 'Diluted EPS TTM',
                  'AnalystTargetPrice': 'Analyst Target Price', 'EVToEBITDA': 'EV To EBITDA',
                  'PayoutRatio': 'Payout Ratio', 'DividendDate': 'Dividend Date'}

    for i in range(0, math.ceil(len(list_ratios) / 3)):
        r1, r2, r3 = st.beta_columns(3)


        with r1:
            st.markdown(f"**{dict_ratios[list_ratios[i * 3 + 0]]}**")
            if list_ratios[i * 3 + 0] in overview_data.keys():
                st.markdown(f"<div style ='{r_style}'>{overview_data[list_ratios[i * 3 + 0]]}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style ='{r_style}'> N/A </div>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"**{dict_ratios[list_ratios[i * 3 + 1]]}**")
            if list_ratios[i * 3 + 1] in overview_data.keys():
                st.markdown(f"<div style ='{r_style}'>{overview_data[list_ratios[i * 3 + 1]]}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style ='{r_style}'> N/A </div>", unsafe_allow_html=True)
        with r3:
            st.markdown(f"**{dict_ratios[list_ratios[i * 3 + 2]]}**")
            if list_ratios[i * 3 + 2] in overview_data.keys():
                st.markdown(f"<div style ='{r_style}'>{overview_data[list_ratios[i * 3 + 2]]}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style ='{r_style}'> N/A </div>", unsafe_allow_html=True)

    return 0

@st.cache
def get_reports_data(ticker, report_type):
    # --------------------------------------------------
    # Getting data with regular financial reports using an API request
    # ticker: string
    # report_type: {'Income Statement', 'Balance Sheet', 'Cash Flow'}
    # --------------------------------------------------
    if report_type == 'Income Statement':
    # API function=INCOME_STATEMENT
        reports_func = "INCOME_STATEMENT"

    elif report_type == 'Balance Sheet':
    # API function=BALANCE_SHEET
        reports_func = "BALANCE_SHEET"

    elif report_type == 'Cash Flow':
    # API function=CASH_FLOW
        reports_func = "CASH_FLOW"

    # Send API request
    url = f'https://www.alphavantage.co/query?function={reports_func}&symbol={ticker}&apikey={config.AV_KEY}'
    r = requests.get(url)
    return r.json()


def dataframe_reports(ticker, report_type, number_quarter, period):
    # --------------------------------------------------------------
    # ticker: string
    # report_type: {'Income Statement', 'Balance Sheet', 'Cash Flow'}
    # number_quarter: int
    # period: {'annual', 'quarter'}
    # --------------------------------------------------------------

    data = get_reports_data(ticker, report_type)

    # number of periods: for quarters - set number by slider, for annual - get all available reports
    if period == "quarter":
        periodNumber = number_quarter
        analyse_data = data["quarterlyReports"][0:periodNumber]

    elif period == "annual":
        periodNumber = len(data["annualReports"])
        analyse_data = data["annualReports"][0:periodNumber]

    analyse_data_keys = list(analyse_data[0].keys())

    df_analyse_data = pd.DataFrame(columns=['Reporting date', 'Indicator', 'Value'])
    for i in range(0, periodNumber):
        for key in analyse_data_keys[1:]:
            # st.write(analyse_data[i][key])
            df_analyse_data = df_analyse_data.append(
                {'Reporting date': datetime.strptime(analyse_data[i]['fiscalDateEnding'], "%Y-%m-%d").date(),
                 'Indicator': key, 'Value': analyse_data[i][key]}, ignore_index=True)

    df_pivot = df_analyse_data.pivot(index='Indicator', columns='Reporting date', values='Value')
    df_pivot.replace(to_replace='None', value=0, inplace=True)
    df_pivot.sort_index(axis=1, ascending=False, inplace=True)
    df_pivot.loc[df_pivot.index != 'reportedCurrency'] = df_pivot.loc[df_pivot.index != 'reportedCurrency'].astype(
        'float64') / 1000000

    return df_pivot


def show_reports_visualization(fields, df):
    # --------------------------------------------------------------
    # Displaying a barplot for each selected metric from the report
    # for the corresponding reporting periods
    # fields: []
    # --------------------------------------------------------------


    for field in fields:
        col1, col2 = st.beta_columns([2, 5])
        with col1:
            st.subheader(field)
        with col2:
            str_y = field + ':Q'
            st.write(alt.Chart(df).mark_bar().encode(alt.X('Reporting date:O', axis=alt.Axis(labelAngle=-45)),
                                                             y=str_y, tooltip=field,
                                                             color=alt.condition(f"datum.{field} > 0",
                                                                                 alt.value('darkred'),
                                                                                 alt.value('orange'))).properties(
                width=400, height=200).configure_axis(disable=True).configure_view(stroke=None))

    return 0






