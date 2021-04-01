# Toon2mqtt

Toon2mqtt is a little webcrawler that crawls the integration endpoints of a rooted toon and sends the values to a MQTT broker.

I use it to show data from my rooted toon in home-assistant.

It starts a bunch of timers that crawl several endpoints on the toon local device.


## Clone the repo

```
git clone https://github.com/fliphess/toon2mqtt.git && cd toon2mqtt
```


## Install in a virtualenv

### Create venv

Create a virtualenv and install `toon2mqtt` and its requirements:

```
python3 -m venv venv
source venv/bin/activate

pip install  .
```

### Create a config

A config file is created on first run if nonexistent:

```
toon2mqtt --settings settings.yaml --init

vim settings.yaml
```

### Run toon2mqtt

```
toon2mqtt --config settings -vvv
```


## Install using docker

### Build the container:

```
docker build -t toon2mqtt .
```

### Create a config file (created if nonexistent):

```
docker run -ti -v "/tmp:/cfg" --rm toon2mqtt  --config /cfg/settings.yaml

mv /tmp/settings.yaml .
vim settings.yaml
```

### Run

```
docker run \
	--rm \
	-ti \
	-v "$(pwd)/settings.yaml:/opt/toon2mqtt/settings.yaml" \
        -v "$(pwd)/schemas:/opt/toon2mqtt/schemas" \
	toon2mqtt --config settings.yaml -vvv
```


## Home Assistant Addon

TODO


## The `settings.yaml` file 

The config file will be created on first run if the config file does not exist. It will fill up the required fields with the default values. This will not automagically work, as you need to configure your broker. 

A full configuration file contains:

```
## MQTT Broker config
mqtt_host: "some.broker"
mqtt_port: 1883
mqtt_username: "username"
mqtt_password: "password"
mqtt_topic: home/toon2mqtt

mqtt_ssl: true
mqtt_cert: "/etc/ssl/cert.pem"


## Toon settings
toon_host: 10.30.1.127
toon_port: 80


## Schema settings
schema_dir: ./schemas
```

## Schemas

Schemas are json definitions that can be used to validate
the json data returned from toon (or any other json api).

There are some predefined json schemas that can be used
in the schemas directory in this repository.

Additionally, you can write your own schemas and feed them
to this service as a file or over MQTT.

A schema consists of 4 main elements:

- `name`     - The name of the schema
- `endpoint` - The api endpoint to retrieve json data from (IE: `/some/endpoint` )
- `interval` - The time in seconds between retrievals
- `fields`   - A list of dictionaries defining fields that
               are to be expected in the retrieved json.

Optional elements are:

- `topic` - Override the topic where to send the data to.
          (The topic is appended with the value of the  `name` element)
- `host`  - The host of the http api to connect to.
- `port`  - The port of the http api to connect to (set `use_ssl: true` to enable ssl)
- `use_ssl`   - Use ssl for this connection

A `field` element consists of 2 fields:

- `path`   - The jmespath of the value to send to mqtt
- `type`   - The type of data in this field

The types available:
- String
- Integer
- Float
- Boolean
- None
- List
- Dictionary


Example: retrieve the module version data from the toon and send over MQTT
```
{
    "name": "module_version",
    "endpoint": "/happ_thermstat?action=getModuleVersion",
    "interval": 3600,
    "fields": {
        "mmb": {
            "type": "Boolean",
            "path": "mmb"
        },
        "version": {
            "type": "Integer",
            "path": "version"
        }
    }
}
```

The topics used to publish to in this example are:
- `home/toon2mqtt/module_version/mmb`
- `home/toon2mqtt/module_version/version`

Or you can override the topics using the `topic` field.

By setting the host, port and ssl settings, in the schema, any json api can be crawled periodically using this tool, as long as you define a schema for the json fields you want to send to mqtt.


## Controlling the daemon

You can control the daemon over MQTT.

You can start and stop timers, add, remove and reload schemas.


## MQTT Topics:


### Publishing topics:

The topics to which the retrieved data and response metrics are send:
```
home/toon2mqtt/<schema name>/<key>               # Retrieved json keys from api
home/toon2mqtt/<schema name>/request/success     # If the last request succeeded
home/toon2mqtt/<schema name>/request/status_code # The status code of the last request
home/toon2mqtt/<schema name>/request/reason      # The reason of the last request
home/toon2mqtt/<schema name>/request/url         # The full url of the request
```

### Command topics

The topics to create and manipulate the schemas

```
home/toon2mqtt/command/schema/add                # Add a json schema
home/toon2mqtt/command/schema/remove             # Remove/Disable a schema
home/toon2mqtt/command/schema/list               # List all json schemas
home/toon2mqtt/command/schema/import             # Import all schemas from disk
home/toon2mqtt/command/schema/dump               # Write all schemas to disk
```

Schemas can be manipulated, loaded and written to disk. They are used by the scheduler, but not automatically renewed.
To update the timers that use the schemas, you additionally need to reload the the scheduler task(s)

This is useful to reuse a schema, only changing the host or portname for another environment polling the same data, using only MQTT


### Timer topics

Timers are the actual crawling of the endpoint. These can be controlled separately from the schemas that are used to instruct what to crawl and how often.

```
home/toon2mqtt/command/scheduler/stop            # Stop all timers
home/toon2mqtt/command/scheduler/start           # Start all times
home/toon2mqtt/command/scheduler/reload          # Reload the scheduler, start and stop all timers
home/toon2mqtt/command/scheduler/add_timer       # Add a timer using a json schema, do not save anything to schemas, just start the timer
home/toon2mqtt/command/scheduler/remove_timer    #
home/toon2mqtt/command/scheduler/restart_timer   #
home/toon2mqtt/command/scheduler/stop_timer      #
home/toon2mqtt/command/scheduler/remove          #
```

## TODO

To be added:

- manipulate (edit/change) schemas
- MQTT control
- Better error catching for fetch
- Request timings metrics
- Only start missing timers, do not reload and stop the others
- Allow changing config

