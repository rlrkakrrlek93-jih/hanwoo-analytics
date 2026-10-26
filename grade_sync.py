#!/usr/bin/env python3
"""Second mtrace table: national Hanwoo grade counts & incidence rates.
Reads an authenticated browser's own public-statistics POST parameters, requests
2026-01 onward using that browser context and rejects ambiguous results.
Existing published data are left intact if the request or validation fails.
"""
import argparse, json, re, os, tempfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import parse_qsl, urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
URL='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1050005&conn_path=I3'
GRADES=['1++','1+','1','2','3']


def flatten_rows(trs):
    """Expand rowspans so merged labels are present on every row."""
    spans={}
    for tr in trs:
        out=[]; col=0
        for cell in tr.find_all(['td','th'],recursive=False):
            while col in spans:
                v,left=spans[col]; out.append(v)
                if left<=1: del spans[col]
                else: spans[col]=(v,left-1)
                col+=1
            cs=int(cell.get('colspan',1)); rs=int(cell.get('rowspan',1))
            for k in range(cs):
                out.append(cell)
                if rs>1: spans[col+k]=(cell,rs-1)
            col+=cs
        while col in spans:
            v,left=spans[col];out.append(v)
            if left<=1: del spans[col]
            else: spans[col]=(v,left-1)
            col+=1
        yield out


def parse_grade_response(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('result'),list) or not raw['result']:
        raise ValueError('공식 응답 result HTML 없음')
    soup=BeautifulSoup(raw['result'][0],'html.parser')
    table=soup.select_one('table#mainTable')
    if table is None: raise ValueError('mainTable 없음')
    head=table.select('thead tr')
    if len(head)<3: raise ValueError('월/전국/항목 헤더 부족')
    # For each metric column, derive the month/location/metric from three header rows.
    h=list(flatten_rows(head[:3]))
    def names(row):return [c.get('title') or c.get_text(' ',strip=True) for c in row]
    a,b,c=map(names,h)
    # Header rowspans on left contribute 4 descriptive cells; aligned end is safer.
    n=min(len(a),len(b),len(c)); a,b,c=a[-n:],b[-n:],c[-n:]
    slots=[]
    for idx,(month,location,item) in enumerate(zip(a,b,c)):
        m=re.search(r'(20\d{2})\s*[.\-/]?\s*(0?[1-9]|1[0-2])',month)
        if m and '전국' in location:
            label='count' if '두수' in item else ('rate' if '출현율' in item else None)
            if label: slots.append((idx,f'{m.group(1)}-{int(m.group(2)):02d}',label))
    if not slots: raise ValueError('전국 월별 두수/출현율 열을 찾을 수 없음')
    # Group grade rows by breed/sex; rowspans are reconstructed.
    result={}; current_breed='';current_sex='';current_section=''
    for row in flatten_rows(table.select('tbody tr')):
        if len(row)<6: continue
        cells=[x.get_text(' ',strip=True) for x in row]
        # If row spans aren't supplied in DOM, carry hierarchy forward.
        labels=cells[:4]
        if labels[0] not in ('','12'):current_breed=labels[0]
        if labels[1] not in ('','12'):current_sex=labels[1]
        if labels[2] not in ('','12'):current_section=labels[2]
        breed=current_breed if labels[0] in ('','12') else labels[0]
        sex=current_sex if labels[1] in ('','12') else labels[1]
        section=current_section if labels[2] in ('','12') else labels[2]
        grade=labels[3]
        if breed!='한우' or sex not in ('거세','암') or not (section=='육질등급' or grade=='소계'):continue
        if grade not in GRADES+['소계']:continue
        vals=cells[4:]
        # Headers can have four leftmost rowspan descriptors.
        offset=len(a)-len(vals)
        for ix,month,typ in slots:
            k=ix-offset
            if not 0<=k<len(vals): raise ValueError('헤더/본문 열 좌표 불일치')
            text=vals[k].replace(',','').replace('%','').strip()
            if text in ('-','','…'):continue
            try:value=float(text)
            except ValueError:raise ValueError(f'비숫자 출현율 {sex} {grade} {month}: {text}')
            key=(month,'거세우' if sex=='거세' else '암소')
            result.setdefault(key,{}).setdefault(grade,{})[typ]=value
    rows=[]
    for (month,sex),items in sorted(result.items()):
        if month<'2026-01':continue
        if not set(GRADES).issubset(items): continue
        total=items.get('소계',{}).get('count')
        if total is None or total<=0:raise ValueError(f'{month} {sex} 판정두수 소계 없음')
        r={'month':month,'sex':sex,'count':int(total),'grades':{}}
        for grade in GRADES:
            val=items[grade]
            if 'count' not in val or 'rate' not in val:raise ValueError(f'{month} {sex} {grade} 누락')
            count=int(val['count']);rate=float(val['rate'])
            if not (0<=count<=total and 0<=rate<=100) or abs(100*count/total-rate)>0.25:
                raise ValueError(f'{month} {sex} {grade} 두수/출현율 불일치')
            r['grades'][grade]={'count':count,'rate':rate}
        if sum(x['count'] for x in r['grades'].values())>total:raise ValueError('등급 두수 합계 초과')
        rows.append(r)
    bymonth={}
    for r in rows:bymonth.setdefault(r['month'],set()).add(r['sex'])
    rows=[r for r in rows if bymonth[r['month']]=={'거세우','암소'}]
    if not rows:raise ValueError('전국 한우 거세우/암소 완전한 월별 육질등급 데이터를 찾지 못함')
    return rows


def collect():
    captured=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        context=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul')
        page=context.new_page()
        def handle(resp):
            if '/statHtml/html.do' in resp.url and resp.request.method=='POST' and resp.status==200:
                try:
                    raw=resp.json()
                    if isinstance(raw.get('result'),list) and 'mainTable' in raw['result'][0]:
                        captured.append((resp.request.post_data,raw))
                except Exception:pass
        page.on('response',handle)
        try:
            page.goto(URL,wait_until='domcontentloaded',timeout=60000)
            page.wait_for_timeout(9000)
            if not captured:raise RuntimeError('통계표 초기 조회 응답 없음')
            # Site default is recent three months. Request all months from Jan 2026
            # using the same browser session and POST fieldList parameters.
            from_date='202601'; upto=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m')
            months=[];yy,mm=2026,1
            while f'{yy:04d}{mm:02d}'<=upto:
                months.append(f'{yy:04d}{mm:02d}')
                mm+=1
                if mm==13:yy+=1;mm=1
            errors=[]
            for post,original in reversed(captured):
                try:
                    fields=dict(parse_qsl(post or '',keep_blank_values=True))
                    choices=json.loads(fields['fieldList'])
                    prd=[item for item in choices if item.get('targetId')=='PRD']
                    if not prd:raise ValueError('기간 PRD 설정 없음')
                    for item in prd:item['prdValue']='M,'+','.join(reversed(months))+'@J'
                    fields['fieldList']=json.dumps(choices,ensure_ascii=False,separators=(',',':'))
                    reply=context.request.post('https://mtrace.go.kr/statHtml/html.do',data=urlencode(fields),headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest'},timeout=60000)
                    if reply.status!=200:raise ValueError('기간 확장 조회 HTTP '+str(reply.status))
                    obj=reply.json()
                    rows=parse_grade_response(obj)
                    if any(r['month']=='2026-01' for r in rows):return rows
                    # Refuse to pretend missing January was collected.
                    raise ValueError('2026년 1월 자료가 반환되지 않음: 기간 설정 검증 필요')
                except Exception as ex:errors.append(str(ex))
            raise RuntimeError('2026년 1월부터 자동 수집 실패: '+' | '.join(errors[:2]))
        finally:browser.close()


def save_rows(rows):
    path=ROOT/'grade_data.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        hist={(r['month'],r['sex']):r for r in old.get('records',[])}
        hist.update({(r['month'],r['sex']):r for r in rows})
        rows=sorted(hist.values(),key=lambda r:(r['month'],r['sex']))
    checked=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')
    payload={'source':URL,'table_id':'DT_323903_E1050005','last_success_kst':checked,'records':rows}
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'육질등급 수집 성공: {len(rows)}행, {rows[0]["month"]} ~ {rows[-1]["month"]}, {checked}')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--response',help='캡처한 공개 통계 HTML 응답 JSON')
    opt=a.parse_args()
    rows=parse_grade_response(json.loads(Path(opt.response).read_text(encoding='utf-8'))) if opt.response else collect()
    save_rows(rows)
