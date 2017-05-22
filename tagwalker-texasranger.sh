#!/bin/bash

set -ex

delay=300 # time in sec to delay between checks - initially set to 5 minutes, but might need adjusting.

run_tagwalker-texasranger() {
  /usr/local/bin/tagwalker-texasranger.py
}

while true; do
  echo "$(date) - Running Tagwalker Texas Ranger NOW"
  run_tagwalker-texasranger
  echo "$(date) - Tagwalker Texas Ranger Done - sleeping for $delay seconds"
  sleep $delay
done
