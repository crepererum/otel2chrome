#!/usr/bin/env bash

set -euo pipefail

podman build -t otel2chrome .
docker-compose up &

read -p "Press enter to continue"

podman cp otel2chrome-otel2chrome1:/data/otel.json data/otel.json
docker-compose down -v

./convert.py > data/out.json
