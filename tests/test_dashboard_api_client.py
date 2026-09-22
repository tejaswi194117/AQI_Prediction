import sys
import unittest


sys.path.insert(0, "dashboard")
from api_client import predict  # noqa: E402


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"predicted_pm25_next_day": 44.0}


class DashboardClientTests(unittest.TestCase):
    def test_prediction_posts_features_to_normalized_api_url(self):
        calls = []

        def fake_post(url, **kwargs):
            calls.append((url, kwargs))
            return FakeResponse()

        result = predict("http://localhost:8000/", {"pm25_lag_1d": 40}, fake_post)

        self.assertEqual(result["predicted_pm25_next_day"], 44.0)
        self.assertEqual(calls[0][0], "http://localhost:8000/predict")
        self.assertEqual(calls[0][1]["json"], {"features": {"pm25_lag_1d": 40}})


if __name__ == "__main__":
    unittest.main()
