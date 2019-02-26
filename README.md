# Statick ROS-M Upload Plugin
| Service | Status |
| ------- | ------ |
| Build   | [![Travis-CI](https://api.travis-ci.org/soartech/statick-rosm-registry.svg?branch=master)](https://travis-ci.org/soartech/statick-rosm-registry/branches) |
| PyPI    | [![PyPI version](https://badge.fury.io/py/statick-rosm-registry.svg)](https://badge.fury.io/py/statick-rosm-registry) |
| Codecov | [![Codecov](https://codecov.io/gh/soartech/statick-rosm-registry/branch/master/graphs/badge.svg)](https://codecov.io/gh/soartech/statick-rosm-registry) |


The Statick ROS-M Upload Plugin is a plugin for Statick to generate output compatible with the ROS-M registry.
You should only care about this plugin if you are involved with the ROS-M registry.

## Additions to Statick
This plugin introduces a new reporting plugin to Statick.
The plugin should be automatically detected the next time you run Statick.

## Use Cases
This plugin generates a .json file which can be manually uploaded to the ROS-M registry.
Future work will add support for automatically uploading to the registry.
