#!/usr/bin/env python3
"""Fetch official monthly nationwide 육우 거세 beef quality-grade counts.
Independent dataset: never infer grade incidence from mean marbling score.
The public statistics HTML response is parsed defensively and older verified
records survive temporary access or publication failures.
"""
import json
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
SOURCE='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1050005&conn_path=I3'
POST='https://mtrace.go.kr/statHtml/html.do'
OUTPUT=ROOT/'beef_grade_data.json'
GRADES=('1++','1+','1','2','3')
TOP=('1++','1+','1')

def parse_response(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('result'),list) or not raw['result']:
        raise ValueError('Official result HTML missing')
    soup=BeautifulSoup(raw['result'][0],'html.parser')
    table=soup.select_one('table#mainTable')
    if not table: raise ValueError('mainTable missing')
    months=[]
    for th in table.select('thead tr:first-child th[name^="M"]'):
        match=re.fullmatch(r'M(20\d{4})', th.get('name',''))
        if match:months.append(match.group(1)[:4]+'-'+match.group(1)[4:])
    if not months:raise ValueError('Official month columns missing')
    rows={}
    current=['','','','']
    for tr in table.select('tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)<4+2*len(months):continue
        for i in range(4):
            if 'merge' not in cells[i].get('class',[]):
                label=cells[i].get('title','').strip() or cells[i].get_text(' ',strip=True)
                if label: current[i]=label
        breed,sex,kind,grade=current
        if breed!='육우' or sex!='거세':continue
        if not ((kind=='전체' and grade=='소계') or
                (kind=='육질등급' and grade in GRADES)):continue
        for idx,month in enumerate(months):
            try:
                raw_count=cells[4+2*idx].get('title','').replace(',','').strip()
                raw_rate=cells[5+2*idx].get('title','').replace(',','').strip()
                if not raw_count or not raw_rate:continue
                count=int(raw_count);rate=float(raw_rate)
            except (ValueError,IndexError):continue
            key=month
            record=rows.setdefault(key,{'month':month,'breed':'육우','sex':'거세우','grades':{}})
            if kind=='전체':record['count']=count
            else:record['grades'][grade]={'count':count,'rate':rate}
    valid=[]
    for month,rec in sorted(rows.items()):
        if month<'2026-01':continue
        total=rec.get('count')
        if not isinstance(total,int) or total<=0 or any(x not in rec['grades'] for x in GRADES):
            continue
        sum_grades=sum(rec['grades'][x]['count'] for x in GRADES)
        if sum_grades>total:raise ValueError(f'{month} grade counts exceed total')
        for x in GRADES:
            entry=rec['grades'][x]
            n,rate=entry['count'],entry['rate']
            if not (0<=n<=total and 0<=rate<=100) or abs(n/total*100-rate)>0.56:
                raise ValueError(f'{month} {x} count/rate mismatch')
        rec['grade1plus_count']=sum(rec['grades'][x]['count'] for x in TOP)
        rec['grade1plus_rate']=round(100*rec['grade1plus_count']/total,2)
        valid.append(rec)
    if not valid:raise ValueError('No complete nationwide beef-steer grade rows')
    return valid

def collect():
    now=datetime.now(ZoneInfo('Asia/Seoul'))
    year,mo=now.year,now.month-1
    if mo==0:year,mo=year-1,12
    months=[]
    y,m=2026,1
    while y*100+m<=year*100+mo:
        months.append(f'{y:04d}{m:02d}')
        m+=1
        if m==13:y,m=y+1,1
    if not months:raise ValueError('No completed calendar months')
    template=json.loads((ROOT/'grade_request_template.json').read_text(encoding='utf8'))
    fields={k:str(v) for k,v in template.items() if isinstance(v,(str,int,float))}
    fieldlist=json.loads(fields['fieldList'])
    for entry in fieldlist:
        if entry.get('targetId')=='PRD':entry['prdValue']='M,'+','.join(reversed(months))+',@'
    fields['fieldList']=json.dumps(fieldlist,ensure_ascii=False,separators=(',',':'))
    fields.update({'orgId':'323','tblId':'DT_323903_E1050005','language':'ko',
                   'colAxis':'TIME,A,ITEM','rowAxis':'B,C,D','connPath':'I3',
                   'contextPath':'/statHtml','periodStr':'M','isFirst':'N',
                   'viewKind':'1','view':'table','findData':'on',
                   'maxCellOver':'Y','reqCellCnt':'8352'})
    pairs=list(fields.items())+[('timeChkM',x) for x in reversed(months)]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        try:
            context=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul')
            context.new_page().goto(SOURCE,wait_until='domcontentloaded',timeout=60000)
            resp=context.request.post(POST,data=urlencode(pairs),headers={
               'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
               'X-Requested-With':'XMLHttpRequest','Referer':SOURCE},timeout=60000)
            if resp.status!=200:raise RuntimeError(f'Official grade query HTTP {resp.status}')
            return parse_response(resp.json())
        finally: browser.close()

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--response',help='Saved official JSON response for offline parser tests')
    args=parser.parse_args()
    new=parse_response(json.loads(Path(args.response).read_text('utf8'))) if args.response else collect()
    old={}
    if OUTPUT.exists():
        old={(r['month'],r['breed'],r['sex']):r for r in json.loads(OUTPUT.read_text('utf8')).get('records',[])}
    for row in new:old[(row['month'],row['breed'],row['sex'])]=row
    verified=sorted(old.values(),key=lambda r:r['month'])
    checked=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')
    payload={'source':SOURCE,'table_id':'DT_323903_E1050005','definition':'전국 육우 거세우 육질 1등급 이상(1++, 1+, 1)의 등급별 판정두수 합계 / 전체 육우 거세우 판정두수','last_success_kst':checked,'records':verified}
    OUTPUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for row in new:print(row['month'],row['grade1plus_count'],'/',row['count'],'=',row['grade1plus_rate'],'%')
    print('Published official beef grade months:',len(verified))

if __name__=='__main__':main()
