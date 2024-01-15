import logging
from datetime import date, timedelta
from logging import getLogger
from sys import exit

import requests


def calculate_dates(days_count, date_format="%Y-%m-%d"):
    today = date.today()
    from_date = today - timedelta(days=days_count)
    to_date = today - timedelta(days=1)
    return from_date.strftime(date_format), to_date.strftime(date_format)


def get_rates(currency, days_count):
    logger = getLogger()
    from_date, to_date = calculate_dates(days_count)
    logging.info(f'Getting {currency} rates from NBP for {days_count} days, ie. from {from_date} to {to_date}')

    url = f'https://api.nbp.pl/api/exchangerates/rates/a/{currency}/{from_date}/{to_date}'
    header = {'Accept': 'application/json'}
    try:
        r = requests.get(url, headers=header)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        exit(1)
    if r.status_code != 200:
        logger.error(f'Failed fetching {r.url}. {r.status_code}: {r.reason}')
        exit(1)

    rates = r.json().get('rates', [])
    logging.debug(f'Got {len(rates)} records.')
    return {rate.get('effectiveDate'): {currency: rate.get('mid')} for rate in rates}


def download_rates(days_count=90):
    currencies = ('EUR', 'USD', 'CHF')
    origin_rates = [get_rates(currency, days_count) for currency in currencies]

    dates = {key for item in origin_rates for key in item.keys()}

    rates = {
        date: {
            currency: rate for rate_dict in origin_rates for currency, rate in rate_dict.get(date, {}).items()
        } for date in dates
    }

    return rates










