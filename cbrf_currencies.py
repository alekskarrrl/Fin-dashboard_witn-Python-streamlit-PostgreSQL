import requests
import xml.etree.ElementTree as ET
import config
import psycopg2.extras
from datetime import datetime
from decimal import Decimal


# For example, to get quotes for a given day
# http://www.cbr.ru/scripts/XML_daily.asp?date_req=02/03/2002

# An example of obtaining the dynamics of US dollar quotes:
# http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=02/03/2001&date_req2=14/03/2001&VAL_NM_RQ=R01235

# catalog of currencies
# https://www.cbr.ru/scripts/XML_valFull.asp


def fill_currencies_catalog(cursor):
    with open('full_catalog.xml', 'w') as k:
        k.write(full_catalog.text)

    tree = ET.parse('full_catalog.xml')
    root = tree.getroot()

    for valute in root.findall('Item'):
        valute_id = valute.get('ID')
        num_code = valute.find('ISO_Num_Code').text
        char_code = valute.find('ISO_Char_Code').text
        name = valute.find('Name').text
        eng_name = valute.find('EngName').text
        print(valute.tag, valute.attrib)
        print(f'ID = {valute_id} NumCode = {num_code} CharCode = {char_code} Name = {name} EngName = {eng_name}')
        cursor.execute("""
                            INSERT INTO currencies_catalog (valute_id, name, eng_name, char_code, num_code)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (valute_id, name, eng_name, char_code, num_code))

    return 0


def fill_currency_by_char_code(cursor, char_code, date_start, date_end):

    cursor.execute("Select valute_id from currencies_catalog Where char_code=%s", (char_code, ))
    valute_id = cursor.fetchone()[0]  # [0]
    url_dynamic = f'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={date_start}&date_req2={date_end}&VAL_NM_RQ={valute_id}'

    dynamic = requests.get(url_dynamic)

    with open('dynamic.xml', 'w') as m:
        m.write(dynamic.text)

    tree = ET.parse('dynamic.xml')
    root = tree.getroot()
    for record in root.findall('Record'):
        valute_id = record.get('Id')
        record_date = record.get('Date')
        value = record.find('Value').text

        print(record.tag, record.attrib)
        print(f'Record date = {record_date} Id = {valute_id} value = {value}')

        cursor.execute("""
                            INSERT INTO currency_price_cbrf (valute_id, dt, value)
                                    VALUES (%s, %s, %s)
                                    """, (valute_id, record_date, float(str(value).replace(',', '.'))))

    return 0


def get_currency_value(cursor, char_code, date):
    cursor.execute("Select valute_id from currencies_catalog Where char_code=%s", (char_code,))
    valute_id = cursor.fetchone()[0]  # [0]

    cursor.execute("Select value from currency_price_cbrf Where valute_id=%s and "
                   "dt=(Select MAX(dt) from currency_price_cbrf where dt < %s or dt = %s)", (valute_id, date, date))
    value = cursor.fetchone()
    return float(value[0])




connection = psycopg2.connect(host =config.DB_HOST, database = config.DB_NAME, user = config.DB_USER, password = config.DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

str_date = '21/08/2021'
str_start_date = '28/08/2021'
str_end_date = '02/09/2021'
currency_id = 'R01235'
currency_list = ['USD', 'EUR', 'GBP', 'SEK', 'CHF', 'JPY', 'CNY']

url_daily = f'http://www.cbr.ru/scripts/XML_daily.asp?date_req={str_date}'
url_dynamic = f'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={str_start_date}&date_req2={str_end_date}&VAL_NM_RQ={currency_id}'
url_full_catalog = 'https://www.cbr.ru/scripts/XML_valFull.asp'


daily = requests.get(url_daily)
dynamic = requests.get(url_dynamic)
full_catalog = requests.get(url_full_catalog)

# with open('daily.xml', 'w') as f:
#     f.write(daily.text)




# To fill out the catalog of currencies
# fill_currencies_catalog(cursor)

# To fill out the currencies value
# for curr in currency_list:
#     fill_currency_by_char_code(cursor, curr, str_start_date, str_end_date)

    #print(curr, get_currency_value(cursor, curr, datetime.strptime('24/08/2021', '%d/%m/%Y')))
    #print(curr, get_currency_value(cursor, curr, datetime.strptime('2020-12-23T22:28:54.902000+03:00', '%Y-%m-%dT%H:%M:%S.%f%z').date()))
    #print(type(get_currency_value(cursor, curr, datetime.strptime('21/08/2021', '%d/%m/%Y'))))


connection.commit()



