# Toon2mqtt

Toon2mqtt is a little webcrawler that crawls the integration endpoints of a rooted toon and sends the values to a MQTT broker. 

I use it to show data from my rooted toon in home-assistant.

It starts a bunch of timers that crawl several endpoints on the toon local device.


## Setup

### Clone the repo

```
git clone https://github.com/fliphess/toon2mqtt.git && cd toon2mqtt
```

### Install

#### Install in a virtualenv

Create a virtualenv and install `toon2mqtt` and its requirements:

```
python3 -m venv venv
source venv/bin/activate

pip install .
```

Create a config file (created if nonexistent):

```
toon2mqtt --settings settings.yaml 

vim settings.yaml
```

#### Install using docker 

Build the container:

```
docker build -t toon2mqtt .
```

Create a config file (created if nonexistent):

```
docker run -ti -v "/tmp:/cfg" --rm toon2mqtt  --config /cfg/settings.yaml


mv /tmp/settings.yaml . 
vim settings.yaml
```


## Running 

### In a virtualenv 

```
toon2mqtt --config settings -vvv
```

### In a container

```
docker run \
	--rm \
	-ti \
	-v "$(pwd)/settings.yaml:/opt/toon2mqtt/settings.yaml" 
	toon2mqtt --config settings.yaml -vvv
```


## Home Assistant Addon











