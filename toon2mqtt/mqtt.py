import os
import socket
import sys
import time
import paho.mqtt.client as mqtt

from toon2mqtt.crawler import Scheduler


# noinspection PyMethodOverriding
class MQTTListener(mqtt.Client):
    def __init__(self, settings, schemas, logger, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger
        self.schemas = schemas
        self.settings = settings
        self.scheduler = None

        self.online_topic = f"{self.settings.get('mqtt_topic')}/online"
        self.command_topic = f"{self.settings.get('mqtt_topic')}/command/#"

    def topic(self, name, key):
        return "{base}/{name}/{key}".format(
            base=self.settings.get('mqtt_topic'), name=name, key=key
        )

    def on_log(self, client, userdata, level, buffer):
        self.logger.debug(buffer)

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("Sending to will topic we're online")
        client.publish(topic=self.online_topic, payload=1)

        self.logger.info("Subscribing to topics...")
        client.subscribe(self.command_topic)

    def on_disconnect(self, client, userdata, rc):
        self.logger.error("Connection to broker failed... Reconnecting.")

    def on_subscribe(self, client, userdata, mid, granted_qos):
        self.logger.info("Subscribed to: {} {}".format(str(mid), str(granted_qos)))

    def on_message(self, client, userdata, message):
        self.logger.info("Incoming message on {}: {}".format(message.topic, message.payload))

    def setup_listener(self):
        self.reconnect_delay_set(min_delay=1, max_delay=30)
        self.will_set(self.online_topic, payload=0, qos=0, retain=True)

        if self.settings.get('mqtt_username') and self.settings.get('mqtt_password'):
            self.username_pw_set(
                username=self.settings.get('mqtt_username'),
                password=self.settings.get('mqtt_password')
            )

        if self.settings.get('mqtt_ssl') and \
                self.settings.get('mqtt_cert') and \
                os.path.isfile(self.settings.get('mqtt_cert')):
            self.tls_set(ca_certs=self.settings.get('mqtt_cert'))

        self.message_callback_add(sub=self.command_topic, callback=self.on_message)

        self.logger.info("Connecting to mqtt broker: {}://{}:{}".format(
            "mqtt/ssl" if self.settings.get('mqtt_ssl') else "mqtt",
            self.settings.get('mqtt_host'),
            self.settings.get('mqtt_port'))
        )

        self.connect(
            host=self.settings.get('mqtt_host'),
            port=self.settings.get('mqtt_port'),
            keepalive=60
        )

    def run(self):
        self.setup_listener()

        self.scheduler = Scheduler(client=self)
        self.scheduler.start()

        while True:
            try:
                self.loop_forever()

            except socket.error:
                time.sleep(5)

            except KeyboardInterrupt:
                self.logger.warning("Ctrl+C Pressed! Quitting Listener.")
                self.scheduler.stop()
                sys.exit(1)
