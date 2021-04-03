#!/usr/bin/env python3
import os
from setuptools import setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='json2mqtt',
    version='2021.03.28.001',
    url='https://github.com/fliphess/json2mqtt.git',
    author='Flip Hess',
    author_email='flip@fliphess.com',
    classifiers=[
        'Topic :: MQTT',
        'Topic :: Internet Of Things',
        'Programming Language :: Python :: 3.9',
    ],
    description='json2mqtt',
    install_requires=[
        'jmespath',
        'jsonschema',
        'multitimer',
        'paho-mqtt',
        'pid',
        'requests',
        'rfc3986-validator',
        'ruamel.yaml',
    ],
    packages=[
        'json2mqtt',
    ],
    entry_points=dict(console_scripts=[
        'json2mqtt = json2mqtt.main:main',
    ]),
)
