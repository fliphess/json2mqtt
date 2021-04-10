import os


class CommandHandler(object):
    def __init__(self, client):
        self.client = client
        self.settings = self.client.settings
        self.schemas = self.client.schemas
        self.logger = self.client.logger
        self.scheduler = self.client.scheduler

        self.topic = f"{self.settings.mqtt_topic}/talkback"

        self.routing = {
            # Handles base_topic/schema/+
            "schema": {
                "add": self.schema_add,
                "add_file": self.schema_add_file,
                "remove": self.schema_remove,
                "dump": self.schema_dump,
                "import": self.schema_import,
                "list": self.schema_list,
            },

            # Handles base_topic/scheduler/+
            "scheduler": {
                "list": self.scheduler_list,
                "stop": self.scheduler_stop,
                "start": self.scheduler_start,
                "add_timer": self.scheduler_add_timer,
                "remove_timer": self.scheduler_remove_timer,
                "pause_timer": self.scheduler_pause_timer,
                "start_timer": self.scheduler_start_timer,
            }
        }

    def dispatcher(self, section, task, payload):
        section = self.routing.get(section, {})
        fn = section.get(task, None)

        if fn is not None:
            # noinspection PyArgumentList
            fn(payload.decode('ascii'))

    def schema_list(self, payload):
        self.logger.debug('Running schema/list')
        self.client.publish(topic=self.topic, payload="Schemas: " + ",".join(self.schemas.keys()))

    def schema_import(self, payload):
        self.logger.debug('Running schema/import')

        if self.schemas.import_all():
            self.client.publish(topic=self.topic, payload="Imported all schemas from disk")
        else:
            self.client.publish(topic=self.topic, payload="Import failed")

    def schema_dump(self, payload):
        self.logger.debug('Running schema/dump')

        if self.schemas.dump_all():
            self.client.publish(topic=self.topic, payload="Saved all schemas to disk")
        else:
            self.client.publish(topic=self.topic, payload="Failed to save all schemas to disk")

    def schema_add(self, payload):
        self.logger.debug('Running schema/add')

        data = self.schemas.load(payload)
        if not data:
            self.client.publish(topic=self.topic, payload="Invalid json for schema!")
            return False

        if self.schemas.add_schema(schema=data):
            self.client.publish(topic=self.topic, payload=f"Schema {data.get('name')} added to schemas")
        else:
            self.client.publish(topic=self.topic, payload="Failed to add payload to schemas")

    def schema_add_file(self, payload):
        self.logger.debug('Running schema/add_file')
        filename = os.path.join(self.schemas.schema_dir, payload)

        if os.path.isfile(filename):
            if self.schemas.add_schema_file(filename=filename):
                self.client.publish(topic=self.topic, payload=f"Schema {payload} loaded from file")
            else:
                self.client.publish(topic=self.topic, payload="Failed to load file from payload to schemas")
        else:
            self.client.publish(topic=self.topic, payload="Schema file from payload not found")

    def schema_remove(self, payload):
        self.logger.debug('Running schema/remove')

        if self.schemas.remove_schema(name=payload):
            self.client.publish(topic=self.topic, payload=f"Schema {payload} removed from schemas")
        else:
            self.client.publish(topic=self.topic, payload="Schema from payload not found")

    def scheduler_list(self, payload):
        self.logger.debug('Running scheduler/list')
        self.client.publish(topic=self.topic, payload="Schedulers: " + ",".join(self.scheduler.timers.keys()))

    def scheduler_stop(self, payload):
        self.logger.debug('Running scheduler/stop')

        if self.scheduler.stop():
            self.client.publish(topic=self.topic, payload="Stopped all schema timers")
        else:
            self.client.publish(topic=self.topic, payload="Failed to stop all schema timers")

    def scheduler_start(self, payload):
        self.logger.debug('Running scheduler/start')

        if self.scheduler.start():
            self.client.publish(topic=self.topic, payload="Started all schema timers")
        else:
            self.client.publish(topic=self.topic, payload="Failed to start all schema timers")

    def scheduler_add_timer(self, payload):
        self.logger.debug('Running scheduler/add_timer')

        schema = self.schemas.get(payload)
        if not schema:
            self.client.publish(topic=self.topic, payload="Failed to add timer: schema not found")
            return False

        if schema.get('name') in self.scheduler.timers:
            self.client.publish(topic=self.topic, payload="Failed to add timer: already exists!")
            return False

        self.scheduler.add_timer(name=schema.get('name'))

    def scheduler_remove_timer(self, payload):
        self.logger.debug('Running scheduler/remove_timer')

        schema = self.schemas.get(payload)
        if not schema:
            self.client.publish(topic=self.topic, payload="Failed to add timer: schema not found")
            return False

        self.scheduler.remove_timer(name=schema.get('name'))

    def scheduler_pause_timer(self, payload):
        self.logger.debug('Running scheduler/pause_timer')

        schema = self.schemas.get(payload)
        if not schema:
            self.client.publish(topic=self.topic, payload="Failed to add timer: schema not found")
            return False

        self.scheduler.pause_timer(name=schema.get('name'))

    def scheduler_start_timer(self, payload):
        self.logger.debug('Running scheduler/start_timer')

        schema = self.schemas.get(payload)
        if not schema:
            self.client.publish(topic=self.topic, payload="Failed to start timer: schema not found")
            return False

        self.scheduler.add_timer(name=schema.get('name'))
