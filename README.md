# OpenTelemetry to Chrome Tracing
A small tool to convert [OpenTelemetry] tracing data to the Google [Trace Event Format] that can be read using
[Google Chrome] / [Chromium] or [Speedscope].

## Usage
Use `run.sh` to start an [OpenTelemetry Collector] that provides the following interface:

| Port       | Interface               |
| ---------- | ----------------------- |
| `6831/udp` | [Jaeger] Thrift Compact |

Hit any key to stop the server. The [OpenTelemetry] -- stored in `./data/otel.json` -- will then be converted to the
[Trace Event Format] under `./data/out.json`. This file can then be opened in [Google Chrome] / [Chromium] or
[Speedscope].

## License

Licensed under either of these:

 * Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
 * MIT License ([LICENSE-MIT](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

### Contributing

Unless you explicitly state otherwise, any contribution you intentionally submit for inclusion in the work, as defined
in the Apache-2.0 license, shall be dual-licensed as above, without any additional terms or conditions.


[Chromium]: https://www.chromium.org/Home/
[Google Chrome]: https://www.google.com/chrome/index.html
[Jaeger]: https://www.jaegertracing.io/
[OpenTelemetry]: https://opentelemetry.io/
[OpenTelemetry Collector]: https://opentelemetry.io/docs/collector/
[Speedscope]: https://www.speedscope.app/
[Trace Event Format]: https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview
