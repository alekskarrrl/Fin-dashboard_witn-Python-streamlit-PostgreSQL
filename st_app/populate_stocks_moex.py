import psycopg2.extras
import csv
import os
from dotenv import load_dotenv

load_dotenv()

connection = psycopg2.connect(host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
                              password=os.getenv('DB_PASS'))
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

with open("rates.csv", encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        print(row)
        ticker = row[0]

        if ticker:
            name = row[2]
            cursor.execute("""
                           INSERT INTO stock (name, symbol, exchange, is_etf)
                           VALUES (%s, %s, 'MOEX', false)

                           """, (name, ticker))


connection.commit()

