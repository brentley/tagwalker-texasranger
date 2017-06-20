#!/usr/bin/env bash
set -u

DIR="$PWD"
GIT_SHA=$(git rev-parse HEAD 2>/dev/null | cut -c 1-7)
DRAAS_REPO=ecs-services-registry-internal.ng.cloudpassage.com:5000
version="${GIT_SHA}"
name="$(basename $DIR)"
name="tagwalker-texasranger"
image="${image:-${DRAAS_REPO}/${name}}"


docker push $image:$version
docker push $image:latest
