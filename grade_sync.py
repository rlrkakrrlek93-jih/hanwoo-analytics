#!/usr/bin/env python3
"""National Hanwoo grade incidence; validated against a captured official HTML response.
This is a public-statistics web interface, not an official external API.
"""
import argparse, json, re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
URL='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1050005&conn_path=I3'
POST_URL='https://mtrace.go.kr/statHtml/html.do'
GRADES=['1++','1+','1','2','3']

def parse_grade_response(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('result'),list) or not raw['result']:
        raise ValueError('응답 result 배열 없음: 서버 응답 구조 확인 필요')
    soup=BeautifulSoup(raw['result'][0],'html.parser')
    table=soup.select_one('table#mainTable')
    if table is None: raise ValueError('응답에 mainTable 없음')
    # The first header row contains date headers, one per 2 numeric columns.
    months=[]
    for th in table.select('thead tr:first-child th[name^="M"]'):
        m=re.fullmatch(r'M(20\d{4})',th.get('name',''))
        if m:months.append(m.group(1)[:4]+'-'+m.group(1)[4:])
    if not months:raise ValueError('월별 통계 헤더 없음')
    rows={};current=['','','','']
    for tr in table.select('tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)<4+2*len(months):continue
        for i in range(4):
            if 'merge' not in cells[i].get('class',[]):
                value=cells[i].get('title','').strip() or cells[i].get_text(' ',strip=True)
                if value:current[i]=value
        breed,sex,category,grade=current
        if breed!='한우' or sex not in ('암','거세'):continue
        if not ((category=='전체' and grade=='소계') or (category=='육질등급' and grade in GRADES)):
            continue
        for idx,month in enumerate(months):
            try:
                count_text=cells[4+2*idx].get('title','').replace(',','').strip()
                rate_text=cells[5+2*idx].get('title','').replace(',','').strip()
                if not count_text or not rate_text:continue
                count=int(count_text);rate=float(rate_text)
            except (ValueError,IndexError):continue
            key=(month,'거세우' if sex=='거세' else '암소')
            data=rows.setdefault(key,{'month':month,'sex':key[1],'grades':{}})
            if category=='전체':data['count']=count
            else:data['grades'][grade]={'count':count,'rate':rate}
    valid=[]
    for k,data in sorted(rows.items()):
        if data['month']<'2026-01':continue
        total=data.get('count',0)
        if total<=0 or any(g not in data['grades'] for g in GRADES):continue
        for grade,info in data['grades'].items():
            n=info['count'];rate=info['rate']
            if not (0<=n<=total and 0<=rate<=100) or abs(n/total*100-rate)>0.56:
                raise ValueError(f'{k} {grade}: 판정두수와 출현율이 불일치')
        # Some cattle may be out-of-grade, so grade counts can be less than total.
        if sum(v['count'] for v in data['grades'].values())>total:
            raise ValueError(f'{k}: 등급 두수 합계가 총 판정두수 초과')
        valid.append(data)
    cover={}
    for r in valid:cover.setdefault(r['month'],set()).add(r['sex'])
    valid=[r for r in valid if cover[r['month']]=={'거세우','암소'}]
    if not valid:raise ValueError('전국 한우 거세우·암소의 유효한 월별 행 없음')
    return valid

def collect():
    now=datetime.now(ZoneInfo('Asia/Seoul'))
    # Request no later than the last completed month, to avoid partial reporting.
    year,mo=now.year,now.month-1
    if mo==0: year-=1;mo=12
    end=year*100+mo
    months=[];y,m=2026,1
    while y*100+m<=end:
        months.append(f'{y:04d}{m:02d}')
        m+=1
        if m==13:y+=1;m=1
    if not months:raise ValueError('2026년 1월 이후 완료월이 없음')
    template=json.loads((ROOT/'grade_request_template.json').read_text(encoding='utf-8'))
    fields={k:str(v) for k,v in template.items() if isinstance(v,(str,int,float))}
    fieldlist=json.loads(fields['fieldList'])
    for entry in fieldlist:
        if entry.get('targetId')=='PRD':
            entry['prdValue']='M,'+','.join(reversed(months))+',@'
    fields['fieldList']=json.dumps(fieldlist,ensure_ascii=False,separators=(',',':'))
    fields.update({'orgId':'323','tblId':'DT_323903_E1050005','language':'ko',
                   'colAxis':'TIME,A,ITEM','rowAxis':'B,C,D','connPath':'I3',
                   'contextPath':'/statHtml','periodStr':'M','isFirst':'N','viewKind':'1','view':'table',
                   'findData':'on','maxCellOver':'Y','reqCellCnt':'8352'})
    # Multiple timeChkM values are intentionally repeated, as in the real form submission.
    pairs=list(fields.items())+ [('timeChkM',v) for v in reversed(months)]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        try:
            context=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul')
            page=context.new_page()
            page.goto(URL,wait_until='domcontentloaded',timeout=60000)
            resp=context.request.post(POST_URL,data=urlencode(pairs),headers={
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With':'XMLHttpRequest','Referer':URL},timeout=60000)
            print('육질등급 조회 HTTP',resp.status)
            if resp.status!=200:raise RuntimeError(f'통계 서버 HTTP {resp.status}')
            raw=resp.json()
            try:rows=parse_grade_response(raw)
            except Exception as exc:
                # Minimal diagnostics only. No cookies or authorization headers.
                err={'keys':list(raw) if isinstance(raw,dict) else type(raw).__name__,
                     'result_type':type(raw.get('result')).__name__ if isinstance(raw,dict) else None,
                     'result_preview':str(raw.get('result',''))[:600] if isinstance(raw,dict) else str(raw)[:600]}
                (ROOT/'grade_error_summary.json').write_text(json.dumps(err,ensure_ascii=False,indent=2),encoding='utf-8')
                raise RuntimeError('공식 응답 구조 오류; grade_error_summary.json 확인') from exc
            if not any(r['month']=='2026-01' for r in rows):
                raise RuntimeError('2026년 1월 결과 누락: 조회 조건 확인 필요')
            return rows
        finally:browser.close()

def save_rows(rows):
    path=ROOT/'grade_data.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        old_rows=old.get('records',[])
        merged={(r['month'],r['sex']):r for r in old_rows}
        merged.update({(r['month'],r['sex']):r for r in rows})
        rows=sorted(merged.values(),key=lambda x:(x['month'],x['sex']))
    checked=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')
    result={'source':URL,'table_id':'DT_323903_E1050005','last_success_kst':checked,'records':rows}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'육질등급 수집 성공: {len(rows)}행, {rows[0]["month"]} ~ {rows[-1]["month"]}')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--response',help='사용자가 캡처한 공개 통계 JSON 응답 파일')
    args=parser.parse_args()
    rows=parse_grade_response(json.loads(Path(args.response).read_text(encoding='utf-8'))) if args.response else collect()
    save_rows(rows)
