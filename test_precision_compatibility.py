import json
import tempfile
import unittest
from pathlib import Path
from precision_compatibility import compare

HEAD='<thead><tr><th name="A">품종</th><th name="B">성별</th><th name="C">체중</th><th name="M202608" colspan="8">8월</th></tr><tr><th name="00" colspan="8">전국</th></tr><tr>'+''.join('<th name="T%03d">항목</th>'%i for i in range(1,9))+'</tr></thead>'

def original(male=100,female=80):
    rows=''.join('<tr><td>한우</td><td>%s</td><td>전체</td><td>%s</td>%s</tr>'%(sex,n,''.join('<td>7</td>' for _ in range(7))) for sex,n in [('거세',male),('암',female)])
    return '<table id="mainTable">'+HEAD+'<tbody>'+rows+'</tbody></table>'

def candidate(male=100,female=80):
    head='<thead><tr><th name="A">품종</th><th name="B">성별</th><th name="C">성적</th><th name="M202608">8월</th></tr></thead>'
    rows=''.join('<tr><td>한우</td><td>%s</td><td>두수 (두)</td><td>%s</td></tr>'%(sex,n) for sex,n in [('거세',male),('암',female)])
    return '<table id="mainTable">'+head+'<tbody>'+rows+'</tbody></table>'

class TestPrecisionCompatibility(unittest.TestCase):
    def run_compare(self,a,b):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'original.json';q=Path(folder)/'candidate.json'
            p.write_text(json.dumps({'result':[a]}),encoding='utf-8')
            q.write_text(json.dumps({'result':[b]}),encoding='utf-8')
            return compare(p,q)

    def test_mismatch_is_blocked(self):
        r=self.run_compare(original(),candidate(99,80))
        self.assertEqual(r['overlap'],2)
        self.assertFalse(r['count_matches_all_overlapping'])
        self.assertFalse(r['can_replace_site_values'])

    def test_equal_counts_never_automatically_approve(self):
        r=self.run_compare(original(),candidate())
        self.assertTrue(r['count_matches_all_overlapping'])
        self.assertFalse(r['can_replace_site_values'])

    def test_missing_sex_blocks(self):
        r=self.run_compare(original(),candidate().replace('<td>암</td>','<td>수</td>'))
        self.assertFalse(r['candidate_covers_all_original_months'])
        self.assertFalse(r['can_replace_site_values'])

if __name__=='__main__':unittest.main()
