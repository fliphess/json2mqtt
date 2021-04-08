import os
import socket
import sys
import time
import paho.mqtt.client as mqtt

from json2mqtt.commands import CommandHandler
from json2mqtt.scheduler import Scheduler


# noinspection PyMethodOverriding
class MQTTListener(mqtt.Client):
    def __init__(self, settings, schemas, logger, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger
        self.schemas = schemas
        self.settings = settings
        self.scheduler = None

        self.online_topic = f"{self.settings.mqtt_topic}/online"
        self.command_topic = f"{self.settings.mqtt_topic}/command/+/+"
        self.command_handler = None

    def topic(self, name, key, base_topic=None):
        base = base_topic or self.settings.mqtt_topic
        return f"{base}/{name}/{key}"

    def on_log(self, client, userdata, level, buffer):
        self.logger.debug(buffer)

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("Sending to will topic we're online")
        client.publish(topic=self.online_topic, payload=1)

        self.logger.info("Subscribing to topics...")
        client.subscribe(self.command_topic)

    def on_disconnect(self, client, userdata, rc):
        self.logger.error("Disconnected from broker....")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        self.logger.info(f"Subscribed to: {self.command_topic}")

    def on_message(self, client, userdata, message):
        self.logger.debug("Incoming message on {}: {}".format(message.topic, message.payload))

        section, task = str(message.topic).split('/')[-2:]

        self.command_handler.dispatcher(
            section=section,
            task=task,
            payload=message.payload
        )

    def setup_listener(self):
        self.reconnect_delay_set(min_delay=1, max_delay=30)
        self.will_set(self.online_topic, payload=0, qos=0, retain=True)

        if self.settings.mqtt_username and self.settings.mqtt_password:
            self.username_pw_set(
                username=self.settings.mqtt_username,
                password=self.settings.mqtt_password
            )

        if self.settings.mqtt_ssl and \
                self.settings.mqtt_cert and \
                os.path.isfile(self.settings.mqtt_cert):
            self.tls_set(ca_certs=self.settings.mqtt_cert)

        self.message_callback_add(sub=self.command_topic, callback=self.on_message)

        self.logger.info("Connecting to mqtt broker: {}://{}:{}".format(
            "mqtt/ssl" if self.settings.mqtt_ssl else "mqtt",
            self.settings.mqtt_host,
            self.settings.mqtt_port)
        )

        self.connect(
            host=self.settings.mqtt_host,
            port=self.settings.mqtt_port,
            keepalive=60
        )

    def run(self):
        self.setup_listener()

        self.scheduler = Scheduler(client=self)
        self.scheduler.start()

        self.command_handler = CommandHandler(client=self)

        while True:
            try:
                self.loop_forever()

            except socket.error:
                time.sleep(5)

            except KeyboardInterrupt:
                self.logger.warning("Ctrl+C Pressed! Quitting Listener.")
                self.scheduler.stop()
                self.disconnect()
                sys.exit(1)
