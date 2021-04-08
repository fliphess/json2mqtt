#!/usr/bin/env python3
import argparse
import logging
import sys

from pid import PidFile, PidFileAlreadyLockedError
from json2mqtt.mqtt import MQTTListener
from json2mqtt.schemas import Schemas
from json2mqtt.settings import Settings, ConfigError


def parse_arguments():
    parser = argparse.ArgumentParser(description="Toon2MQTT")

    parser.add_argument(
        "-c",
        "--config",
        dest="filename",
        type=str,
        required=True,
        help="The config file to use"
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        dest="loglevel",
        action="count",
        help="increase output verbosity"
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()

    loglevel = {
        1: logging.INFO,
        2: logging.DEBUG,
        None: logging.WARN
    }.get(arguments.loglevel, logging.INFO)

    logging.basicConfig(
        level=loglevel,
        format="[%(asctime)s] %(name)s | %(funcName)-20s | %(levelname)s | %(message)s")
    logger = logging.getLogger('json2mqtt')

    try:
        with PidFile('json2mqtt', piddir='/var/tmp'):
            logger.info("Reading configuration file {}".format(arguments.filename))
            settings = Settings(filename=arguments.filename)

            logger.info("Reading schema files {}".format(arguments.filename))
            schemas = Schemas(logger=logger, schema_dir=settings.schema_dir)
            schemas.import_all()

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
