import logging
import unittest

from log_record_attribute_injector_kit import LogRecordAttributeInjector


class LogRecordAttributeInjectorTests(unittest.TestCase):
    def test_injects_attributes_into_record(self):
        injector = LogRecordAttributeInjector(request_id="req-123", hostname="host-1")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname=__file__, lineno=1,
            msg="hello", args=(), exc_info=None,
        )
        result = injector.filter(record)
        self.assertTrue(result)
        self.assertEqual(record.request_id, "req-123")
        self.assertEqual(record.hostname, "host-1")

    def test_does_not_overwrite_existing_attribute(self):
        injector = LogRecordAttributeInjector(request_id="global")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname=__file__, lineno=1,
            msg="hello", args=(), exc_info=None,
        )
        record.request_id = "per-record"
        injector.filter(record)
        self.assertEqual(record.request_id, "per-record")

    def test_filter_returns_true_even_with_no_attributes(self):
        injector = LogRecordAttributeInjector()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname=__file__, lineno=1,
            msg="hello", args=(), exc_info=None,
        )
        self.assertTrue(injector.filter(record))

    def test_attributes_property_returns_copy(self):
        injector = LogRecordAttributeInjector(request_id="abc")
        attrs = injector.attributes
        attrs["request_id"] = "changed"
        self.assertEqual(injector.attributes["request_id"], "abc")

    def test_with_hostname_sets_hostname(self):
        injector = LogRecordAttributeInjector.with_hostname(request_id="abc")
        attrs = injector.attributes
        self.assertIn("hostname", attrs)
        self.assertIsInstance(attrs["hostname"], str)
        self.assertEqual(attrs["request_id"], "abc")

    def test_with_hostname_does_not_override_explicit_hostname(self):
        injector = LogRecordAttributeInjector.with_hostname(hostname="explicit")
        self.assertEqual(injector.attributes["hostname"], "explicit")

    def test_can_be_attached_to_logger_and_used_by_handler(self):
        import io

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(request_id)s %(message)s"))
        logger = logging.getLogger("test.injector")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.addFilter(LogRecordAttributeInjector(request_id="req-1"))
        logger.info("hello")
        self.assertEqual(stream.getvalue().strip(), "req-1 hello")


if __name__ == "__main__":
    unittest.main()
