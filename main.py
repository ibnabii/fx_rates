import argparse
import logging

from utils.config import configure_logging

DEFAULT_DB_CONFIG_FILENAME = './db_config.json'


def parse_arguments():
    parser = argparse.ArgumentParser(description='FX Rates')
    parser.add_argument('--log-level', dest='log_level',
                        default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Set the logging level (default: INFO)')

    return parser.parse_args()


def main():
    args = parse_arguments()

    configure_logging(args.log_level)

    logger = logging.getLogger(__name__)
    logger.debug(f'Arguments: {args}',)


if __name__ == '__main__':
    main()
