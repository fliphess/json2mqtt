import logging
import sys


def verbosity(level):
    return {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARN,
        3: logging.INFO,
        4: logging.DEBUG,
        None: logging.WARN
    }.get(level, logging.DEBUG)


def log(level, filename="toon2mqtt.log", fmt="[%(asctime)s] %(name)s | %(funcName)-20s | %(levelname)s | %(message)s"):
    loglevel = verbosity(level=level)
    formatter = logging.Formatter(fmt=fmt)

    logger = logging.getLogger('toon2mqtt')
    logger.setLevel(loglevel)

    file_handler = logging.FileHandler(filename=filename)
    file_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logger
