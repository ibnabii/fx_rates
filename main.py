import argparse
import csv
import logging
import sys
import time

import schedule
from utils.config import configure_logging
from utils.nbp import download_rates
from utils.database import read_db_config, save_to_db, FXRates, FXStats

DEFAULT_DB_CONFIG_FILENAME = './db_config.json'


def parse_arguments():
    parser = argparse.ArgumentParser(description='FX Rates')
    parser.add_argument('--log-level', dest='log_level',
                        default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Set the logging level (default: INFO)'
                        )

    parser.add_argument('--download', action='store_true',
                        help='Download the data from NBP API and store it in database'
                        )

    parser.add_argument('--list', action='store_true',
                        help='Output the rate data'
                        )

    parser.add_argument('--save', action='store_true',
                        help='Save the rate data to a file'
                        )

    parser.add_argument('--stats', action='store_true',
                        help='Calculate statistics for rates'
                        )

    parser.add_argument('--rates', nargs='+', required=False,
                        choices=['EUR/PLN', 'USD/PLN', 'CHF/PLN', 'EUR/USD', 'CHF/USD'],
                        help='List of FX rates to work with - works with "--list", "--save" and "--stats" switches. '
                             'All rates will be used when not specified.'
                        )

    parser.add_argument('--schedule', action='store_true',
                        help='Schedule execution of the download and save (with all other parameters in force)'
                             ' to run daily at 12:00 PM'
                        )

    return parser.parse_args()


def download_data():

    rates = download_rates(days_count=90)
    database = read_db_config(DEFAULT_DB_CONFIG_FILENAME)
    save_to_db(database, rates)


def list_data(rates):
    logging.info('Listing data')
    items = FXRates(rates, DEFAULT_DB_CONFIG_FILENAME)
    for item in items:
        print('\t'.join(item))


def save_data(rates):
    if rates:
        filename = './selected_currency_data.csv'
        msg = ', '.join(rates)
    else:
        filename = './all_currency_data.csv'
        msg = 'all rates'

    try:
        with open(filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            items = FXRates(rates, DEFAULT_DB_CONFIG_FILENAME)
            for item in items:
                writer.writerow(item)
        logging.info(f'Data for {msg} have been saved to {filename}')

    except (FileNotFoundError, PermissionError, OSError) as e:
        logging.error(e)
        sys.exit(1)


def calculate_stats(rates):
    logging.info('Calculating statistics')
    stats = FXStats(rates, DEFAULT_DB_CONFIG_FILENAME)
    for item in stats.statistics:
        print(item)


def scheduled_process(rates):
    download_data()
    save_data(rates)


def main():
    args = parse_arguments()

    configure_logging(args.log_level)

    logger = logging.getLogger(__name__)
    logger.debug(f'Arguments: {args}',)

    if args.download:
        download_data()
    if args.list:
        list_data(args.rates)
    if args.save:
        save_data(args.rates)
    if args.stats:
        calculate_stats(args.rates)
    if args.schedule:
        schedule.every().day.at("00:00").do(lambda: scheduled_process(args.rates))
        while True:
            sleep_time = max(0, schedule.next_run().timestamp() - time.time())
            logging.debug(f'Next execution: {schedule.next_run()} ({schedule.next_run().timestamp()})')
            logging.debug(f'Current time: {time.time()}')
            logging.debug(f'Sleeping for {sleep_time}')

            time.sleep(sleep_time)
            schedule.run_pending()


if __name__ == '__main__':
    main()
