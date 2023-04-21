import pandas as pd
import streamlit as st
import json
import psycopg2.extras
from datetime import datetime
import requests
from typing import Union
from dotenv import load_dotenv


load_dotenv()

"""
Tinkoff invest API2 docstrings ... 
"""


# @st.cache_data
def get_positions_by_acc(account_id: str, api_token: str) -> pd.DataFrame:
    """Get the portfolio positions of the specified account, write the received data into
       pandas.DataFrame and return the dataframe.

    Arguments:
    account_id: str
    api_token: str
    Returns: df_positions: pandas.DataFrame
    """
    data = {
        "accountId": account_id
    }

    head = {'Authorization': 'Bearer ' + api_token}

    url_get_portfolio = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPortfolio'
    response = requests.post(url_get_portfolio, json=data, headers=head)
    r = response.json()

    positions = r.get('positions')  # get portfolio by broker_account_id
    # df_positions = pd.DataFrame(columns=["Name", "Ticker", "Balance", "Currency", "Price"])
    df_positions = pd.DataFrame(
        columns=["Figi", "InstrumentType", "Balance", "Currency", "AvgPositionPriceFifo", "CurrentPrice"])

    for position in positions:
        figi = position.get('figi')
        instrumentType = position.get('instrumentType')
        quantity = position.get('quantity').get('units')
        averagePositionPriceFifo_units = int(position.get('averagePositionPriceFifo').get('units'))
        averagePositionPriceFifo_nano = position.get('averagePositionPriceFifo').get('nano') / 1000000000
        averagePositionPriceFifo = averagePositionPriceFifo_units + averagePositionPriceFifo_nano

        currentPrice_units = int(position.get('currentPrice').get('units'))
        currentPrice_nano = position.get('currentPrice').get('nano') / 1000000000
        currentPrice = currentPrice_units + currentPrice_nano
        currency = position.get('currentPrice').get('currency')
        df_positions = df_positions.append({"Figi": figi,
                                            "InstrumentType": instrumentType,
                                            "Balance": quantity,
                                            "Currency": currency,
                                            "AvgPositionPriceFifo": averagePositionPriceFifo,
                                            "CurrentPrice": currentPrice
                                            },
                                           ignore_index=True)

    return df_positions


# In process... api2
def get_historical_price(api_token: str, figi: str, dt_from: str, dt_to: str, interval: Union[str, int]) -> list:
    """  Get historical prices.
    Parameters:
    ----------
    api_token : str
    figi : str
    dt_from : str   / Format "2022-10-14T05:57:20.233Z"
    dt_to : str    / Format "2022-10-14T05:57:20.233Z"
    interval : str
    Возможные значения - str ['CANDLE_INTERVAL_1_MIN', 'CANDLE_INTERVAL_5_MIN', 'CANDLE_INTERVAL_15_MIN',
                            'CANDLE_INTERVAL_HOUR', 'CANDLE_INTERVAL_DAY']  OR
                            integer [1, 2, 3, 4, 5]

    Все интервалы свечей, кроме 'CANDLE_INTERVAL_DAY', возможны только для периода внутри дня.

    Returns
    -------

    candles: list(dict)
    candles = [
    {
    'open': {'units': int, 'nano': int},
    'high': {'units': int, 'nano': int},
    'low': {'units': int, 'nano': int},
    'close': {'units': int, 'nano': int},
    'volume': int,
    'time': timestamp in UTC # str format  '2022-09-01T04:00:00Z',
    'isComplete': bool
    }
    ...
    {....}
    ]

    """

    data = {
        "figi": figi,
        "from": dt_from,  # "2022-10-14T05:57:20.233Z",
        "to": dt_to,  # "2022-10-14T05:57:20.233Z",
        "interval": interval,  # "CANDLE_INTERVAL_DAY",
        "instrumentId": figi
    }
    head = {'Authorization': 'Bearer ' + api_token}
    url_get_prices = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles'
    response = requests.post(url_get_prices, json=data, headers=head)
    r = response.json()


    return r.get('candles')



#  ------------------------ API V 2 --- Futures

def fill_tcs_futures(conn, api_token):
    """Through the API client,  the method receives information about futures traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    api_token: str
    Returns: No returns
    """
    # headers and data for request
    hed = {'Authorization': 'Bearer ' + api_token,
           'Content-Type': 'application/json',
           'accept': 'application/json'
           }
    #
    data = {
        "instrument_status": "INSTRUMENT_STATUS_UNSPECIFIED"
    }

    # check if such "symbol" exists in the table
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(""" Select symbol from stock WHERE type='Futures' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    #

    url_get_futures = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService/Futures'
    response = requests.post(url_get_futures, json=data, headers=hed)
    r = response.json()
    r_text = response.text
    print(response.status_code)
    fut_list = r.get('instruments')

    for item in fut_list:
        symbol = item.get("ticker")
        name = item.get("name")
        exchange = item.get("exchange")
        # is_etf = False
        currency = item.get("currency").upper()
        figi = item.get("figi")
        # isin   =  Null
        lot = item.get("lot")
        # min_price_increment = Null
        type = "Futures"
        # min_quantity =  Null
        fut_classCode = item.get("classCode")
        fut_firstTradeDate = item.get("firstTradeDate")
        fut_lastTradeDate = item.get("lastTradeDate")
        futuresType = item.get("futuresType")
        fut_basicAsset = item.get("basicAsset")
        fut_basicAssetSize = item.get("basicAssetSize").get("units")
        fut_expirationDate = item.get("expirationDate")

        if symbol not in tickers:
            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment,
            type, min_quantity, "fut_classCode", "fut_firstTradeDate", "fut_lastTradeDate", "futuresType", "fut_basicAsset", "fut_basicAssetSize", "fut_expirationDate")
                                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                                                """,
                           (symbol, name, exchange, False, currency, figi, None,
                            lot, None, type, None, fut_classCode, fut_firstTradeDate, fut_lastTradeDate,
                            futuresType, fut_basicAsset, fut_basicAssetSize, fut_expirationDate))
            conn.commit()


        else:
            print(f"{symbol} is already exist and will be update now ")
            cursor.execute(""" UPDATE stock SET currency = %s, figi = %s, lot = %s,
                                           type = %s, "fut_classCode" = %s, "fut_firstTradeDate" = %s, 
                                           "fut_lastTradeDate" = %s, "futuresType" = %s, "fut_basicAsset" = %s, "fut_basicAssetSize" = %s, 
                                           "fut_expirationDate" = %s
                                           Where symbol = %s
                                           """, (currency, figi, lot, type, fut_classCode, fut_firstTradeDate, fut_lastTradeDate,
                           futuresType, fut_basicAsset, fut_basicAssetSize, fut_expirationDate, symbol))
            conn.commit()

    conn.close()

    return


#  ------------------------ API V 2 --- Futures



def save_tcs_operations_to_db(conn, api_token, acc_id, start_date, end_date):
    """the method receives information about performed operations of the account,
    checks by 'operation_id' whether the operation has already been written to the database and inserts the row
    into the table 'operations'.

    Arguments:
    conn: connection object
    acc_id: str
    start_date: datetime object
    end_date: datetime object
    Returns: No returns
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    hed = {'Authorization': 'Bearer ' + api_token,
           'Content-Type': 'application/json',
           'accept': 'application/json'
           }
    #
    data = {
        "accountId": acc_id,                                                           #"2029092513"
        "from": start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),                          #"2022-04-29T00:00:00.000Z" str format
        "to": end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),                              #"2022-05-09T23:59:59.999Z"  str format
        "state": "OPERATION_STATE_UNSPECIFIED"

    }

    url_get_operations = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetOperations'
    response = requests.post(url_get_operations, json=data, headers=hed)
    r = response.json()
    print(response.status_code)
    operations = r.get('operations')[0:20]
    child_operations = []


    for item in operations:
        commission = None
        parentOperationId = item.get("parentOperationId")
        currency_code = item.get("currency").upper()
        operation_date = item.get("date")
        figi = item.get("figi")
        operation_id = item.get("id")
        instrument_type = item.get("instrumentType")
        is_margin_call = False
        operation_type = item.get("operationType")
        payment_units = int(item.get("payment").get("units"))
        payment_nano = item.get("payment").get("nano") / 1000000000
        payment = payment_units + payment_nano
        price_units = int(item.get("price").get("units"))
        price_nano = item.get("price").get("nano") / 1000000000
        price = price_units + price_nano
        quantity = int(item.get("quantity"))
        quantity_executed = quantity - int(item.get("quantityRest"))
        status = item.get("state")

        if parentOperationId != "":
            child_operations.append(item)

        print(f""" 
                    id = {operation_id},
                    parentOperationId = {parentOperationId},
                    currency = {currency_code},
                    date = {operation_date},
                    payment = {payment},
                    price = {price},
                    state = {status},
                    quantity = {quantity},
                    quantity_executed = {quantity_executed},
                    figi = {figi},
                    instrumentType = {instrument_type},
                    operationType = {operation_type}
                """, 30 * "#")

        cursor.execute("""  Select id from stock Where figi = %s """, (figi,))
        stock_id = None if figi == "" else cursor.fetchone()[0]
        #stock_id = cursor.fetchone()[0]

        cursor.execute("""  Select currency_id from currencies_catalog Where char_code = %s """, (currency_code,))
        currency_id = cursor.fetchone()[0]

        cursor.execute("""  INSERT INTO operations (id, account_id, commission, currency, date, stock_id, instrument_type,
                                        is_margin_call, operation_type, payment, price, quantity, quantity_executed, status)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                       (operation_id, acc_id, commission, currency_id, operation_date, stock_id, instrument_type,
                        is_margin_call, operation_type, payment, price, quantity, quantity_executed, status))

        conn.commit()
    print("child operations is: ", child_operations)
    for oper in child_operations:
        operation_id = oper.get("parentOperationId")
        commission = int(oper.get("payment").get("units")) + oper.get("payment").get("nano") / 1000000000

        cursor.execute(""" UPDATE operations SET commission = %s Where id = %s""", (commission, operation_id))
        print(commission, operation_id)

        conn.commit()

    return



def fill_tcs_currencies(conn, api_token):
    """Through the API client,  the method receives information about currencies traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    api_token: str
    Returns: No returns
    """

    hed = {'Authorization': 'Bearer ' + api_token,
           'Content-Type': 'application/json',
           'accept': 'application/json'
           }
    #
    data = {
        "instrumentStatus": "INSTRUMENT_STATUS_UNSPECIFIED"
    }

    url_get_operations = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService/Currencies'
    response = requests.post(url_get_operations, json=data, headers=hed)
    r = response.json()
    currencies = r.get('instruments')

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='Currency' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    for item in currencies:
        if item.get('ticker') not in tickers:
            ticker = item.get('ticker')
            name = item.get('name')
            currency = item.get('currency').upper()
            figi = item.get('figi')
            isin = None
            lot = item.get('lot')
            minPriceIncrement_units = int(item.get('minPriceIncrement').get('units'))
            minPriceIncrement_nano = item.get('minPriceIncrement').get('nano') / 1000000000
            minPriceIncrement = minPriceIncrement_units + minPriceIncrement_nano
            exchange = 'MOEX'
            is_etf = False
            sec_type = 'Currency'

            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                                        """, (
                ticker, name, exchange, is_etf, currency, figi, isin, lot,
                minPriceIncrement, sec_type, None))

            conn.commit()

        else:
            print(f"{item.get('ticker')} is already exist")

    return


def fill_tcs_etfs(conn, api_token):
    """Through the API client,  the method receives information about etfs traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    api_token: str
    Returns: No returns
    """

    hed = {'Authorization': 'Bearer ' + api_token,
           'Content-Type': 'application/json',
           'accept': 'application/json'
           }
    #
    data = {
        "instrumentStatus": "INSTRUMENT_STATUS_UNSPECIFIED"
    }

    url_get_operations = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService/Etfs'
    response = requests.post(url_get_operations, json=data, headers=hed)
    r = response.json()
    etfs = r.get('instruments')

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

 # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='Etf' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    for item in etfs:
        if item.get('ticker') not in tickers:
            ticker = item.get('ticker')
            name = item.get('name')
            currency = item.get('currency').upper()
            figi = item.get('figi')
            isin = item.get('isin')
            lot = item.get('lot')
            minPriceIncrement_units = int(item.get('minPriceIncrement').get('units'))
            minPriceIncrement_nano = item.get('minPriceIncrement').get('nano') / 1000000000
            minPriceIncrement = minPriceIncrement_units + minPriceIncrement_nano
            exchange = item.get('exchange')
            is_etf = True
            sec_type = 'Etf'

            # print(ticker, name, exchange, is_etf, currency, figi, isin, lot, minPriceIncrement, sec_type)


            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                                        """, (
                ticker, name, exchange, is_etf, currency, figi, isin, lot, minPriceIncrement, sec_type, None))

            conn.commit()

        else:
            print(f"{item.get('ticker')} is already exist")

    return


def fill_tcs_bonds(conn, api_token):
    """Through the API client,  the method receives information about bonds traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    api_token: str
    Returns: No returns
    """

    hed = {'Authorization': 'Bearer ' + api_token,
           'Content-Type': 'application/json',
           'accept': 'application/json'
           }
    #
    data = {
        "instrumentStatus": "INSTRUMENT_STATUS_UNSPECIFIED"
    }

    url_get_operations = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService/Bonds'
    response = requests.post(url_get_operations, json=data, headers=hed)
    r = response.json()
    bonds = r.get('instruments')
    print(bonds)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

 # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='Bond' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    for item in bonds:
        if item.get('ticker') not in tickers:
            try:
                ticker = item.get('ticker')
                name = item.get('name')
                currency = item.get('currency').upper()
                figi = item.get('figi')
                isin = item.get('isin')
                lot = item.get('lot')
                print(figi)
                minPriceIncrement_units = int(item.get('minPriceIncrement').get('units'))
                minPriceIncrement_nano = item.get('minPriceIncrement').get('nano') / 1000000000
                minPriceIncrement = minPriceIncrement_units + minPriceIncrement_nano
                exchange = item.get('exchange')
                is_etf = False
                sec_type = 'Bond'

                cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                                            """, (
                    ticker, name, exchange, is_etf, currency, figi, isin, lot, minPriceIncrement, sec_type, None))

                conn.commit()

            except AttributeError as e:
                print(e)

        else:
            print(f"{item.get('ticker')} is already exist")

    return


def fill_tcs_stock(conn, api_token):
    """Through the API client,  the method receives information about stocks traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    api_token: str
    Returns: No returns
    """

    hed = {'Authorization': 'Bearer ' + api_token,
           'Content-Type': 'application/json',
           'accept': 'application/json'
           }
    #
    data = {
        "instrumentStatus": "INSTRUMENT_STATUS_UNSPECIFIED"
    }

    url_get_operations = 'https://invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares'
    response = requests.post(url_get_operations, json=data, headers=hed)
    r = response.json()
    shares = r.get('instruments')
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='stock' OR type is Null """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    for item in shares:
        ticker = item.get('ticker')
        name = item.get('name')
        currency = item.get('currency').upper()
        figi = item.get('figi')
        isin = item.get('isin')
        lot = item.get('lot')
        minPriceIncrement_units = int(item.get('minPriceIncrement').get('units'))
        minPriceIncrement_nano = item.get('minPriceIncrement').get('nano') / 1000000000
        minPriceIncrement = minPriceIncrement_units + minPriceIncrement_nano
        exchange = item.get('exchange')
        is_etf = False
        sec_type = 'stock'
        # Check if item.ticker is in the 'tickers' list
        if item.get('ticker') not in tickers:

            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                """, (
                ticker, name, exchange, is_etf, currency, figi, isin, lot,
                minPriceIncrement, sec_type, None))
            conn.commit()
            print(ticker, name, exchange, is_etf, currency, figi, isin, lot, minPriceIncrement, sec_type)
        else:

            cursor.execute(""" UPDATE stock SET currency = %s, figi = %s, isin = %s, lot = %s, min_price_increment = %s,
                               type = %s, min_quantity = %s
                               Where symbol = %s
                               """, (currency, figi, isin, lot, minPriceIncrement, sec_type, None, ticker))
            conn.commit()
            print(f"{item.get('ticker')} is already exist")

    return

