#!/usr/bin/env bash
set -u

name="${name}"
stackname="${stackname:-cphalo}"
grid="${stackname:-cphalo}"
version="${version:-latest}"
cpus="${cpus:-0.25}"
mem="${mem:-256}"
image="${image:-registry.marathon.mesos:5000/$name:$version}"

cat <<EOF
{
  "id": "/$name",
  "cpus": ${cpus},
  "mem": ${mem},
  "backoffFactor": 1.15,
  "backoffSeconds": 1,
  "maxLaunchDelaySeconds": 90,
  "container": {
    "type": "DOCKER",
    "docker": {
      "image": "${image}",
      "network": "BRIDGE"
    }
  },
  "labels": {
    "MARATHON_SINGLE_INSTANCE_APP": "true"
  },
  "upgradeStrategy": {
    "minimumHealthCapacity": 0,
    "maximumOverCapacity": 0
  },
  "healthChecks": [{
    "protocol": "COMMAND",
    "command": {
      "value": "/bin/true"
    },
    "gracePeriodSeconds": 300,
    "intervalSeconds": 60,
    "timeoutSeconds": 5,
    "maxConsecutiveFailures": 3
  }]
}
EOF
