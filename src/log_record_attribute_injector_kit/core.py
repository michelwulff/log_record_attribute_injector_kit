import logging
import socket


class LogRecordAttributeInjector(logging.Filter):
    """A logging filter that adds predefined attributes to every LogRecord.

    The filter is attached to a logger or handler and runs before formatting.
    It copies the given attributes onto the record, but only if the record
    does not already have them.  This lets a record created inside a request
    scope carry its own request_id without being overwritten by the global
    value.  The trade-off is that a global attribute can never override an
    explicit per-record value; that is deliberate, because per-record context
    is more specific and should win.

    ``hostname`` is resolved once at construction time.  Resolving it on every
    record would add a syscall to every log line, which is unacceptable in a
    hot path.  If the hostname changes while the process runs, the filter must
    be recreated; that is a rare enough case to accept.
    """

    def __init__(self, **attributes):
        """Create the filter with the attributes to inject.

        Example::

            injector = LogRecordAttributeInjector(request_id="abc", hostname=socket.gethostname())

        Any keyword argument becomes an attribute name on the record.  Names
        that collide with ``logging.LogRecord`` internals (for example
        ``msg`` or ``levelname``) are allowed but will only be set if the
        record does not already have them, which is almost never the case for
        standard fields.
        """
        super().__init__()
        self._attributes = dict(attributes)

    def filter(self, record):
        """Inject the configured attributes into *record*.

        Returns ``True`` so the record is always processed.  A filter that
        returns ``False`` would silently drop the record, which is not the
        purpose of this class.
        """
        for name, value in self._attributes.items():
            if not hasattr(record, name):
                setattr(record, name, value)
        return True

    @property
    def attributes(self):
        """Return a copy of the attributes this filter will inject."""
        return dict(self._attributes)

    @classmethod
    def with_hostname(cls, **attributes):
        """Create a filter that includes the current hostname.

        This is a convenience for the common case.  The hostname is resolved
        once here, not on every record.
        """
        attributes.setdefault("hostname", socket.gethostname())
        return cls(**attributes)
