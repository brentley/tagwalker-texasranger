#!/usr/bin/env bash
set -u

DIR="$PWD"
GIT_SHA=$(git rev-parse HEAD 2>/dev/null | cut -c 1-7)
version="${GIT_SHA}"
name="$(basename $DIR)"
name="tagwalker-texasranger"
image="${image:-brentley/$name}"

docker push $image:$version
docker push $image:latest
