CREATE TABLE stock (
	id SERIAL PRIMARY KEY,
	symbol TEXT NOT NULL,
	name TEXT NOT NULL,
	exchange TEXT NOT NULL,
	is_etf BOOLEAN NOT NULL

);


ALTER TABLE stock
ADD COLUMN currency TEXT,
ADD COLUMN figi TEXT,
ADD COLUMN isin TEXT,
ADD COLUMN lot INTEGER,
ADD COLUMN min_price_increment NUMERIC,
ADD COLUMN type TEXT,
ADD COLUMN min_quantity INTEGER

;

-- --------Set NOT NULL later -----------
--ALTER TABLE stock
--ALTER COLUMN currency SET NOT NULL,
--ALTER COLUMN figi SET NOT NULL,
--ALTER COLUMN isin SET NOT NULL,
--ALTER COLUMN lot SET NOT NULL,
--ALTER COLUMN min_price_increment SET NOT NULL,
--ALTER COLUMN type SET NOT NULL
--;


CREATE TABLE mention (
    stock_id INTEGER NOT NULL,
    dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    sourse TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (stock_id, dt),
    CONSTRAINT fk_mention_stock FOREIGN KEY (stock_id) REFERENCES stock(id)

);

CREATE INDEX on mention (stock_id, dt DESC);
SELECT create_hypertable('mention', 'dt');

CREATE TABLE etf_holding (
	etf_id INTEGER NOT NULL,
	holding_id INTEGER NOT NULL,
	dt DATE NOT NULL,
	shares NUMERIC,
	weight NUMERIC,
	PRIMARY KEY (etf_id, holding_id, dt),
	CONSTRAINT fk_etf FOREIGN KEY (etf_id) REFERENCES stock (id),
	CONSTRAINT fk_holding FOREIGN KEY (holding_id) REFERENCES stock (id)
	
);

CREATE TABLE stock_price (
	stock_id INTEGER NOT NULL,
	dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	open NUMERIC NOT NULL,
	high NUMERIC NOT NULL,
	low NUMERIC NOT NULL,
	close NUMERIC NOT NULL,
	volume NUMERIC NOT NULL,
	PRIMARY KEY (stock_id, dt),
	CONSTRAINT fk_stock FOREIGN KEY (stock_id) REFERENCES stock (id)
	
);


CREATE INDEX ON stock_price (stock_id, dt DESC);
SELECT create_hypertable('stock_price', 'dt');

CREATE TABLE portfolios (
	portfolio TEXT NOT NULL,
	stock_id INTEGER NOT NULL,
	dt DATE NOT NULL,
	shares NUMERIC,
	avg_purchase_price NUMERIC,
	purchase_value NUMERIC,
	sales_value NUMERIC,
	PRIMARY KEY (portfolio, stock_id, dt),
	CONSTRAINT fk_stock_portfolios FOREIGN KEY (stock_id) REFERENCES stock (id)

);


CREATE TABLE currencies_catalog (
	currency_id TEXT Primary Key,
	name TEXT NOT NULL,
	eng_name TEXT NOT NULL,
	char_code TEXT,
	num_code TEXT
);

CREATE TABLE currency_price_cbrf (
	currency_id TEXT NOT NULL,
	dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	value NUMERIC NOT NULL,
	PRIMARY KEY (currency_id, dt),
	CONSTRAINT fk_currency FOREIGN KEY (currency_id) REFERENCES currencies_catalog (currency_id)

);

ALTER TABLE currency_price_cbrf RENAME to currency_price;
Alter TABLE currency_price RENAME COLUMN value to value_cbrf;

CREATE TABLE broker_accounts(
    id TEXT NOT NULL Primary Key,
    type TEXT NOT NULL,
    owner TEXT NOT NULL,
    broker TEXT NOT NULL,
    is_valid BOOLEAN NOT NULL

);

CREATE TABLE operations (
    id TEXT NOT NULL Primary Key,
    account_id TEXT NOT NULL,
	commission NUMERIC,
	currency TEXT NOT NULL,
	date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	stock_id INTEGER,
	instrument_type TEXT,
	is_margin_call BOOLEAN NOT NULL,
	operation_type TEXT NOT NULL,
	payment NUMERIC NOT NULL,
	price NUMERIC,
	quantity INTEGER,
	quantity_executed INTEGER,
	status TEXT NOT NULL,
	CONSTRAINT fk_accounts FOREIGN KEY (account_id) REFERENCES broker_accounts (id),
	CONSTRAINT fk_currencies FOREIGN KEY (currency) REFERENCES currencies_catalog (currency_id),
	CONSTRAINT fk_stocks FOREIGN KEY (stock_id) REFERENCES stock (id)
	);


