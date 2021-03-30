#!/usr/bin/env python3
import os
from setuptools import setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='toon2mqtt',
    version='2021.03.28.001',
    url='https://github.com/fliphess/toon2mqtt.git',
    author='Flip Hess',
    author_email='flip@fliphess.com',
    classifiers=[
        'Topic :: MQTT',
        'Topic :: Internet Of Things',
        'Programming Language :: Python :: 3.9',
    ],
    description='toon2mqtt',
    install_requires=[
        'jmespath',
        'multitimer',
        'paho-mqtt',
        'pid',
        'requests',
        'ruamel.yaml',
    ],
    packages=[
        'toon2mqtt',
        'toon2mqtt.schemas',
    ],
    entry_points=dict(console_scripts=[
        'toon2mqtt = toon2mqtt.main:main',
    ]),
)
