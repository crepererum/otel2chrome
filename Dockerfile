FROM docker.io/otel/opentelemetry-collector

COPY --chown=10001:10001 ./empty /data
