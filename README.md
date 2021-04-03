# Json HTTP to MQTT utility.

Json2mqtt is a little python daemon that retrieves data
from json api's and send selected fields to an MQTT broker.

I wrote it to retrieve temperature data from my rooted Toon thermostat,
but while still in the initial build phase, the toon focus was dropped
and it continued as a more generic tool.

It is very useful to retrieve data from any api that returns json,
select the required fields using jmespath and send it to a topic on a mqtt broker.
It starts a bunch of timers that crawl several endpoints.

Using the schemas you can give fine grained instructions to the daemon to crawl,
both using predefined files or over MQTT.

## Timers

Timers are http requests that are executed a defined amount of times or keep running periodically,
that are running concurrently and send the defined data to MQTT

all data that should be send to the broker can be defined in a schema, which is a json definition
that is used to pick all the required fields from the returned json api.

All json files that match the jsonschema definition in the schemas directory that is defined in the config file
are loaded at startup unless explicitly disabled setting `"enabled": false` in the schema definition.

## Schemas

### Introduction

There are some predefined json schemas that can be loaded
from the schemas directory in this repository or over MQTT
that can be used to poll a rooted Toon.

Additionally, you can write your own schemas and feed them
to this service as a file or over MQTT.

### Schema required fields

A schema consists of 4 main (required) elements:

- `name`     - The name of the schema
- `url` -    - The url to retrieve json data from

- `interval` - The time in seconds between retrievals

- `fields`   - A list of dictionaries each containing a path and a type element defining fields that
               are to be expected in the retrieved json. (more info below)


### Additional schema elements

Additional optional elements are:

- `topic`    - Override the topic where to send the data to.
               (The topic is appended with the value of the  `name` element)

- `count`    - How many times the crawl should be performed. Default is `-1`,
               which keeps repeating the request until the timer is stopped,
               waiting to be started again

- `timeout`  - The timeout for the http requests (Default is 10s)

- `headers`  - A list of key value pairs with additional headers (can be used for host, auth, user-agent etc)

- `enabled`  - Explicitly enable or disable the schema at startup (The schema needs to exist on disk to be loaded at startup)


### Fields

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


### Schema example

Example: retrieve the module version data from the toon and send over MQTT

```
{
    "name": "module_version",
    "url": "http:///toon.local/happ_thermstat?action=getModuleVersion",
    "interval": 3600,
    "timeout": 30,
    "headers": [
        {
            "key": "User-Agent",
            "value": "Json2MQTT"
        },
        {
            "key": "Authorization",
            "value": "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
        }
    ],
    "fields": {
        "mmb": {
            "type": "String",
            "path": "mmb"
        },
        "version": {
            "type": "String",
            "path": "version"
        }
    }
}
```

The topics used to publish to in this example are:
- `home/json2mqtt/module_version/mmb`
- `home/json2mqtt/module_version/version`

Or you can override the topics using the `topic` field.
By setting the host, port and ssl settings, in the schema, any json api can be crawled periodically using this tool, as long as you define a schema for the json fields you want to send to mqtt.


## Install

### Clone the repo

```
git clone https://github.com/fliphess/json2mqtt.git && cd json2mqtt
```


### Install in a virtualenv

#### Create venv

Create a virtualenv and install `json2mqtt` and its requirements:

```
python3 -m venv venv
source venv/bin/activate

pip install  .
```

#### Create a config

A config file is created on first run if nonexistent:

```
json2mqtt --settings settings.yaml --init

vim settings.yaml
```

### Run json2mqtt

```
json2mqtt --config settings -vvv
```


## Install using docker

### Build the container:

```
docker build -t json2mqtt .
```

### Create a config file

```
docker run -ti -v "/tmp:/cfg" --rm json2mqtt  --config /cfg/settings.yaml

mv /tmp/settings.yaml .
vim settings.yaml
```

### Run

```
docker run \
	--rm \
	-ti \
	-v "$(pwd)/settings.yaml:/opt/json2mqtt/settings.yaml" \
        -v "$(pwd)/schemas:/opt/json2mqtt/schemas" \
	json2mqtt --config settings.yaml -vvv
```


## The `settings.yaml` file

The config file will be created on first run if it does not exist.
It will fill up the required fields with the default values.
This will not work out of the box, as you need to configure your broker first.

A full configuration file contains:

```
mqtt_host: "some.broker"
mqtt_port: 1883
mqtt_username: "username"
mqtt_password: "password"
mqtt_topic: home/toon2mqtt

mqtt_ssl: true
mqtt_cert: "/etc/ssl/cert.pem"

schema_dir: ./schemas
```


## Controlling the daemon

You can control the daemon over MQTT.

You can start and stop timers, add, remove and reload schemas.


## MQTT Topics:

### Publishing topics:

The topics to which the retrieved data and response metrics are send:
```
home/json2mqtt/<schema name>/<key>               # Retrieved json keys from api
home/json2mqtt/<schema name>/request/success     # If the last request succeeded
home/json2mqtt/<schema name>/request/status_code # The status code of the last request
home/json2mqtt/<schema name>/request/reason      # The reason of the last request
home/json2mqtt/<schema name>/request/url         # The full url of the request
```

### Command topics

The topics to create and manipulate the schemas

```
<<<<<<< HEAD
home/toon2mqtt/command/schema/add                # Add a json schema
home/toon2mqtt/command/schema/remove             # Remove/Disable a schema
home/toon2mqtt/command/schema/list               # List all json schemas
home/toon2mqtt/command/schema/import             # Import all schemas from disk
home/toon2mqtt/command/schema/dump               # Write all schemas to disk
=======
home/json2mqtt/command/schema/add                # Add a json schema from the mqtt payload
home/json2mqtt/command/schema/add_file           # Add a json schema from a file that is present on disk
home/json2mqtt/command/schema/remove             # Remove/Disable a schema
home/json2mqtt/command/schema/list               # List all json schemas
home/json2mqtt/command/schema/import             # Import all schemas from disk
home/json2mqtt/command/schema/dump               # Write all schemas to disk
>>>>>>> b600184 (Rename and add some more features)
```

Schemas can be manipulated, loaded and written to disk. They are used by the scheduler, but not automatically renewed.
To update the timers that use the schemas, you additionally need to reload the the scheduler task(s)

This is useful to reuse a schema, only changing the host or portname for another environment polling the same data, using only MQTT


### Timer topics

Timers are the actual crawling of the endpoint. These can be controlled separately from the schemas that are used to instruct what to crawl and how often.

```
home/json2mqtt/command/scheduler/list            # List all timers
home/json2mqtt/command/scheduler/stop            # Stop all timers
home/json2mqtt/command/scheduler/start           # Start all times
home/json2mqtt/command/scheduler/add_timer       # Add a timer using a json schema, do not save anything to schemas, just start the timer
home/json2mqtt/command/scheduler/remove_timer    # Remove a timer
home/json2mqtt/command/scheduler/start_timer     # Start a stopped timer
home/json2mqtt/command/scheduler/pause_timer     # Stop a running timer
```

