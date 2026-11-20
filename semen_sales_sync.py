#!/usr/bin/env python3
"""Read public Hanwoo Association PDFs; update only validated NongHyup semen sales.

Official publication units are thousand straws (rounded).
A failed download, unmatched table or incomplete month never changes published JSON.
"""
from __future__ import annotations
import json,re,tempfile,os,argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo
import requests
import fitz
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
DEST=ROOT/'semen_sales_data.json'
LIST='https://www.ihanwoo.org/board/sub4?Ncode=publication&code=3&tabsNum=3'
PAGES=[
 'https://www.ihanwoo.org/20928',
 'https://www.ihanwoo.org/20841',
 'https://www.ihanwoo.org/20803',
]
UA={'User-Agent':'Mozilla/5.0 (compatible; HanwooInsight public data check)'}
SOURCE={'2024':"https://www.ihanwoo.org/file_c/file_download?fname=ax_6049658841.pdf&furl=%2Fupload&orifname=2025%EB%85%84+2%EC%9B%94+%ED%95%9C%EC%9A%B0+%EB%8F%99%ED%96%A5+%EB%B6%84%EC%84%9D.pdf",
 '2025':"https://www.ihanwoo.org/file_c/file_download?furl=/upload&fname=ax_9838022113.pdf&orifname=2025%EB%85%84+6%EC%9B%94+%ED%95%9C%EC%9A%B0+%EB%8F%99%ED%96%A5+%EB%B6%84%EC%84%9D.pdf"}
BASELINE_2024=[128,207,140,162,193,195,188,168,180,165,133,161]
BASELINE_2025=[139,143,118,140,179]

def find_values(raw,year):
    """Find only semen table rows after known 2021 control values; drop report subtotal."""
    text=raw.replace('\u00a0',' ')
    match=re.search(r'2021\s+172\s+162\s+179\s+209',text)
    if not match:return None
    section=text[match.start():match.start()+4200]
    for line in section.splitlines():
        row=re.match(r'^\s*'+str(year)+r'\s+(.+?)\s*$',line)
        if not row:continue
        tokens=re.findall(r'\d{1,3}(?:,\d{3})*',row.group(1))
        numbers=[int(x.replace(',','')) for x in tokens]
        if len(numbers)>1 and numbers[-1]==sum(numbers[:-1]):
            numbers=numbers[:-1]
        if not 1<=len(numbers)<=12 or any(v<25 or v>400 for v in numbers):
            return None
        return numbers
    return None

def report_rows(url):
    response=requests.get(url,headers=UA,timeout=23)
    response.raise_for_status()
    if not response.content.startswith(b'%PDF') or len(response.content)>25_000_000:
        raise ValueError('Not a valid public PDF')
    doc=fitz.open(stream=response.content,filetype='pdf')
    results={}
    for page in doc:
        text=page.get_text(sort=True)
        if '정액' not in text or '천str' not in text.replace(' ','').lower():
            continue
        for year in range(2024,datetime.now(ZoneInfo('Asia/Seoul')).year+1):
            vals=find_values(text,year)
            if vals and (year not in results or len(vals)>len(results[year])):
                results[year]=vals
    return results

def discover():
    """Only search publication pages for additional reports, never parse news estimates."""
    urls=[*SOURCE.values()]
    for page_url in PAGES:
        try:
            html=requests.get(page_url,headers=UA,timeout=12)
            html.raise_for_status()
            for a in BeautifulSoup(html.text,'html.parser').select('a[href]'):
                title=a.get_text(' ',strip=True)
                link=urljoin(page_url,a['href'])
                if '한우 동향 분석.pdf' in title and '/file_c/file_download' in link:
                    urls.append(link)
        except Exception as err:
            print('Report discovery unavailable:',page_url,str(err)[:130])
    return list(dict.fromkeys(urls))

def merge(existing,reports):
    old={r['month']:r for r in existing.get('records',[])}
    today=datetime.now(ZoneInfo('Asia/Seoul'))
    last_month=(today.year*12+today.month-2)
    imported=0
    for url,result in reports:
        for year,vals in result.items():
            for i,value in enumerate(vals):
                if year*12+i>last_month:continue
                month=f'{year}-{i+1:02d}'
                candidate={'month':month,'sold_thousand_str':value,'source_url':url}
                prior=old.get(month)
                if prior and prior['sold_thousand_str']!=value:
                    print('WARNING differing published values: preserved existing',month,prior['sold_thousand_str'],value)
                    continue
                if prior is None:
                    old[month]=candidate;imported+=1
    records=[old[k] for k in sorted(old)]
    if not records or any(type(r.get('sold_thousand_str')) is not int or not 25<=r['sold_thousand_str']<=400 for r in records):
        raise ValueError('Semen sales validation failed')
    return records,imported

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--dry-run',action='store_true');args=cli.parse_args()
    previous=json.loads(DEST.read_text(encoding='utf8')) if DEST.exists() else {}
    reports=[]
    for url in discover():
        try:
            parsed=report_rows(url)
            if parsed:
                reports.append((url,parsed))
                print('Validated official source',len(parsed),'years:',{str(k):len(v) for k,v in parsed.items()})
        except Exception as err:print('Source unavailable:',str(err)[:160])
    if not reports:
        print('No verifiable source replies. Existing data untouched.')
        if args.dry_run:raise RuntimeError('Could not access historical public reports')
        return
    results,added=merge(previous,reports)
    bymonth={r['month']:r['sold_thousand_str'] for r in results}
    if any(bymonth.get(f'2024-{i+1:02d}')!=v for i,v in enumerate(BASELINE_2024)):
        raise ValueError('2024 reported benchmark differs')
    if any(bymonth.get(f'2025-{i+1:02d}')!=v for i,v in enumerate(BASELINE_2025)):
        raise ValueError('2025 official Jan-May benchmark differs')
    print('VALIDATED_SEMEN_RECORDS',len(results),'new',added,'latest',results[-1]['month'])
    if args.dry_run:
        print('SEED_COUNTS '+json.dumps({str(y):sum(r['month'].startswith(str(y)) for r in results) for y in range(2024,2027)}))
        return
    if added==0:return
    out={**previous,'records':results,'coverage':f'{results[0]["month"]} ~ {results[-1]["month"]} (검증된 월만)',
         'last_verified_kst':datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')}
    fd,temp=tempfile.mkstemp(dir=ROOT,prefix='.semen_',suffix='.json')
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
        os.replace(temp,DEST)
    finally:Path(temp).unlink(missing_ok=True)

if __name__=='__main__':main()
