#!/usr/bin/env bash

set -euo pipefail

if hash podman &> /dev/null; then
    echo 'Using podman'
    dockpod=podman
elif hash docker &> /dev/null; then
    echo 'Using docker'
    dockpod=docker
else
    echo 'Need podman or docker'
    exit 1
fi

"$dockpod" build -t otel2chrome .
"$dockpod" run \
    --name otel2chrome \
    --publish 127.0.0.1:6831:6831/udp \
    --rm \
    --tty \
    otel2chrome &

read -r -p "Press any key to stop capture..."

"$dockpod" cp otel2chrome:/data/otel.json data/otel.json
"$dockpod" rm --force --volumes otel2chrome

./convert.py > data/out.json
