import logging
import os

from colorlog import ColoredFormatter


class MyFormatter(ColoredFormatter):
    def format(self, record):
        package, module = self.extract_package_module(record.pathname)
        record.pathname = f"{package}/{module}"
        return super().format(record)

    @staticmethod
    def extract_package_module(pathname):
        # Assuming that the pathname follows the structure "path/to/package/module.py"
        parts = os.path.splitext(pathname)[0].split(os.path.sep)

        if len(parts) > 2:
            package = parts[-2]
            module = parts[-1]
            return (package, module) if package != "" else (module,)
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            return "", parts[0]


def configure_logging(log_level):
    default_fmt = '%(log_color)s%(levelname)-8s%(white)s | %(message)s%(reset)s'
    debug_fmt = ('%(log_color)s%(levelname)-8s | %(asctime)s | %(pathname)s:%(lineno)d %(funcName)s | '
                 '%(white)s%(message)s%(reset)s')

    numeric_level = getattr(logging, log_level.upper(), None)

    if numeric_level == logging.DEBUG:
        fmt = debug_fmt
    else:
        fmt = default_fmt

    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    # Remove existing handlers from the root logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    formatter = MyFormatter(
        fmt,
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red'
        }
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logging.root.addHandler(stream_handler)
    logging.root.setLevel(numeric_level)

    logging.getLogger('config').info('Logging level set to %s', log_level)
