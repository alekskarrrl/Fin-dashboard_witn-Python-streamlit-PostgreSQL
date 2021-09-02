<<<<<<< HEAD
docker build -t dashboard-test .  
docker run -p 8501:8501 dashboard-test  




# Wallstreetbets
**Что сделано:**  

**Что планируется:**  




# Tinkoff Invest  
**Цель:**  
Анализ эффективности сделок по принципу FIFO, мониторинг брокерских комиссий и начисленных/уплаченных налогов  

**Что сделано:**  
С помощью модуля [tinvest](https://daxartio.github.io/tinvest/) (Python модуль для работы с OpenAPI Тинькофф Инвестиции) получаем данные о состоянии портфеля ценных бумаг в разбивке по счетам,
список операций по счету за выбранный период,  
строим таблицу FIFO сделок купли-продажы выбранной бумаги с учетом курса валюты на дату покупки и продажи активов. Курс валют взят по данным ЦБ РФ, так как для целей налогообложения доходы и расходы в валюте конвертируются в рубли именно по курсу ЦБ РФ.
Курсы основных валют получены через [сервис ЦБ РФ](https://www.cbr.ru/development/SXML/) в формате XML, извлечены из документа XML и сохранены в БД (PostgreSQL)  
Для закрытых сделок расчитана прибыль в валюте инструмента и в рублях.
Для открытых позиций расчитана ожидаемая прибыль при продаже в текущий день по текущей цене в валюте и выполнен пересчет в рубли по текущему курсу ЦБ РФ (логика - прибыль при продаже актива сегодня по текущей цене и при текущем курсе валюты относительно рубля)  
Выгрузка таблицы в файл .csv


**Что планируется:**  
рефакторинг, кэширование ответов API  
в таблицу покупок/продаж сохранять дату сразу в формете datetime, а не текстовом  
Прописать получение списка всех счетов, а не жесткая привязка по ID счета  
Построить сводный отчет FIFO по портфелю  
Расчет налогов  
Добавить информацию по дивидендам (возможно добавить визуализацию в динамике), по комиссиям и прочим расходам  
Прописать логику для бондов  
Расчет чистой внутренней доходности портфеля  

# Fundamental Data
**Что сделано:**   
С помощью [Alpha Vantage API](https://www.alphavantage.co/documentation/) выводится информация о компании по введенному тикеру в боковой панели:
- краткое описание деятельности компании,
- набор коэфициентов (нужно пересмотреть набор),
- квартальные и годовые отчеты на выбор за необходимое количество периодов в формате таблицы или столбчатых диаграм:
    - Баланс (Balance Sheet),
    - Отчет о прибыли (Income Statement),
    - Отчет о движении денежных средств (Cash Flow).
    
В каждом виде отчета по умолчанию выбрано несколько наиболее важных показателей, но по желанию можно выбрать дополнительные из выпадающего списка 


**Что планируется:**  
рефакторинг, ответы API нужно кэшироввать  
доработать дизайн графиков (нужна вертикальная ось, графики прозрачные, поправить отображение текста слева от диаграмм, возможно изменить цветовую схему и тд)  
отчеты складывать в БД  
Дальнейший анализ и сопоставление показателей с рыночными ценами 

=======
# Fin-dashboard_witn-Python-streamlit-PostgreSQL
TimescaleDB - PostgreSQL for Time-Series Data plyalist by Part Time Larry  youtube channel


1. Build an ETF Database (ARK INVEST ETFs) with PostgreSQL, creating tables - file <code>create_query.sql</code>.
2. Populating the <code>stock</code> table with data from <code>alpaca_trade_api</code> - script file <code>populate_stocks.py</code>.
3. Populating the <code>etf_holding</code> table with data about ARK INVEST ETFs - script file <code>populate_etfs.py</code>.   
   Data on the composition of ARK INVEST funds was taken from the site https://ark-funds.com/arkk in csv format.
4. Create <code>mention</code> table and populate it with data from the [wallstreetbets community](https://www.reddit.com/r/wallstreetbets/)  on reddit.com (using <code>PushshiftAPI</code>).
   Publications are matched against the <code>stock</code> table by cashtags (words start with '$' symbol) and recorded in <code>mention</code> table - script file <code>search_wsb.py</code>.
5. 
>>>>>>> 5e12f69a0b3fe4e192d4dbb9640da803624873af


