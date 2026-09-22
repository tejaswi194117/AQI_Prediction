import sys
import unittest

import pandas as pd


sys.path.insert(0, "src/features")
from build_training_dataset import build_features  # noqa: E402


class BuildTrainingDatasetTests(unittest.TestCase):
    def test_next_day_target_and_lag_are_leakage_safe(self):
        source = pd.DataFrame(
            {
                "location_id": [1, 1, 1, 1],
                "date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
                "pm25": [10.0, 20.0, 30.0, 40.0],
            }
        )

        features = build_features(source)
        second_day = features.iloc[1]

        self.assertEqual(second_day["pm25_lag_1d"], 10.0)
        self.assertEqual(second_day["target_pm25_next_day"], 30.0)
        self.assertTrue(pd.isna(features.iloc[-1]["target_pm25_next_day"]))

    def test_gap_does_not_become_a_one_day_lag(self):
        source = pd.DataFrame(
            {
                "location_id": [1, 1],
                "date": ["2025-01-01", "2025-01-03"],
                "pm25": [10.0, 30.0],
            }
        )

        features = build_features(source)
        third_day = features.iloc[1]

        self.assertTrue(pd.isna(third_day["pm25_lag_1d"]))
        self.assertTrue(pd.isna(features.iloc[0]["target_pm25_next_day"]))


if __name__ == "__main__":
    unittest.main()
