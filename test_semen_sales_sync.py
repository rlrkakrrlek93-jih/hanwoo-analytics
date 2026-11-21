import json, unittest
from pathlib import Path
from unittest.mock import patch
from semen_sales_sync import find_values,merge,BASELINE_2022,BASELINE_2023,BASELINE_2024,BASELINE_2025

TABLE= """<표 6> 배합사료 및 정액판매 추이
      2021   442  406 490
      2024   512  449 447
      2021   172   162   179   209   209   233   226   214   183   220   170   197  2,374
      2022   171   171   171   183   206   233   199   192   202   220   176   162  2,281
      2023   132   167   152   181   161   194   172   188   200   178   135   170  2,030
      2024   128   207   140   162   193   195   188   168   180   165   133   161  2,020
      2025   139   143   118   140   179                                             719
      자료 : 한국사료협회, 농협경제지주 한우개량사업소
"""

class TestSemenSales(unittest.TestCase):
    def test_2022_year_rounding_discrepancy(self):
        self.assertEqual(find_values(TABLE,2022),BASELINE_2022)
        self.assertEqual(sum(BASELINE_2022),2286)
        self.assertEqual(len(BASELINE_2022),12)

    def test_2023_year_is_12_months(self):
        self.assertEqual(find_values(TABLE,2023),BASELINE_2023)
        self.assertEqual(sum(BASELINE_2023),2030)

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
        self.assertEqual([obs[f'2022-{m:02d}'] for m in range(1,13)],BASELINE_2022)
        self.assertEqual([obs[f'2023-{m:02d}'] for m in range(1,13)],BASELINE_2023)
        self.assertEqual([obs[f'2024-{m:02d}'] for m in range(1,13)],BASELINE_2024)
        self.assertEqual([obs[f'2025-{m:02d}'] for m in range(1,6)],BASELINE_2025)
        self.assertEqual(sum(BASELINE_2024),2020)
        self.assertEqual(sum(BASELINE_2025),719)
        self.assertEqual(len(obs),50)
        self.assertEqual([obs[f'2025-{m:02d}'] for m in range(6,13)],[157.6,166.3,218.7,223.4,195.0,221.0,196.1])
        self.assertEqual([obs[f'2026-{m:02d}'] for m in range(1,3)],[170.6,201.8])
        self.assertTrue(all(r.get('source_name','').startswith('한국농촌경제연구원(KREI)')
            for r in data['records'] if r['month']>='2025-06'))
        self.assertEqual(len({r['month'] for r in data['records']}),50)
        self.assertEqual(len([r for r in data['records'] if r['month'].startswith('2025-')]),12)

if __name__=="__main__":
    unittest.main()
