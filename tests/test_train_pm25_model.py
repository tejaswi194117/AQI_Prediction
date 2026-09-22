import sys
import unittest

import pandas as pd


sys.path.insert(0, "src/models")
from train_pm25_model import select_feature_columns, time_based_split  # noqa: E402


class TrainPM25ModelTests(unittest.TestCase):
    def test_time_split_keeps_future_dates_out_of_training(self):
        data = pd.DataFrame(
            {
                "date": pd.date_range("2025-01-01", periods=10, freq="D"),
                "pm25_lag_1d": range(10),
                "target_pm25_next_day": range(10, 20),
            }
        )
        train, test = time_based_split(data)

        self.assertLess(train["date"].max(), test["date"].min())
        self.assertEqual(len(train), 8)
        self.assertEqual(len(test), 2)

    def test_target_is_not_a_feature(self):
        data = pd.DataFrame(
            {
                "date": ["2025-01-01"],
                "pm25_lag_1d": [10.0],
                "target_pm25_next_day": [15.0],
            }
        )
        self.assertEqual(select_feature_columns(data), ["pm25_lag_1d"])


if __name__ == "__main__":
    unittest.main()
