FROM docker.io/otel/opentelemetry-collector

COPY ./otel-collector-config.yml /etc/otel-collector-config.yaml
COPY --chown=10001:10001 ./empty /data

CMD ["--config=/etc/otel-collector-config.yaml"]
