#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

CREATE TABLE IF NOT EXISTS stock (
	id SERIAL,
	symbol TEXT NOT NULL,
	name TEXT NOT NULL,
	exchange TEXT NOT NULL,
	is_etf BOOLEAN NOT NULL,
	currency TEXT,
	figi TEXT,
	isin TEXT,
	lot INTEGER,
	min_price_increment NUMERIC,
	type TEXT,
  min_quantity INTEGER,
  "fut_classCode" text,
  "fut_firstTradeDate" timestamp without time zone,
  "fut_lastTradeDate" timestamp without time zone,
  "futuresType" text,
  "fut_basicAsset" text,
  "fut_basicAssetSize" integer,
  "fut_expirationDate" timestamp without time zone,
  CONSTRAINT stock_pkey PRIMARY KEY (id)
);



CREATE TABLE IF NOT EXISTS mention (
    stock_id INTEGER NOT NULL,
    dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    sourse TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (stock_id, dt),
    CONSTRAINT fk_mention_stock FOREIGN KEY (stock_id) REFERENCES stock(id)

);


CREATE TABLE IF NOT EXISTS stock_price (
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


CREATE TABLE IF NOT EXISTS currencies_catalog (
	currency_id TEXT,
	name TEXT NOT NULL,
	eng_name TEXT NOT NULL,
	char_code TEXT,
	num_code TEXT,
	PRIMARY KEY (currency_id)
);

CREATE TABLE IF NOT EXISTS currency_price (
	currency_id TEXT NOT NULL,
	dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	value_cbrf NUMERIC NOT NULL,
	PRIMARY KEY (currency_id, dt),
	CONSTRAINT fk_currency FOREIGN KEY (currency_id) REFERENCES currencies_catalog (currency_id)

);



CREATE TABLE IF NOT EXISTS broker_accounts(
    id TEXT NOT NULL Primary Key,
    type TEXT NOT NULL,
    owner TEXT NOT NULL,
    broker TEXT NOT NULL,
    is_valid BOOLEAN NOT NULL

);

CREATE TABLE IF NOT EXISTS operations (
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




EOSQL