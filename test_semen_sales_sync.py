import json, unittest
from pathlib import Path
from unittest.mock import patch
from semen_sales_sync import find_values,merge,BASELINE_2024,BASELINE_2025

TABLE= """<표 6> 배합사료 및 정액판매 추이
      2021   442  406 490
      2024   512  449 447
      2021   172   162   179   209   209   233   226   214   183   220   170   197  2,374
      2024   128   207   140   162   193   195   188   168   180   165   133   161  2,020
      2025   139   143   118   140   179                                             719
      자료 : 한국사료협회, 농협경제지주 한우개량사업소
"""

class TestSemenSales(unittest.TestCase):
    def test_2024_year_is_12_months(self):
        self.assertEqual(find_values(TABLE,2024),BASELINE_2024)
    def test_2025_total_is_not_extra_month(self):
        self.assertEqual(find_values(TABLE,2025),BASELINE_2025)
    def test_wrong_metric_is_not_accepted(self):
        self.assertIsNone(find_values("2024 512 449 447\n2025 472 440",2024))
    def test_merge_keeps_previous_on_different_source(self):
        previous={'records':[{'month':'2024-01','sold_thousand_str':128,'source_url':'first'}]}
        records,added=merge(previous,[('second',{2024:[127,207],2025:[139]})])
        values={r['month']:r['sold_thousand_str'] for r in records}
        self.assertEqual(values['2024-01'],128)
        self.assertEqual(values['2024-02'],207)
        self.assertEqual(values['2025-01'],139)
        self.assertEqual(added,2)
    def test_checked_in_history(self):
        data=json.loads(Path(__file__).with_name('semen_sales_data.json').read_text(encoding='utf-8'))
        obs={r['month']:r['sold_thousand_str'] for r in data['records']}
        self.assertEqual([obs[f'2024-{m:02d}'] for m in range(1,13)],BASELINE_2024)
        self.assertEqual([obs[f'2025-{m:02d}'] for m in range(1,6)],BASELINE_2025)
        self.assertEqual(sum(BASELINE_2024),2020)
        self.assertEqual(sum(BASELINE_2025),719)
        self.assertEqual(len(obs),17)

if __name__=="__main__":
    unittest.main()
