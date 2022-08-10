#!/usr/bin/env bash

set -euo pipefail

podman build -t otlp-flamegraph .
docker-compose up &

read -p "Press enter to continue"

podman cp otlp-flamegraph-otel-collector-1:/data/otel.json data/otel.json
docker-compose down -v

./convert.py > data/out.json
