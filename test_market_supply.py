import unittest
from market_supply_sync import parse_inventory,parse_grading,build

def resp(html):
    return {'result':[html]}

def inventory():
    header='<thead><tr><th name="B">시도</th><th name="M202610" colspan="4">2026.10</th></tr><tr>'+''.join('<th name="%s">%s</th>'%(a,a) for a in ('00','01','02','03'))+'</tr></thead>'
    row='<tr><td title="전국">전국</td>'+''.join('<td title="%s">%s</td>'%(n,n) for n in ('3,139,307','426,068','316,985','2,396,254'))+'</tr>'
    return resp('<table id="mainTable">'+header+'<tbody>'+row+'</tbody></table>')

def grading():
    header='<thead><tr><th name="A">품종</th><th name="B">성별</th><th name="C">구간</th><th name="M202610" colspan="8">2026.10</th></tr><tr><th name="00" colspan="8">전국</th></tr><tr>'+''.join('<th name="T%03d">항목</th>'%i for i in range(1,9))+'</tr></thead>'
    rows=''
    for sex,count in [('암',27570),('수',527),('거세',34328)]:
        rows+='<tr><td>한우</td><td>%s</td><td>전체</td><td title="%s">%s</td>'%(sex,count,count)
        rows+=''.join('<td title="10">10</td>' for _ in range(7))+'</tr>'
    return resp('<table id="mainTable">'+header+'<tbody>'+rows+'</tbody></table>')

class TestSupplySync(unittest.TestCase):
    def test_nationwide_inventory_and_farm_sum(self):
        rows,parts=parse_inventory(inventory())
        self.assertEqual(rows['2026-10'],3139307)
        self.assertEqual(sum(parts['2026-10'].values()),3139307)
    def test_grading_includes_hanwoo_male(self):
        rows,parts=parse_grading(grading())
        self.assertEqual(rows['2026-10'],62425)
        self.assertEqual(parts['2026-10']['male'],527)
    def test_incomplete_breakdown_does_not_publish(self):
        doc=grading()
        doc['result'][0]=doc['result'][0].replace('<td>수</td>','<td>등외</td>')
        with self.assertRaisesRegex(ValueError,'incomplete'):
            parse_grading(doc)
    def test_month_population_labels(self):
        inv,ip=parse_inventory(inventory());gr,gp=parse_grading(grading())
        doc=build(inv,ip,gr,gp)
        self.assertEqual(doc['records'][0]['graded_head'],62425)
        self.assertIn('암·수·거세',doc['grading_definition'])
    def test_inventory_inconsistent_subtotal_is_blocked(self):
        doc=inventory()
        doc['result'][0]=doc['result'][0].replace('426,068','426,069')
        with self.assertRaisesRegex(ValueError,'subtotals'):
            parse_inventory(doc)

if __name__=='__main__':unittest.main()
