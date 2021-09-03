CREATE TABLE stock (
	id SERIAL PRIMARY KEY,
	symbol TEXT NOT NULL,
	name TEXT NOT NULL,
	exchange TEXT NOT NULL,
	is_etf BOOLEAN NOT NULL
);


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
	valute_id TEXT Primary Key,
	name TEXT NOT NULL,
	eng_name TEXT NOT NULL,
	char_code TEXT,
	num_code TEXT
);

CREATE TABLE currency_price_cbrf (
	valute_id TEXT NOT NULL,
	dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	value NUMERIC NOT NULL,
	PRIMARY KEY (valute_id, dt),
	CONSTRAINT fk_currency FOREIGN KEY (valute_id) REFERENCES currencies_catalog (valute_id)

);

=======
>>>>>>> 5e12f69a0b3fe4e192d4dbb9640da803624873af
