import unittest
from precision_probe import summarize_table

class PrecisionProbeTest(unittest.TestCase):
    def test_decimal_is_detected(self):
        html = '<table id="mainTable"><thead><tr><th name="x">항목</th></tr></thead><tbody><tr><td>한우</td><td>거세우</td><td>51,288</td><td>6.8</td><td>7.0</td></tr></tbody></table>'
        result = summarize_table(html)
        self.assertEqual(result["data_row_count"], 1)
        self.assertEqual([x["value"] for x in result["nonzero_decimal_samples"]], ["6.8"])
        self.assertEqual(result["numeric_cell_count"], 3)

    def test_zero_decimal_is_not_inferred_precision(self):
        html = '<table id="mainTable"><tbody><tr><td>7.0</td><td>5</td></tr></tbody></table>'
        self.assertEqual(summarize_table(html)["nonzero_decimal_samples"], [])

    def test_missing_table_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "mainTable"):
            summarize_table("<div>No table</div>")

if __name__ == "__main__":
    unittest.main()
