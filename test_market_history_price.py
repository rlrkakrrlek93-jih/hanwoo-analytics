import unittest
import json
from pathlib import Path
from unittest.mock import patch
from market_supply_sync import parse_grading,build,desired_months

def mock_response():
    header=('<thead><tr><th name="A">품종</th><th name="B">성별</th><th name="C">도체중</th>'
      '<th name="M202401" colspan="8">2024.01</th></tr>'
      '<tr><th name="00" colspan="8">전국</th></tr><tr>'
      +''.join('<th name="T%03d">항목</th>'%i for i in range(1,9))+'</tr></thead>')
    rows=''
    for sex,num,price in [('암',42000,16600),('수',500,11500),('거세',60000,19800)]:
        vals=[num,650,460,12,95,62,6,price]
        rows+='<tr><td>한우</td><td>%s</td><td>전체</td>%s</tr>'%(sex,''.join(
            '<td title="%d">%d</td>'%(v,v) for v in vals))
    return {'result':['<table id="mainTable">'+header+'<tbody>'+rows+'</tbody></table>']}

class TestHistoricalPrice(unittest.TestCase):
    def test_requested_history_starts_2024(self):
        with patch('market_supply_sync.last_complete',return_value='2026-10'):
            months=desired_months()
        self.assertEqual(months[0],'202401')
        self.assertEqual(months[-1],'202610')
        self.assertEqual(len(months),34)
    def test_sex_specific_prices_from_published_cells(self):
        counts,parts=parse_grading(mock_response())
        self.assertEqual(counts['2024-01'],102500)
        price=parts['2024-01']['auction_price_by_sex']
        self.assertEqual(price,{'female':16600,'male':11500,'steer':19800})
    def test_no_fabricated_overall_price(self):
        count,parts=parse_grading(mock_response())
        d=build({'2024-01':3200000},{'2024-01':{'breeding':400000,'fattening':400000,'integrated':2400000}},
                count,parts)
        r=d['records'][0]
        self.assertNotIn('auction_price_total',r)
        self.assertEqual(r['auction_price_by_sex']['steer'],19800)
        self.assertEqual(r['graded_head'],102500)
    def test_published_2024_backfill_is_gap_free(self):
        data=json.loads(Path(__file__).with_name('market_supply_data.json').read_text(encoding='utf-8'))
        rows=data['records']
        self.assertEqual(rows[0]['month'],'2024-01')
        self.assertEqual(rows[-1]['month'],'2026-10')
        self.assertEqual(len(rows),34)
        self.assertEqual(len(set(r['month'] for r in rows)),34)
        for r in rows:
            self.assertEqual(sum(r['graded_by_sex'].values()),r['graded_head'])
            self.assertEqual(sum(r['inventory_by_farm'].values()),r['inventory_head'])
            self.assertIsInstance(r['auction_price_by_sex']['steer'],int)
            self.assertIsInstance(r['auction_price_by_sex']['female'],int)

    def test_no_unverified_future_month(self):
        with patch('market_supply_sync.last_complete',return_value='2026-10'):
            months=desired_months()
        self.assertNotIn('202611',months)

if __name__=='__main__':
    unittest.main()
