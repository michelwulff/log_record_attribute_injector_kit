# log_record_attribute_injector_kit

A `logging.Filter` subclass that adds predefined attributes such as `request_id` and `hostname` to every `LogRecord` before formatting.

```python
import logging

from log_record_attribute_injector_kit import LogRecordAttributeInjector

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addFilter(LogRecordAttributeInjector(request_id="req-42", hostname="web-1"))

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(request_id)s %(hostname)s %(message)s"))
logger.addHandler(handler)

logger.info("started")
# req-42 web-1 started
```

## Why this exists

Standard `logging` records do not carry application context like a request id or the hostname.  The usual workarounds are to pass `extra=` at every call site, or to subclass `logging.Logger` and override `makeRecord`.  The first is repetitive and easy to forget; the second changes the logger class for the whole process and is awkward to compose with existing configuration.

A filter is the smallest hook that sees every record and can mutate it before any formatter runs.  This library provides that filter and nothing else.  The trade-off is that attributes are static for the lifetime of the filter: a single filter cannot carry a different `request_id` per request.  For per-request values, create a short-lived filter or set the attribute on the record before it reaches the filter; the filter will not overwrite an attribute that is already present.

The hostname is resolved once when the filter is created, not on every record, because a syscall per log line is not acceptable in a hot path.  If the hostname can change while the process runs, recreate the filter.

## API

`LogRecordAttributeInjector(**attributes)`

Creates a filter.  Every keyword argument becomes an attribute name on the record.  `filter(record)` always returns `True`, so records are never dropped.

The `attributes` property returns a copy of the configured attributes.

`LogRecordAttributeInjector.with_hostname(**attributes)`

Class method that adds `hostname` (resolved at call time) unless the caller already passed one.

## Edge case

If a record already has an attribute with the same name, the filter leaves it alone.  This means a per-record value always wins over the global filter value, which is what you want when a request sets its own `request_id` and a default filter is also installed.
