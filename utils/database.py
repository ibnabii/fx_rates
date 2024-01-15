import json
from sys import exit
from typing import Optional


import logging
import psycopg2
from pydantic import BaseModel
from pydantic_core import ValidationError

SQL_CREATE_TABLE = """
CREATE TABLE data (
    rate_date DATE NOT NULL,
    eur_pln NUMERIC(10, 4) NULL,
    usd_pln NUMERIC(10, 4) NULL,
    chf_pln NUMERIC(10, 4) NULL,
    eur_usd NUMERIC(10, 4) NULL,
    chf_usd NUMERIC(10, 4) NULL
);
"""

SQL_CHECK_TABLE_EXISTS = """
select table_name from information_schema.tables
where table_schema = 'fx_rates'
and table_name = 'data'
"""

SQL_INSERT = """
INSERT INTO data (rate_date, eur_pln, usd_pln, chf_pln) VALUES (%s, %s, %s, %s);
"""

SQL_UPDATE = """
UPDATE data SET eur_usd = eur_pln / usd_pln, chf_usd = chf_pln / usd_pln
"""

TABLE_NAME = 'data'

COLUMN_NAMES = {
    'EUR/PLN': 'eur_pln',
    'USD/PLN': 'usd_pln',
    'CHF/PLN': 'chf_pln',
    'EUR/USD': 'eur_usd',
    'CHF/USD': 'chf_usd'
}


class DBConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str
    db_schema: Optional[str] = None


def read_db_config(filename: str) -> DBConfig:
    logging.debug(f'Reading database configuration from {filename}')
    try:
        with open(filename, 'r') as file:
            config = DBConfig(**json.load(file))
            logging.debug(f'DB config: {config}')
            return config
    except (FileNotFoundError, ValidationError, json.decoder.JSONDecodeError) as e:
        logging.error(e)
        exit(1)


def save_to_db(config: DBConfig, rates: dict):
    connection = None
    try:
        connection = get_db_connection(config)
    except psycopg2.OperationalError as e:
        logging.error(e)
        exit(1)

    else:
        if not table_exists(connection):
            create_table(connection)
        else:
            truncate_table(connection)

        with connection.cursor() as cursor:
            logging.debug("Saving data to database")
            for date, points in rates.items():
                cursor.execute(SQL_INSERT, (date, points.get('EUR'), points.get('USD'), points.get('CHF')))
            cursor.execute(SQL_UPDATE)
        connection.commit()

        logging.info('Data saved to database')

    finally:
        if connection:
            connection.close()
        logging.debug('Connection to DB closed')


def get_db_connection(config: DBConfig) -> psycopg2:
    logging.debug('Creating database connection')
    connection_string = f'host={config.host} port={config.port} user={config.user} password={config.password} dbname={config.database}'
    if config.db_schema:
        connection_string += f" options='-c search_path={config.db_schema}'"
    logging.debug(f'Connection string: {connection_string}')
    return psycopg2.connect(connection_string)


def table_exists(connection: psycopg2) -> bool:
    with connection.cursor() as cursor:
        logging.debug('Connection established')
        cursor.execute(SQL_CHECK_TABLE_EXISTS)
        exists = bool(cursor.fetchone())
        logging.debug(f'Table exists: {exists}')
        return exists


def create_table(connection: psycopg2):
    with connection.cursor() as cursor:
        logging.debug('Creating table')
        cursor.execute(SQL_CREATE_TABLE)
    connection.commit()


def truncate_table(connection: psycopg2):
    with connection.cursor() as cursor:
        logging.debug('Truncating table')
        cursor.execute(f'TRUNCATE TABLE {TABLE_NAME};')
        logging.debug(f"Result of TRUNCATE: {cursor.statusmessage}")
    connection.commit()


class FXRates:


    def __init__(self, rates, db_config_filename, show_columns=True):
        if rates:
            self.columns = ['Rate date'] + rates
            self.db_columns = ['rate_date'] + [COLUMN_NAMES.get(currency) for currency in rates]
        else:
            columns, db_columns = zip(*[(key, value) for key, value in COLUMN_NAMES.items()])
            self.columns = ['Rate date'] + list(columns)
            self.db_columns = ['rate_date'] + list(db_columns)
        self.select_query = f'''
            SELECT {', '.join([f'{db_name} as "{label}"' for db_name, label in zip(self.db_columns, self.columns)])}
            from {TABLE_NAME}
            order by rate_date;
        '''
        logging.debug(f'Select query:\n{self.select_query}')

        self.db_config_filename = db_config_filename
        self.show_columns = show_columns

    def __iter__(self):
        try:
            self.connection = get_db_connection(read_db_config(self.db_config_filename))
            self.cursor = self.connection.cursor()
            self.cursor.execute(self.select_query)
            return self
        except psycopg2.OperationalError as e:
            logging.error(e)
            exit(1)

    def __next__(self):
        if self.show_columns:
            self.show_columns = False
            return self.columns
        row = self.cursor.fetchone()
        if row is None:
            self.cursor.close()
            self.connection.close()
            raise StopIteration

        return [str(item) for item in row]


class FXStats:
    class Stats:
        def __init__(self, currency, avg, median, minimum, maximum):
            self.currency = currency
            self.average_rate = avg
            self.median_rate = median
            self.minimum_rate = minimum
            self.maximum_rate = maximum

        def __str__(self):
            return (f'\nStatistics for {self.currency}:\n'
                    f'\tAverage:\t{self.average_rate}\n'
                    f'\tMedian: \t{self.median_rate}\n'
                    f'\tMinimum:\t{self.minimum_rate}\n'
                    f'\tMaximum:\t{self.maximum_rate}')

    def __init__(self, rates, db_config_filename):
        if rates:
            self.rates = rates
        else:
            self.rates = COLUMN_NAMES.keys()

        try:
            self.connection = get_db_connection(read_db_config(db_config_filename))
            self.cursor = self.connection.cursor()

        except psycopg2.OperationalError as e:
            logging.error(e)
            exit(1)

        self.statistics = [self.Stats(currency, *self.calculate_statistics(currency)) for currency in self.rates]

    def calculate_statistics(self, currency):
        column_name = COLUMN_NAMES.get(currency)
        if not column_name:
            logging.error("We do not store data for {currency}!")
        SQL = f"""
            SELECT 
                AVG({column_name}) as average_rate,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER by {column_name}) as median_rate,
                MIN({column_name}) as min_rate,
                MAX({column_name}) as max_rate
            FROM {TABLE_NAME};
        """
        self.cursor.execute(SQL)
        return [round(float(item), 4) for item in self.cursor.fetchone()]


