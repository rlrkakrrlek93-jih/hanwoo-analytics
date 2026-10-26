#!/usr/bin/env python3
"""Public KAPE statistics table scraper (not an official API)."""
import argparse,json,re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
TABLE='DT_323901_A300000005'
URL=f'https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId={TABLE}&conn_path=I2'
ENDPOINT='https://mtrace.go.kr/statHtml/html.do'

def months_until_last_complete():
    now=datetime.now(ZoneInfo('Asia/Seoul')); end=now.year*12+now.month-2
    return [f'{k//12:04d}{k%12+1:02d}' for k in range(2026*12, end+1)]

def payload(months):
    field=[{'targetId':'PRD','targetValue':'','prdValue':'M,'+','.join(reversed(months))+',@'},
           {'targetId':'ITM_ID','targetValue':'T001','prdValue':''}]
    for id,values in [('OV_L1_ID',['01','03']),('OV_L2_ID',['00','01','02','03'])]:
        field += [{'targetId':id,'targetValue':v,'prdValue':''} for v in values]
    pairs=[('orgId','323'),('tblId',TABLE),('language','ko'),('file',''),('analText',''),('scrId',''),
      ('fieldList',json.dumps(field,ensure_ascii=False,separators=(',',':'))),('colAxis','A,B'),('rowAxis','TIME'),
      ('isFirst','N'),('contextPath','/statHtml'),('connPath','I2'),('statId','2006901'),('viewKind','1'),
      ('mode','tab'),('dataOpt','ko'),('view','table'),('periodStr','M'),('findData','on'),
      ('classAllArr','[{"objVarId":"A","ovlSn":"1"},{"objVarId":"B","ovlSn":"2"}]'),
      ('classSet','[{"objVarId":"A","ovlSn":"1","visible":"true"},{"objVarId":"B","ovlSn":"2","visible":"true"}]'),
      ('itemMultiply','8'),('reqCellCnt',str(len(months)*8)),('enableLevelExpr','Y'),('prdSort','desc'),
      ('itemChkLi','T001'),('classChkLi1_1','01='),('classChkLi1_1','03='),
      ('classChkLi2_1','00='),('classChkLi2_1','01='),('classChkLi2_1','02='),('classChkLi2_1','03=')]
    pairs += [('timeChkM',m) for m in reversed(months)]
    return pairs

def parse(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('result'),list) or not raw['result']:
        raise ValueError('공식 응답 result HTML 없음')
    soup=BeautifulSoup(raw['result'][0],'html.parser'); table=soup.select_one('table#mainTable')
    if not table:raise ValueError('mainTable 없음')
    # User-verified table layout: period | Hanwoo (all/female/male/neutered) | Beef breed (...) .
    # Verify actual headings rather than trust numeric offsets silently.
    heads=table.select('thead tr'); header=' '.join(h.get_text(' ',strip=True) for h in heads[:3])
    if not all(t in header for t in ('한우','암','거세')):
        raise ValueError('한우·암·거세 열 제목 확인 실패: 응답 표 구조가 달라짐')
    # Reconstruct leaf column labels using header colspan / rowspan.
    # In this table first four columns after date belong to Hanwoo: 전체, 암, 수, 거세.
    rows=[]
    for tr in table.select('tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)<5:continue
        date=(cells[0].get('title','') or cells[0].get_text(' ',strip=True)).strip()
        mo=re.match(r'^(20\d{2})[.\-\s]+(\d{1,2})$',date)
        if not mo:continue
        month=f'{mo.group(1)}-{int(mo.group(2)):02d}'
        if month<'2026-01':continue
        for sex,index in [('암소',2),('거세우',4)]:
            txt=(cells[index].get('title','') or cells[index].get_text(' ',strip=True)).replace(',','').strip()
            if txt in ('','-','…'):continue
            try:age=float(txt)
            except ValueError:continue
            if not (10<=age<=150):raise ValueError(f'{month} {sex}: 비정상 도축개월령 {age}')
            rows.append({'month':month,'sex':sex,'age_months':age})
    cover={}
    for r in rows:cover.setdefault(r['month'],set()).add(r['sex'])
    rows=[r for r in rows if cover[r['month']]=={'거세우','암소'}]
    rows.sort(key=lambda r:(r['month'],r['sex']))
    if not rows or not any(r['month']=='2026-01' for r in rows):
        raise ValueError('2026년 1월 이후 전국 한우 거세우·암소 자료를 모두 찾지 못함')
    return rows

def collect():
    months=months_until_last_complete()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        try:
            ctx=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul')
            page=ctx.new_page();page.goto(URL,wait_until='domcontentloaded',timeout=60000)
            r=ctx.request.post(ENDPOINT,data=urlencode(payload(months)),headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest','Referer':URL},timeout=60000)
            print('도축개월령 조회 HTTP',r.status)
            if r.status!=200:raise RuntimeError('통계표 요청 실패')
            try: raw=r.json()
            except Exception as e:raise RuntimeError('통계표 JSON 응답 아님') from e
            try:return parse(raw)
            except Exception:
                summary={'keys':list(raw) if isinstance(raw,dict) else str(type(raw)),
                         'result_length':len(str(raw.get('result',''))) if isinstance(raw,dict) else 0,
                         'result_preview':str(raw.get('result',''))[:250] if isinstance(raw,dict) else str(raw)[:250]}
                (ROOT/'age_error_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
                raise
        finally:browser.close()

def save(rows):
    dest=ROOT/'age_data.json'
    old=json.loads(dest.read_text(encoding='utf8')) if dest.exists() else {}
    allrows={(r['month'],r['sex']):r for r in old.get('records',[])}
    allrows.update({(r['month'],r['sex']):r for r in rows})
    merged=sorted(allrows.values(),key=lambda r:(r['month'],r['sex']))
    data={'source':URL,'table_id':TABLE,'indicator':'평균도축개월령','last_success_kst':datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST'),'records':merged}
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print(f'도축개월령 수집 성공: {len(merged)}행, {merged[0]["month"]} ~ {merged[-1]["month"]}')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--response');a=ap.parse_args()
    save(parse(json.loads(Path(a.response).read_text(encoding='utf8'))) if a.response else collect())
