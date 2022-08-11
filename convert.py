#!/usr/bin/env python3
from dataclasses import dataclass
import json
import sys


@dataclass
class Event:
    ts: int
    name: str

    @classmethod
    def from_json(cls, event):
        return cls(
            ts=int(event["timeUnixNano"]),
            name=event["name"],
        )


@dataclass
class Span:
    span_id: str
    name: str
    parent_id: str
    start_time: int
    end_time: int
    events: list[Event]

    @classmethod
    def from_json(cls, span):
        return cls(
            span_id=span["spanId"],
            name=span["name"],
            parent_id=span["parentSpanId"],
            start_time=int(span["startTimeUnixNano"]),
            end_time=int(span["endTimeUnixNano"]),
            events=(
                [Event.from_json(event) for event in span["events"]]
                if "events" in span
                else []
            ),
        )


@dataclass
class Frame:
    i: int
    name: str
    parent: str


class FrameBuilder:
    def __init__(self):
        self.frames = {}

    def create_frame(self, span, level):
        i = level * 1_000_000 + len(self.frames)
        self.frames[span.span_id] = Frame(i, span.name, span.parent_id)
        return i

    def to_dict(self):
        out = {}

        for k, v in sorted(self.frames.items(), key=lambda x: x[1].i):
            obj = {
                "name": v.name,
            }

            try:
                obj["parent"] = self.frames[v.parent].i
            except KeyError:
                pass

            out[str(v.i)] = obj

        return out


def iter_spans(batch):
    """
    Iterate over spans.
    """
    for resource_span in batch["resourceSpans"]:
        for scope_spans in resource_span["scopeSpans"]:
            for span in scope_spans["spans"]:
                yield Span.from_json(span)


def ns_to_us(t: int) -> float:
    """
    Convert nanoseconds to microseconds.
    """
    return t / 1000.0


def expand_time_ranges(time_ranges, children):
    # fill task stack w/ roots (i.e. spans w/o any children)
    roots = set(time_ranges)
    for span_id, child_ids in children.items():
        # ignore parent->child relationships if the parent is not part of the trace
        if span_id not in time_ranges:
            continue

        for child_id in child_ids:
            roots.remove(child_id)

    stack = [
        (span_id, 0)
        for span_id in sorted(roots, key=lambda span_id: time_ranges[span_id])
    ]
    added_children = set()
    out = {}

    while stack:
        current, depth = stack[-1]

        if current not in added_children and current in children:
            child_ids = sorted(
                (
                    child_id
                    for child_id in children[current]
                    # ignore parent->child relationships if the parent is not part of the trace
                    if child_id in time_ranges
                )
            )
            for child_id in child_ids:
                stack.append((child_id, depth + 1))
            added_children.add(current)
            continue

        stack.pop()

        t_begin, t_end = time_ranges[current]

        # speedscope is messy and uses some timestamp-based stack, so "shrink" the event by a few NS depending on the
        # stack size to avoid overlaps
        # TODO: this is a hack, we should have a proper overlap fix
        add = 100 - depth
        t_begin -= add
        t_end += add

        if current in children:
            child_ids = children[current]
            t_begin = min(
                t_begin,
                min(out[i][0] for i in child_ids),
            )
            t_end = max(
                t_end,
                max(out[i][1] for i in child_ids),
            )
        out[current] = (t_begin, t_end, depth)

    return out


def main():
    frame_builder = FrameBuilder()

    min_start = None
    time_ranges = {}
    children = {}
    events = []

    with open("./data/otel.json") as f:
        for line in f:
            batch = json.loads(line)
            for span in iter_spans(batch):
                actual_min = min(span.start_time, span.end_time)
                actual_max = max(span.start_time, span.end_time)

                if span.events:
                    events_min = min(event.ts for event in span.events)
                    events_max = max(event.ts for event in span.events)
                    actual_min = min(events_min, actual_min)
                    actual_max = max(events_max, actual_max)

                time_ranges[span.span_id] = (actual_min, actual_max)
                try:
                    children[span.parent_id].append(span.span_id)
                except KeyError:
                    children[span.parent_id] = [span.span_id]

        f.seek(0)

        time_ranges = expand_time_ranges(time_ranges, children)
        min_start = min(t[0] for t in time_ranges.values()) if time_ranges else 0

        id_counter = 1

        for line in f:
            batch = json.loads(line)
            for span in iter_spans(batch):
                start_time, end_time, level = time_ranges[span.span_id]
                frame_id = frame_builder.create_frame(span, level)
                span_name = f"{span.name} ({span.span_id})"
                category = span.name

                span_id = id_counter
                id_counter += 1

                events.append(
                    {
                        "name": span_name,
                        "ph": "B",
                        "ts": ns_to_us(start_time - min_start),
                        "pid": 1,  # for Chrome
                        "cat": category,  # for color
                        "sf": frame_id,
                        "id": span_id,
                        "_level": level,
                    }
                )
                for event in span.events:
                    event_id = id_counter
                    id_counter += 1

                    event_name = f"{event.name} ({span.span_id})"

                    events.append(
                        {
                            "name": event_name,
                            "ph": "i",
                            "ts": ns_to_us(event.ts - min_start),
                            "pid": 1,  # for Chrome
                            "cat": category,  # for color
                            "sf": frame_id,
                            "id": event_id,
                            "s": "t",
                            "_level": level,
                        }
                    )

                events.append(
                    {
                        "name": span_name,
                        "ph": "E",
                        "ts": ns_to_us(end_time - min_start),
                        "pid": 1,  # for Chrome
                        "cat": category,  # for color
                        "sf": frame_id,
                        "id": span_id,
                        "_level": level,
                    }
                )

    events = sorted(
        events,
        key=lambda e: (
            e["ts"],
            e["ph"],
            # begin events start from lowest to highest level, end events the other way around
            e["_level"] if e["ph"] == "B" else -e["_level"],
        ),
    )

    out = {
        "traceEvents": events,
        "displayTimeUnit": "ns",
        "stackFrames": frame_builder.to_dict(),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
