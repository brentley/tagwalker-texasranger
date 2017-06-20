#!/bin/bash

set -ex

delay=900 # time in sec to delay between checks - initially set to 5 minutes, but might need adjusting.

while /usr/local/bin/tagwalker-texasranger.py; do
  sleep $delay
done
