import pandas as pd
import tinvest
import streamlit as st
import json
import psycopg2.extras
from datetime import datetime
import requests

import config


def create_connection(host_name, user_name, user_password, db_name):
    """Create connection to postgres.
    Arguments:
    host_name: str, user_name: str, user_password: str, db_name: str
    Returns: connection: connection object
    """

    connection = None
    try:
        connection = psycopg2.connect(host=host_name, database=db_name, user=user_name, password=user_password)

        print("Connection to PostgreSQL DB successful")
    except psycopg2.OperationalError as e:
        error_msg = f"The error OperationalError {e} occurred"
        print(error_msg)

    return connection


@st.cache
def get_currency_balance_by_acc(account_id, client):
    """Through the API client, we receive the currency position of the specified account, write the received data into
    pandas.DataFrame and return the dataframe.

    Arguments:
    account_id: str
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: df_balance: pandas.DataFrame
    """
    currency_positions = client.get_portfolio_currencies(account_id)
    df_balance = pd.DataFrame(columns=["Currency", "Balance", "Blocked"])

    for curr in currency_positions.payload.currencies:
        df_balance = df_balance.append({"Currency": curr.currency.name.upper(),
                                        "Balance": curr.balance,
                                        "Blocked": curr.blocked},
                                       ignore_index=True)

    return df_balance


@st.cache
def get_positions_by_acc(account_id, client):
    """Through the API client, we receive the portfolio positions of the specified account, write the received data into
    pandas.DataFrame and return the dataframe.

    Arguments:
    account_id: str
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: df_positions: pandas.DataFrame
    """
    positions = client.get_portfolio(account_id)  # get portfolio by broker_account_id
    df_positions = pd.DataFrame(columns=["Name", "Ticker", "Balance", "Currency", "Price"])

    for position in positions.payload.positions:
        df_positions = df_positions.append({"Name": position.name, "Ticker": position.ticker,
                                            "Balance": position.balance,
                                            "Currency": position.average_position_price.currency.value,
                                            "Price": position.average_position_price.value},
                                           ignore_index=True)

    return df_positions

# ------------------------ API V 2 --- positions
# @st.cache
def api2_get_positions_by_acc(account_id, api_token):
    """Get the portfolio positions of the specified account, write the received data into
       pandas.DataFrame and return the dataframe.

    Arguments:
    account_id: str
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
    df_positions = pd.DataFrame(columns=["Figi", "InstrumentType", "Balance", "Currency", "AvgPositionPriceFifo", "CurrentPrice"])

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

# ------------------------ API V 2 --- positions

def split_buy_fifo(row_counter, df):
    """The method inserts a row into the dataframe after row number row_counter by changing the index and
    returns the modified dataframe.

    Arguments:
    row_counter: int
    df: pandas.DataFrame
    Returns: df: pandas.DataFrame -- modified dataframe
    """

    # Create new index for the dataframe df, excluding the number (row_counter + 1)
    new_index_part_1 = [i for i in range(0, row_counter + 1)]
    new_index_part_2 = [n for n in range(row_counter + 2, df.shape[0] + 1)]
    new_index_part_1.extend(new_index_part_2)

    # Apply the new index to the dataframe df
    df.index = new_index_part_1

    # Add a line with index (row_counter + 1), assign the values equal to line number row_counter
    df.loc[row_counter + 1] = pd.Series(df.loc[row_counter])
    df = df.sort_index()

    return df


# @st.cache
def get_user_accs_info(client):
    """Through the API client, method receive info about accounts and returns in dictionary format:
    key=broker_account_id, value=broker_account_type.
    Arguments: client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: accounts_info: dict

    """
    accounts = client.get_accounts().payload.accounts
    accounts_info = {}
    for acc in accounts:
        key = acc.broker_account_id
        value = acc.broker_account_type
        accounts_info[key] = value

    return accounts_info


def add_tcs_accs_to_db(conn, client):
    """
    Through the API client,  the method takes accounts info and inserts it into
    the 'broker_accounts' table of the database.
    Arguments:
    conn: connection object
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: No returns
    """
    accounts = get_user_accs_info(client)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    for item in accounts.items():
        if item[1].value == 'Tinkoff':
            type = 'regular'
        elif item[1].value == 'TinkoffIis':
            type = 'IIS'

        cursor.execute("""          INSERT INTO broker_accounts (id, type, owner, broker, is_valid)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """, (item[0], type, config.ACC_OWNER, 'Tinkoff', True))

        conn.commit()

    return


def fill_tcs_stock(conn, client):
    """Through the API client,  the method receives information about stock exchange shares traded in TCS, and
    either inserts a row into the table 'stock', or updates existing rows in the table (if the stock ticker is
    already contained in the table).

    Arguments:
    conn: connection object
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: No returns
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = client.get_market_stocks()
    # Get all symbols (tickers) from 'stock' table
    cursor.execute(""" Select symbol from stock WHERE type = 'stock' OR type is Null """)
    fetched_rows = cursor.fetchall()
    tickers = []
    for row in fetched_rows:
        tickers.append(row[0])
    for item in data.payload.instruments:
        # Check if item.ticker is in the 'tickers' list
        if item.ticker not in tickers:
            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                """, (
                item.ticker, item.name, 'SPB', False, item.currency.name.upper(), item.figi, item.isin, item.lot,
                item.min_price_increment, item.type.name, item.min_quantity))
        else:

            cursor.execute(""" UPDATE stock SET currency = %s, figi = %s, isin = %s, lot = %s, min_price_increment = %s,
                               type = %s, min_quantity = %s
                               Where symbol = %s
                               """, (item.currency.name.upper(), item.figi, item.isin, item.lot,
                                     item.min_price_increment, item.type.name, item.min_quantity, item.ticker))
            conn.commit()

    return


def fill_tcs_currencies(conn, client):
    """Through the API client,  the method receives information about currencies traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: No returns
    """
    currencies = client.get_market_currencies().payload.instruments

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='Currency' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    for item in currencies:
        if symbol not in tickers:

            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                            """, (
                item.ticker, item.name, 'MOEX', False, item.currency.value, item.figi, item.isin, item.lot,
                item.min_price_increment, item.type.value, item.min_quantity))

            conn.commit()

        else:
            print(f"{symbol} is already exist")

    return


def fill_tcs_etfs(conn, client):
    """Through the API client,  the method receives information about ETFs traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: No returns
    """
    etfs = client.get_market_etfs().payload.instruments

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='Etf' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])

    for item in etfs:
        if symbol not in tickers:
            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                                """, (
                item.ticker, item.name, 'MOEX', True, item.currency.value, item.figi, item.isin, item.lot,
                item.min_price_increment, item.type.value, item.min_quantity))

            conn.commit()

        else:
            print(f"{symbol} is already exist")

    return


def fill_tcs_bonds(conn, client):
    """Through the API client,  the method receives information about bonds traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    client: tinvest.SyncClient (Synchronous REST API Client)
    Returns: No returns
    """
    bonds = client.get_market_bonds().payload.instruments

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if such "symbol" exists in the table
    cursor.execute(""" Select symbol from stock WHERE type='Bond' """)
    fetched_rows = cursor.fetchall()
    tickers = set()
    for row in fetched_rows:
        tickers.add(row[0])


    for item in bonds:
        if symbol not in tickers:
            cursor.execute("""  INSERT INTO stock (symbol, name, exchange, is_etf, currency, figi, isin, lot, min_price_increment, type, min_quantity)
                                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                                """, (
                item.ticker, item.name, 'MOEX', False, item.currency.value, item.figi, item.isin, item.lot,
                item.min_price_increment, item.type.value, item.min_quantity))

            conn.commit()

        else:
            print(f"{symbol} is already exist")

    return


#  ------------------------ API V 2 --- Futures

def fill_tcs_futures(conn):
    """Through the API client,  the method receives information about bonds traded in TCS and
    inserts a row into the table 'stock'.

    Arguments:
    conn: connection object
    Returns: No returns
    """
    # headers and data for request
    hed = {'Authorization': 'Bearer ' + config.TCS_API_2_token}
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
                                                                """, (symbol, name, exchange, False, currency, figi, None,
                                                                      lot, None, type, None, fut_classCode, fut_firstTradeDate, fut_lastTradeDate,
                                                                      futuresType, fut_basicAsset, fut_basicAssetSize, fut_expirationDate))
            conn.commit()

        else:
            print(f"{symbol} is already exist")

    conn.close()

    return


#  ------------------------ API V 2 --- Futures

def save_tcs_operations_to_db(conn, client, acc_id, start_date, end_date):
    """Through the API client,  the method receives information about performed operations of the account,
    checks by 'operation_id' whether the operation has already been written to the database and inserts the row
    into the table 'operations'.

    Arguments:
    conn: connection object
    client: tinvest.SyncClient (Synchronous REST API Client)
    acc_id: str
    start_date: datetime object
    end_date: datetime object
    Returns: No returns
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    operations = client.get_operations(from_=start_date, to=end_date, broker_account_id=acc_id).payload.operations

    cursor.execute(""" Select id from operations Where date >= %s and date <= %s and account_id=%s""",
                   (start_date, end_date, acc_id))
    fetched_rows = cursor.fetchall()
    saved_operations = set()
    for row in fetched_rows:
        saved_operations.add(row[0])

    for item in operations:
        commission = item.commission if item.commission is None else item.commission.value  # if
        currency_code = item.currency.value
        operation_date = item.date
        figi = item.figi
        operation_id = item.id
        instrument_type = item.instrument_type if item.instrument_type is None else item.instrument_type.value  # if
        is_margin_call = item.is_margin_call
        operation_type = item.operation_type.value
        payment = item.payment
        price = item.price
        quantity = item.quantity
        quantity_executed = item.quantity_executed
        status = item.status.value

        cursor.execute("""  Select id from stock Where figi = %s """, (figi,))
        stock_id = None if figi is None else cursor.fetchone()[0]

        cursor.execute("""  Select currency_id from currencies_catalog Where char_code = %s """, (currency_code,))
        currency_id = cursor.fetchone()[0]

        if operation_id not in saved_operations:
            cursor.execute("""  INSERT INTO operations (id, account_id, commission, currency, date, stock_id, instrument_type,
                                is_margin_call, operation_type, payment, price, quantity, quantity_executed, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                            """,
                           (operation_id, acc_id, commission, currency_id, operation_date, stock_id, instrument_type,
                            is_margin_call, operation_type, payment, price, quantity, quantity_executed, status))

    conn.commit()

    return


if __name__ == '__main__':
    TCS_client = tinvest.SyncClient(config.TCS_API_token)

    # get accounts
    user_accs = get_user_accs_info(TCS_client)

    error_message = ""
    pg_connection = create_connection(config.DB_HOST, config.DB_USER, config.DB_PASS, config.DB_NAME)

    # print(TCS_client.get_market_search_by_ticker("NLOK"))
    # fill_tcs_stock(pg_connection, TCS_client)
    # fill_tcs_futures(pg_connection)

    try:
        pg_cursor = pg_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # for each accounts
        for acc in user_accs.keys():
            # start_date = last date in db, end_date = today
            pg_cursor.execute("Select MAX(date) from operations Where account_id=%s", (acc,))
            last_date = pg_cursor.fetchone()[0].date()                                  # date of last written operation
            # last_date = datetime.strptime("01.11.2021", "%d.%m.%Y").date()
            start_date = datetime.combine(last_date, datetime.min.time())               # last_date  00 hours 00 min 00 sec
            end_date = datetime.combine(datetime.today().date(), datetime.max.time())   # today  23 hours 59 min 59 sec
            save_tcs_operations_to_db(pg_connection, TCS_client, acc, start_date, end_date)

    except psycopg2.OperationalError as e:
        error_message = f"The error OperationalError '{e}' occurred"
        print(error_message)

    except AttributeError as r:
        error_message = f"The error AttributeError '{r}' occurred"
        print(error_message)

    finally:
        pg_connection.commit()
        pg_connection.close()


