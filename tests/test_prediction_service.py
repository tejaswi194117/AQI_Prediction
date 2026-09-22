import sys
import unittest


sys.path.insert(0, "src/api")
from prediction_service import prediction_from_features  # noqa: E402


class ConstantModel:
    def predict(self, data):
        self.last_columns = list(data.columns)
        return [75.125]


class PredictionServiceTests(unittest.TestCase):
    def test_prediction_uses_saved_feature_contract(self):
        model = ConstantModel()
        artifact = {
            "model": model,
            "model_name": "random_forest",
            "feature_columns": ["pm25_lag_1d", "average_temperature"],
        }

        result = prediction_from_features(artifact, {"pm25_lag_1d": 70.0})

        self.assertEqual(model.last_columns, ["pm25_lag_1d", "average_temperature"])
        self.assertEqual(result["predicted_pm25_next_day"], 75.12)
        self.assertEqual(result["predicted_aqi_category"], "Moderate")
        self.assertEqual(result["missing_features"], ["average_temperature"])


if __name__ == "__main__":
    unittest.main()
