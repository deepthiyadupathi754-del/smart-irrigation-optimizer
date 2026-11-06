import tempfile
import unittest
from pathlib import Path
from irrigation import initialize_database, add_plot, get_plots, add_log, get_logs, recommend_irrigation

class IrrigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.sqlite"
        initialize_database(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_read_plot_and_log(self):
        add_plot(self.db, name="North", location="Village A", area_acres=2, crop="Tomato", growth_stage="Vegetative", soil_type="Loamy", target_moisture=60)
        plot = get_plots(self.db)[0]
        self.assertEqual(plot["name"], "North")
        add_log(self.db, plot_id=plot["id"], irrigated_on="2026-11-06", water_mm=10, duration_minutes=30, energy_kwh=1.5, notes="Morning")
        self.assertEqual(get_logs(self.db)[0]["plot_name"], "North")

    def test_database_initialization_preserves_rows(self):
        add_plot(self.db, name="Keep", location="", area_acres=1, crop="Maize", growth_stage="Vegetative", soil_type="Other", target_moisture=50)
        initialize_database(self.db)
        self.assertEqual(len(get_plots(self.db)), 1)

    def test_recommendation_accounts_for_rain_and_area(self):
        dry = recommend_irrigation(30, 60, 0, "Vegetative", 1)
        rainy = recommend_irrigation(30, 60, 30, "Vegetative", 1)
        self.assertGreater(dry["water_mm"], 0)
        self.assertEqual(rainy["water_mm"], 0)
        self.assertEqual(dry["water_m3"], round(dry["water_mm"] * 4.047, 1))

    def test_invalid_recommendation_inputs_fail_clearly(self):
        with self.assertRaises(ValueError):
            recommend_irrigation(110, 60, 0, "Vegetative", 1)
        with self.assertRaises(ValueError):
            recommend_irrigation(40, 60, -1, "Vegetative", 1)

if __name__ == "__main__":
    unittest.main()
