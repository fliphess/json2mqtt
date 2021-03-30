#!/usr/bin/env python3
import argparse
import sys

from pid import PidFile, PidFileAlreadyLockedError

from toon2mqtt.logging import log
from toon2mqtt.mqtt import MQTTListener
from toon2mqtt.schemas.boilervalues import BOILERVALUES_SCHEMA
from toon2mqtt.schemas.edge2stats import EDGE_2_STATS_SCHEMA
from toon2mqtt.schemas.module_version import MODULE_VERSION_SCHEMA
from toon2mqtt.settings import (
    Settings,
    ConfigError,
)

schemas = [
    BOILERVALUES_SCHEMA,
    EDGE_2_STATS_SCHEMA,
    MODULE_VERSION_SCHEMA,
]


def parse_arguments():
    parser = argparse.ArgumentParser(description="Toon2MQTT")

    parser.add_argument(
        "-c",
        "--config",
        dest="filename",
        type=str,
        required=True,
        help="The config file to read (if nonexistent a config will be created)"
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        dest="loglevel",
        action="count",
        help="increase output verbosity"
    )

    parser.add_argument(
        "-l",
        "--log",
        dest="logfile",
        default='toon2mqtt.log',
        help="The log file to write to"
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()

    logger = log(
        level=arguments.loglevel,
        filename=arguments.logfile,
    )

    try:
        with PidFile('toon2mqtt', piddir='/var/tmp'):
            logger.info("Reading configuration file {}".format(arguments.filename))

            settings = Settings(filename=arguments.filename)

            logger.info("Starting MQTT Listener server")
            server = MQTTListener(
                settings=settings,
                schemas=schemas,
                logger=logger,
            )
            server.run()

    except ConfigError as e:
        logger.error("Config file contains errors: {}".format(e))
        sys.exit(1)

    except PidFileAlreadyLockedError:
        logger.error("Another instance of this service is already running")
        sys.exit(1)
