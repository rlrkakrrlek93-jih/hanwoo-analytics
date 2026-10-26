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
from urllib.parse import urlencode
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


def make_months():
    now=datetime.now(ZoneInfo('Asia/Seoul'))
    last_year,last_month=now.year,now.month
    # Only completed months, unless a source has explicitly published an ongoing month.
    last_month-=1
    if last_month==0:last_month=12;last_year-=1
    months=[];year,month=2026,1
    while (year,month)<=(last_year,last_month):
        months.append(f'{year:04d}{month:02d}')
        month+=1
        if month>12: year+=1;month=1
    return months


def build_official_form(months):
    # Based on the user's actual 2026-10-26 DevTools POST payload, not invented selector names.
    # PRD ends in a literal comma + '@' (the earlier @J variant was incorrect).
    choices=[{'targetId':'PRD','targetValue':'','prdValue':'M,'+','.join(reversed(months))+',@'}]
    for metric in ['T001','T002']:
        choices.append({'targetId':'ITM_ID','targetValue':metric,'prdValue':''})
    dims={'OV_L1_ID':['00'],'OV_L2_ID':['00','01','02','03'],
          'OV_L3_ID':['00','01','02','03'],
          'OV_L4_ID':['00','01','02','03']+[f'01{i:02d}' for i in range(1,17)]+[f'02{i:02d}' for i in range(1,7)]+[f'03{i:02d}' for i in range(1,4)]}
    for key,vals in dims.items():
        for v in vals: choices.append({'targetId':key,'targetValue':v,'prdValue':''})
    # Form fields from the actual captured request; repeated multi-select fields use tuples.
    fields=[('orgId','323'),('tblId','DT_323903_E1050005'),('language','ko'),
            ('file',''),('analText',''),('scrId',''),
            ('fieldList',json.dumps(choices,ensure_ascii=False,separators=(',',':'))),
            ('colAxis','TIME,A,ITEM'),('rowAxis','B,C,D'),('isFirst','N'),
            ('contextPath','/statHtml'),('connPath','I3'),('statId','2006903'),
            ('pub',''),('pubLog','0'),('viewKind','1'),('doAnal','N'),('dataOpt','ko'),
            ('view','table'),('classAllArr',json.dumps([{'objVarId':x,'ovlSn':str(i)} for i,x in enumerate('ABCD',1)])),
            ('classSet',json.dumps([{'objVarId':x,'ovlSn':str(i),'visible':'true'} for i,x in enumerate('ABCD',1)])),
            ('selectAllFlag','N'),('periodStr','M'),('tblNm','소도체 시도별 등급판정결과(작업장 기준)'),
            ('itemMultiply','928'),('dbUser','NSI_IN_323.'),('usePivot','N'),('tableType','default'),
            ('dataOpt2','ko'),('enableLevelExpr','Y'),('prdSort','desc'),('findData','on'),
            ('reqCellCnt',str(len(months)*928)),('maxCellOver','Y'),('inheritYn','N'),('first_open','Y'),
            ('downGridFileType','xlsx'),('downGridCellMerge','Y'),('downGridMeta','Y'),
            ('headCheck','M'),('itemChkLi','T001'),('itemChkLi','T002'),('classChkLi1_1','00='),
            ('classLvlAllChk2_1','on'),('classLvlAllChk3_1','on'),('classLvlAllChk4_2','on')]
    for m in reversed(months):fields.append(('timeChkM',m))
    for val in dims['OV_L2_ID']:fields.append(('classChkLi2_1',val+'='))
    for val in dims['OV_L3_ID']:fields.append(('classChkLi3_1',val+'='))
    for val in ['00','01','02','03']:fields.append(('classChkLi4_1',val+'='))
    return urlencode(fields)


def collect():
    months=make_months()
    if not months:raise RuntimeError('2026년 1월부터 조회할 완료 월 없음')
    post=build_official_form(months)
    url='https://mtrace.go.kr/statHtml/html.do'
    diagnostics=[]
    # Keep the source's own browser session, but do not depend on an incidental initial AJAX call.
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        ctx=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul')
        try:
            page=ctx.new_page()
            initial=page.goto(URL,wait_until='domcontentloaded',timeout=45000)
            diagnostics.append('조회 페이지 HTTP '+str(initial.status if initial else '?'))
            headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                     'X-Requested-With':'XMLHttpRequest','Referer':URL}
            # POST with Chromium session cookies. A response may be HTTP 200 yet contain no table.
            reply=ctx.request.post(url,data=post,headers=headers,timeout=75000)
            diagnostics.append('통계 요청 HTTP '+str(reply.status))
            if reply.status != 200:raise RuntimeError(' / '.join(diagnostics))
            raw=reply.json()
            rows=parse_grade_response(raw)
            first=months[0]
            if not any(r['month']==f'{first[:4]}-{first[4:]}' for r in rows):
                raise ValueError('시작월 누락 (응답 데이터 일부만 반환됨)')
            expected={(f'{m[:4]}-{m[4:]}',s) for m in months for s in ('거세우','암소')}
            actual={(r['month'],r['sex']) for r in rows}
            missing=sorted(expected-actual)
            if missing:
                # Never silently claim full 2026 coverage when source does not supply it.
                raise ValueError(f'요청한 기간 일부 누락: {missing[:5]} (총 {len(missing)}개 성별·월)')
            print('[검증 완료] 공식 표 전국 한우 육질등급 2026-01부터 '+months[-1]+'까지',flush=True)
            return rows
        except Exception as exc:
            raise RuntimeError('육질등급 조회/검증 실패: '+' / '.join(diagnostics)+' / '+str(exc)) from exc
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
