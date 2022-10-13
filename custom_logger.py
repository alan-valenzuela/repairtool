import logging
import sys
import time


DEBUG_LEVELV_NUM = 15
logging.INFORAW = DEBUG_LEVELV_NUM
logging.addLevelName(DEBUG_LEVELV_NUM, "INFORAW")

DEBUG_LEVELV_NUM2 = 18
logging.INFOREG = DEBUG_LEVELV_NUM2
logging.addLevelName(DEBUG_LEVELV_NUM2, "INFOREG")


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    blue = "\x1b[34m"
    green = "\x1b[32m"
    grey = "\x1b[36;1m"
    teal = "\x1b[36;1m"
    yellow = "\x1b[33;1m"
    red = "\x1b[31;1m"
    bold_red = "\x1b[31;31m"
    violet = "\x1b[1;45m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format_reg = "%(asctime)s - INFO - %(message)s (%(filename)s:%(lineno)d)"
    format_raw = "%(message)s"

    if sys.platform == 'win32':
        # No colors for windows, they don't deserve it
        FORMATS = {
            logging.DEBUG: format + reset,
            logging.INFORAW: format_raw,
            logging.INFOREG: format_reg + reset,
            logging.INFO: format + reset,
            logging.WARNING: format + reset,
            logging.ERROR: format + reset,
            logging.CRITICAL: format + reset
        }
    else:
        FORMATS = {
            logging.DEBUG: blue + format + reset,
            logging.INFORAW: format_raw,
            logging.INFOREG: teal + format_reg + reset,
            logging.INFO: teal + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: red + format + reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%d %H:%M:%S")
        return formatter.format(record)


class PlainFormatter(logging.Formatter):
    """Logging Formatter to be written to file and count warning / errors"""
    format = "%(asctime)s\t%(levelname)s\t%(message)s\t%(filename)s:%(lineno)d"
    format_reg = "%(asctime)s\tINFOREG\t%(message)s\t%(filename)s:%(lineno)d"
    format_raw = "%(asctime)s - %(message)s"

    FORMATS = {
        logging.DEBUG: format,
        logging.INFORAW: format_raw,
        logging.INFOREG: format_reg,
        logging.INFO: format,
        logging.WARNING: format,
        logging.ERROR: format,
        logging.CRITICAL: format
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def time_elapsed(func):
    """Decorator for writing time elapsed after function usage."""
    def wrapper(*args, **kwargs):
        t1 = time.time()
        done = func(*args, **kwargs)
        t2 = time.time()
        logger.debug(f"Time elapsed\t\t{func.__name__}\t{round(t2-t1, 6)}\ts\t")
        return done
    return wrapper


def reg(attr, value):
    logger.inforeg("\t".join([str(attr), str(value)])+"\t")


# Create main logger
logger = logging.getLogger("MAIN")
logger.reg = reg
# logger.write = write


def init_logger(filename='app.log'):
    """Initialize logger using colored handler and file handler."""
    logger = logging.getLogger("MAIN")
    logger.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    console_log = logging.StreamHandler()
    # Modificate here what we actually want to output on console
    console_log.setLevel(logging.INFORAW)
    console_log.setFormatter(CustomFormatter())

    # create file handler with lower log level
    file_log = logging.FileHandler(filename, mode='w')
    file_log.setLevel(logging.DEBUG)
    file_log.setFormatter(PlainFormatter())

    # Add handlers to be used by logger
    logger.addHandler(console_log)
    logger.addHandler(file_log)
