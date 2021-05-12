# Fin-dashboard_witn-Python-streamlit-PostgreSQL
TimescaleDB - PostgreSQL for Time-Series Data plyalist by Part Time Larry  youtube channel


1. Build an ETF Database (ARK INVEST ETFs) with PostgreSQL, creating tables - file <code>create_query.sql</code>.
2. Populating the <code>stock</code> table with data from <code>alpaca_trade_api</code> - script file <code>populate_stocks.py</code>.
3. Populating the <code>etf_holding</code> table with data about ARK INVEST ETFs - script file <code>populate_etfs.py</code>.   
   Data on the composition of ARK INVEST funds was taken from the site https://ark-funds.com/arkk in csv format.
4. Create <code>mention</code> table and populate it with data from the [wallstreetbets community](https://www.reddit.com/r/wallstreetbets/)  on reddit.com (using <code>PushshiftAPI</code>).
   Publications are matched against the <code>stock</code> table by cashtags (words start with '$' symbol) and recorded in <code>mention</code> table - script file <code>search_wsb.py</code>.
5. 


