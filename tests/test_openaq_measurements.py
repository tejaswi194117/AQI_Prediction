import os
import sys
import unittest


sys.path.insert(0, "src/ingestion")
import openaq_measurements as measurements  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class OpenAQMeasurementsTests(unittest.TestCase):
    def setUp(self):
        self.previous_granularity = measurements.GRANULARITY
        self.previous_page_size = measurements.PAGE_SIZE
        self.previous_start = os.environ.get("OPENAQ_HISTORY_START_DATE")
        self.previous_end = os.environ.get("OPENAQ_HISTORY_END_DATE")
        measurements.GRANULARITY = "days"
        measurements.PAGE_SIZE = 2
        os.environ["OPENAQ_HISTORY_START_DATE"] = "2025-01-01"
        os.environ["OPENAQ_HISTORY_END_DATE"] = "2025-01-02"

    def tearDown(self):
        measurements.GRANULARITY = self.previous_granularity
        measurements.PAGE_SIZE = self.previous_page_size
        if self.previous_start is None:
            os.environ.pop("OPENAQ_HISTORY_START_DATE", None)
        else:
            os.environ["OPENAQ_HISTORY_START_DATE"] = self.previous_start
        if self.previous_end is None:
            os.environ.pop("OPENAQ_HISTORY_END_DATE", None)
        else:
            os.environ["OPENAQ_HISTORY_END_DATE"] = self.previous_end

    def test_fetches_all_pages_and_enriches_measurements(self):
        calls = []

        def fake_get(url, **kwargs):
            calls.append((url, kwargs))
            page = kwargs["params"]["page"]
            payloads = {
                1: {"meta": {"found": 3}, "results": [{"value": 10}, {"value": 20}]},
                2: {"meta": {"found": 3}, "results": [{"value": 30}]},
            }
            return FakeResponse(payloads[page])

        records = measurements.fetch_sensor_history(
            {"id": 12, "location_id": 99}, {"X-API-Key": "test"}, fake_get
        )

        self.assertEqual(len(records), 3)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0][0].endswith("/12/days"))
        self.assertEqual(records[0]["location_id"], 99)
        self.assertEqual(records[0]["aggregation"], "days")


if __name__ == "__main__":
    unittest.main()
