import json
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

        self.host = self.settings.get('mqtt_host')
        self.port = self.settings.get('mqtt_port')
        self.username = self.settings.get('mqtt_username')
        self.password = self.settings.get('mqtt_password')
        self.use_ssl = self.settings.get('mqtt_ssl')
        self.ssl_cert = self.settings.get('mqtt_cert')

        self.online_topic = f"{self.settings.get('mqtt_topic')}/online"
        self.command_topic = f"{self.settings.get('mqtt_topic')}/command/#"

    def topic(self, name, key):
        return "{base}/{name}/{key}".format(
            base=self.settings.get('mqtt_topic'), name=name, key=key
        )

    def on_log(self, mqttc, obj, level, string):
        self.logger.debug(string)

    def on_connect(self, mqttc, obj, flags, rc):
        self.logger.info("Notifying broker we're online")
        mqttc.publish(topic=self.online_topic, payload=1)

    def on_disconnect(self, mqttc, obj, rc):
        self.logger.error("Connection to broker failed... Reconnecting.")

    def on_message(self, mqttc, obj, msg):
        print(obj)
        print(msg)
        self.logger.info("Incoming message: {}".format(msg.payload))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        self.logger.info("Subscribed to: {} {}".format(str(mid), str(granted_qos)))

    def _setup_listener(self):
        self.reconnect_delay_set(min_delay=1, max_delay=30)
        self.will_set(self.online_topic, payload=0, qos=0, retain=True)

        if self.username and self.password:
            self.username_pw_set(username=self.username, password=self.password)

        if self.use_ssl and self.ssl_cert and os.path.isfile(self.ssl_cert):
            self.tls_set(ca_certs=self.ssl_cert)

        self.message_callback_add(self.command_topic, self.on_message)

        self.logger.info("Connecting to mqtt broker: {}://{}:{}".format(
            "mqtt/ssl" if self.use_ssl else "mqtt", self.host, self.port))

        self.connect(host=self.host, port=self.port, keepalive=60)

    def run(self):
        self._setup_listener()

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
