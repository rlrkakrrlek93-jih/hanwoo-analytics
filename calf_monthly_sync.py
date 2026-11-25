#!/usr/bin/env python3
"""Refresh published 2024–2026 sex-specific Hanwoo calf price monthly series.

The AgroPick monthly tables are a separate aggregation of original eKAPEpia
national daily 6–7-month livestock-market survey records. Keep them separate
from the official 'previous-month average' reference and latest day prices.
Never guess monthly prices, extrapolate missing months, or overwrite on error.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'calf_price_data.json'
SOURCES={
 'male_6_7':'https://agropick.martius.kr/indicator/calf-male',
 'female_6_7':'https://agropick.martius.kr/indicator/calf-female'
}
KST=dt.timezone(dt.timedelta(hours=9))

def parse_monthly(html):
    soup=BeautifulSoup(html,'html.parser')
    found={}
    for tr in soup.select('tr'):
        cells=tr.find_all(['td','th'],recursive=False)
        if len(cells)<2:continue
        label=' '.join(cells[0].stripped_strings)
        # Exclude incomplete current-month aggregates.
        if '진행 중' in label:continue
        m=re.match(r'^(202[4-6])-(0[1-9]|1[0-2])$',label.strip())
        if not m:continue
        month=m.group(1)+'-'+m.group(2)
        raw=' '.join(cells[1].stripped_strings).replace(',','').strip()
        n=re.match(r'^([0-9]{3,5})(?:\s|$)',raw)
        if not n:continue
        v=int(n.group(1))
        if not 500<=v<=15000:raise ValueError(f'{month} suspicious calf price {v}')
        if month in found and found[month]!=v:raise ValueError(f'{month} inconsistent table values')
        found[month]=v
    return found

def fetch():
    rows={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        try:
            page=browser.new_page(locale='ko-KR',timezone_id='Asia/Seoul')
            for sex,url in SOURCES.items():
                response=page.goto(url,wait_until='domcontentloaded',timeout=60000)
                if response and response.status>=400:raise ValueError(f'{sex} HTTP {response.status}')
                page.wait_for_timeout(1200)
                rows[sex]=parse_monthly(page.content())
        finally:
            browser.close()
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--male-html')
    parser.add_argument('--female-html')
    opts=parser.parse_args()
    if bool(opts.male_html)!=bool(opts.female_html):
        parser.error('both --male-html and --female-html are required')
    rows={
        'male_6_7':parse_monthly(Path(opts.male_html).read_text('utf8')),
        'female_6_7':parse_monthly(Path(opts.female_html).read_text('utf8'))
    } if opts.male_html else fetch()
    today=dt.datetime.now(KST).date()
    month_end=today.replace(day=1)-dt.timedelta(days=1)
    latest=f'{month_end.year:04d}-{month_end.month:02d}'
    intersection=sorted(set(rows['male_6_7'])&set(rows['female_6_7']))
    verified=[m for m in intersection if '2024-01'<=m<=min('2026-12',latest)]
    if len(verified)<34 or '2024-01' not in verified or '2026-10' not in verified:
        raise ValueError(f'Historical coverage insufficient: {len(verified)} verified months; no data overwritten')
    archive=json.loads(DATA.read_text(encoding='utf8'))
    saved={r['month']:r for r in archive.get('monthly_series',[]) if r.get('region')=='전국'}
    for month in verified:
        saved[month]={
          'month':month,'region':'전국',
          'male_6_7':rows['male_6_7'][month],
          'female_6_7':rows['female_6_7'][month]
        }
    archive['monthly_series']=[saved[k] for k in sorted(saved)]
    archive['monthly_series_last_confirmed']=max(verified)
    archive['monthly_series_last_synced_kst']=dt.datetime.now(KST).strftime('%Y-%m-%d %H:%M KST')
    archive['monthly_series_sources']={**SOURCES,
        'underlying':'https://www.ekapepia.com/v3/price/livestock/cow/producer.do'}
    archive['monthly_series_note']=(
        '아그로픽이 eKAPEpia 공개 가축시장 일별 6~7개월령 한우 송아지 가격을 월평균으로 '
        '재집계한 자료(천원/마리). 축산유통정보 다봄 공식 전월평균과 집계 방식 차이가 '
        '있을 수 있어 별도 시계열로 유지. 미발표·진행 중인 월은 포함하지 않음.'
    )
    fd,temp=tempfile.mkstemp(prefix='.calf_months_',suffix='.json',dir=ROOT)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as file:
            json.dump(archive,file,ensure_ascii=False,indent=2);file.write('\n')
        os.replace(temp,DATA)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    print('Verified historical monthly prices:',len(verified),'through',max(verified))
    print('Archive has',len(archive['monthly_series']),'monthly records')

if __name__=='__main__':main()
