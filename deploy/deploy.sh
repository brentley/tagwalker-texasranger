#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GIT_SHA=$(git rev-parse HEAD 2>/dev/null | cut -c 1-7)

export master=${master:-master.mesos}
export version="${GIT_SHA}"
export name="tagwalker-texasranger"
export image="${image:-registry.marathon.mesos:5000/$name:$version}"
export stackname="${stackname:-$(curl -m3 -s http://$master:5050/state |jq -r '.cluster')}"

curl="curl -k --fail -v -m3 -s -i -L -X PUT"
endpoint="http://$master:8080/v2/apps/$name?force=true"

echo syntax check the json
$DIR/marathon.json.sh | jq .

echo $DIR
$curl -H 'Content-Type: application/json' $endpoint -d "$($DIR/marathon.json.sh)"
