import requests
import xml.etree.ElementTree as ET
import psycopg2.extras
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from tinkoff_invest import create_connection

import config


"""This module contains methods for obtaining data on the dynamics of exchange rates from the official website 
of the Central Bank of the Russian Federation and writing them in the database PostgreSQL.

For example, to get quotes for a given day
https://www.cbr.ru/scripts/XML_daily.asp?date_req=02/03/2002

An example of obtaining the dynamics of US dollar quotes:
https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=02/03/2001&date_req2=14/03/2001&VAL_NM_RQ=R01235

Catalog of currencies
https://www.cbr.ru/scripts/XML_valFull.asp
"""


def get_id_by_char_code(conn, char_code):
    """Executes a database select-query and returns the fetched value from the 'currency_id' column.

    Arguments: conn: connection object, char_code: str
    Returns: curr_id: str
    Exceptions:
    TypeError: The specified value char_code not found and query return value 'NoneType'.
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("Select currency_id from currencies_catalog Where char_code=%s", (char_code,))
    try:
        curr_id = cursor.fetchone()[0]
        conn.commit()
        return curr_id
    except TypeError:
        print(f"The specified value char_code = '{char_code}' was not found.")


def fill_currencies_catalog(conn):
    """Fill currencies catalog - get data from https://www.cbr.ru and populate 'currencies_catalog' table with data once.
     The table will contain various currency identifiers:
     currency_id, name, eng_name, char_code, num_code

     Arguments:
         conn: connection object
     Returns:
         No returns
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Send request to cbr
    url_full_catalog = 'https://www.cbr.ru/scripts/XML_valFull.asp'
    full_catalog = requests.get(url_full_catalog)

    # Save data to xml file
    with open('data/full_catalog.xml', 'w') as k:
        k.write(full_catalog.text)

    # Parse the xml file, extract the required fields for writing to the database
    tree = ET.parse('data/full_catalog.xml')
    root = tree.getroot()

    for curr in root.findall('Item'):
        currency_id = curr.get('ID')
        num_code = curr.find('ISO_Num_Code').text
        char_code = curr.find('ISO_Char_Code').text
        name = curr.find('Name').text
        eng_name = curr.find('EngName').text
        print(curr.tag, curr.attrib)
        print(f'ID = {currency_id} NumCode = {num_code} CharCode = {char_code} Name = {name} EngName = {eng_name}')
        cursor.execute("""
                            INSERT INTO currencies_catalog (currency_id, name, eng_name, char_code, num_code)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (currency_id, name, eng_name, char_code, num_code))

    # Additionally, we insert 'Russian Ruble' into the table, since it is absent in the xml file from cbr
    cursor.execute("""
                                INSERT INTO currencies_catalog (currency_id, name, eng_name, char_code, num_code)
                                VALUES (%s, %s, %s, %s, %s)
                                """, ('R01_', 'Российский рубль', 'Russian Ruble', 'RUB', '643'))

    conn.commit()

    return


def fill_currency_by_char_code(conn, char_code, date_start, date_end):
    """Get data from https://www.cbr.ru  and fill the table 'currency_price' in the database for the period
    from date_start to date_end.

    Arguments:
    conn: connection object
    char_code: str
    date_start: str  '%d/%m/%Y' format (like '24/08/2021')
    date_end: str  '%d/%m/%Y' format (like '24/08/2021')

    Returns: No returns
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get currency_id by char_code of currency from 'currencies_catalog' table
    currency_id = get_id_by_char_code(conn, char_code)

    # Send request to cbr
    url_dynamic = f'https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={date_start}&date_req2={date_end}&VAL_NM_RQ={currency_id}'

    dynamic = requests.get(url_dynamic)

    # Save data to xml file
    with open('data/dynamic.xml', 'w') as m:
        m.write(dynamic.text)

    # Parse the xml file, extract the required fields for writing to table 'currency_price'
    tree = ET.parse('data/dynamic.xml')
    root = tree.getroot()
    for record in root.findall('Record'):
        record_date = record.get('Date')
        value = record.find('Value').text

        cursor.execute("""
                            INSERT INTO currency_price (currency_id, dt, value_cbrf)
                                    VALUES (%s, %s, %s)
                                    """, (
            currency_id, datetime.strptime(record_date, "%d.%m.%Y").date(), float(str(value).replace(',', '.'))))

    conn.commit()

    return


def get_currency_value(conn, char_code, date):
    """Executes a database select-query and returns the currency rate values at the latest date not exceeding
    the date passed in the arguments to the function.
    Arguments: conn - connection object, char_code - str, date - datetime object (not string)
    Returns: float(value) - float
    """

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get currency_id by char_code of currency from 'currencies_catalog' table
    currency_id = get_id_by_char_code(conn, char_code)

    # We extract the value corresponding to the latest date not exceeding the specified date
    cursor.execute("Select value_cbrf from currency_price Where currency_id=%s and "
                   "dt=(Select MAX(dt) from currency_price where dt < %s or dt = %s)",
                   (currency_id, date.date(), date.date()))
    value = cursor.fetchone()[0]
    conn.commit()
    return float(value)


if __name__ == '__main__':

    """Fill the database with exchange rates from 'currency_list' up to and including the current date
    """

    error_message = ""
    pg_connection = create_connection(config.DB_HOST, config.DB_USER, config.DB_PASS, config.DB_NAME)
    currency_list = ['USD', 'EUR', 'GBP', 'SEK', 'CHF', 'JPY', 'CNY']    # list of popular currencies to write to the database

    try:

        pg_cursor = pg_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        for curr in currency_list:
            currency_id = get_id_by_char_code(pg_connection, curr)
            pg_cursor.execute("Select MAX(dt) from currency_price where currency_id=%s",
                              (currency_id,))
            last_date = pg_cursor.fetchone()[0]
            start_date = last_date + timedelta(days=1)
            str_end_date = datetime.today().strftime("%d/%m/%Y")
            str_start_date = start_date.strftime("%d/%m/%Y")

            if (datetime.today() - last_date).days > 0:
                fill_currency_by_char_code(pg_connection, curr, str_start_date, str_end_date)

    except psycopg2.OperationalError as e:
        error_message = f"The error OperationalError '{e}' occurred"
        print(error_message)

    except AttributeError as r:
        error_message = f"The error AttributeError '{r}' occurred"
        print(error_message)

    finally:
        pg_connection.commit()
        pg_connection.close()
