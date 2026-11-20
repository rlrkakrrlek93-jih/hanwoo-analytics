#!/usr/bin/env python3
"""Read-only source-compatibility gate for HANWOO INSIGHT.
Reads official responses from precision_probe.py, never edits production stats.
A matching headcount is necessary but NOT sufficient for precision substitution.
"""
import argparse
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

NUMBER=re.compile(r'^\d[\d,]*(?:\.\d+)?$')
SEX={'거세':'거세우','암':'암소'}

def table(path):
    raw=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    result=raw.get('result',[])
    if not result or not isinstance(result[0],str):
        raise ValueError('No official table response')
    t=BeautifulSoup(result[0],'html.parser').select_one('#mainTable')
    if t is None:
        raise ValueError('mainTable missing')
    return t

def columns(tr):
    return tr.find_all(['th','td'],recursive=False)

def expand(cells):
    out=[]
    for c in cells:
        out.extend([c.get('name','')]*int(c.get('colspan',1)))
    return out

def months(tr):
    return [v[1:] for v in expand(c for c in columns(tr) if c.get('name','').startswith('M20'))]

def cell_number(c):
    v=c.get_text(' ',strip=True).replace(',','').replace(' ','')
    return float(v) if NUMBER.fullmatch(v) else None

def original_counts(path):
    t=table(path);h=t.select('thead tr')
    if len(h)<3:raise ValueError('3-tier source header required')
    mo=months(h[0]);sites=expand(columns(h[1]));metric=expand(columns(h[2]))
    if len(mo)!=len(sites) or len(mo)!=len(metric):
        raise ValueError('Header column mismatch')
    indexes=[(i,m) for i,(m,s,field) in enumerate(zip(mo,sites,metric))
             if s=='00' and field=='T001']
    if not indexes:raise ValueError('Nationwide count fields missing')
    result={};breed=sex=''
    for tr in t.select('tbody tr'):
        c=columns(tr)
        if len(c)<4:continue
        labels=[x.get_text(' ',strip=True) for x in c[:3]]
        breed=labels[0] or breed;sex=labels[1] or sex
        if breed!='한우' or sex not in SEX or labels[2]!='전체':continue
        for idx,raw_month in indexes:
            val=cell_number(c[3+idx]) if 3+idx<len(c) else None
            if val is None or not val.is_integer():raise ValueError('Invalid official count')
            result[(raw_month[:4]+'-'+raw_month[4:],SEX[sex])]=int(val)
    return result

def candidate_counts(path):
    t=table(path);h=t.select('thead tr')
    if not h:raise ValueError('Candidate header missing')
    indexes=[(i,m) for i,m in enumerate(months(h[0]))]
    result={};breed=sex=''
    for tr in t.select('tbody tr'):
        c=columns(tr)
        if len(c)<4:continue
        labels=[x.get_text(' ',strip=True) for x in c[:3]]
        breed=labels[0] or breed;sex=labels[1] or sex
        if breed!='한우' or sex not in SEX or not labels[2].startswith('두수'):
            continue
        for idx,m in indexes:
            val=cell_number(c[3+idx]) if 3+idx<len(c) else None
            if val is not None and val.is_integer():
                result[(m[:4]+'-'+m[4:],SEX[sex])]=int(val)
    return result

def compare(original,candidate):
    a=original_counts(original);b=candidate_counts(candidate)
    overlap=sorted(set(a)&set(b))
    differences=[dict(month=m,sex=s,original_count=a[(m,s)],candidate_count=b[(m,s)])
                 for m,s in overlap if a[(m,s)]!=b[(m,s)]]
    missing=[dict(month=m,sex=s) for m,s in sorted(set(a)-set(b))]
    return dict(status='BLOCK_REPLACEMENT_UNTIL_SAME_POPULATION_AND_PRECISION_PROVEN',
                can_replace_site_values=False,original_record_count=len(a),
                candidate_record_count=len(b),overlap=len(overlap),
                count_matches_all_overlapping=bool(overlap) and not differences,
                candidate_covers_all_original_months=not missing,
                count_mismatches=differences,missing_in_candidate=missing,
                explanation='Matching count and coverage alone do not establish population, methodology, or precision equivalence.')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',default='precision_probe_result')
    args=p.parse_args();folder=Path(args.input_dir)
    result=compare(folder/'current_E1080008_raw_response.json',
                   folder/'candidate_APGS_011_raw_response.json')
    (folder/'precision_compatibility_report.json').write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in
      ('status','overlap','count_matches_all_overlapping','candidate_covers_all_original_months')},
      ensure_ascii=False))

if __name__=='__main__':main()
