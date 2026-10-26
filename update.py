#!/usr/bin/env python3
"""Offline importer for saved mtrace Network Response JSON.
No automated requests are made to the website.
"""
import argparse, csv, json, re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
METRICS=['count','live','weight','fat','rea','yield_index','marbling','price']
SOURCE='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2'

def parse_saved_response(path):
    raw=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(raw,dict) or not raw.get('result') or not isinstance(raw['result'][0],str):
        raise ValueError('통계 응답 JSON의 result[0]에서 HTML 표를 찾을 수 없습니다.')
    soup=BeautifulSoup(raw['result'][0], 'html.parser')
    table=soup.select_one('#mainTable')
    if not table: raise ValueError('mainTable이 없어 업데이트를 중단합니다.')
    # Reconstruct every displayed data column from the three-tier table header.
    # A single month can contain both national data and multiple slaughterhouses.
    head=table.select('thead tr')
    if len(head)<3: raise ValueError('통계표 헤더가 부족합니다.')
    month_columns=[]
    for cell in head[0].find_all(['th','td'],recursive=False):
        name=cell.get('name','')
        if name.startswith('M20'):
            month_columns.extend([name[1:]]*int(cell.get('colspan',1)))
    location_columns=[]
    for cell in head[1].find_all(['th','td'],recursive=False):
        location_columns.extend([cell.get('name','')]*int(cell.get('colspan',1)))
    metric_columns=[]
    for cell in head[2].find_all(['th','td'],recursive=False):
        metric_columns.extend([cell.get('name','')]*int(cell.get('colspan',1)))
    if not month_columns or len(month_columns)!=len(location_columns) or len(month_columns)!=len(metric_columns):
        raise ValueError('월·지역·항목 헤더의 열 수가 일치하지 않습니다.')
    national={}
    for idx,(month,site,metric) in enumerate(zip(month_columns,location_columns,metric_columns)):
        if site=='00':
            national.setdefault(month,{})[metric]=idx
    required={f'T{i:03}' for i in range(1,9)}
    if not national or any(set(fields)!=required for fields in national.values()):
        raise ValueError('전국 항목(T001~T008)을 모두 찾을 수 없습니다.')
    records=[]; current_breed='';current_sex=''
    for tr in table.select('tbody tr'):
        cells=tr.find_all(['td','th'],recursive=False)
        if len(cells)<4: continue
        labels=[c.get_text(' ',strip=True) for c in cells[:3]]
        if labels[0]: current_breed=labels[0]
        if labels[1]: current_sex=labels[1]
        if current_breed!='한우' or current_sex not in ('암','거세') or labels[2]!='전체': continue
        values=cells[3:]
        if len(values)!=len(month_columns):
            raise ValueError(f'{current_sex}의 표 행/헤더 길이 차이: {len(values)} / {len(month_columns)}')
        for month, fields in national.items():
            parts=[values[fields[f'T{i:03}']].get_text(' ',strip=True).replace(',','') for i in range(1,9)]
            if not all(re.fullmatch(r'\d+(?:\.\d+)?',x) for x in parts):
                raise ValueError(f'{month} {current_sex} 전국 항목 숫자 형식 오류: {parts}')
            nums=list(map(float,parts))
            if nums[0]<1 or not 150<=nums[2]<=800 or not 1<=nums[6]<=9:
                raise ValueError(f'{month} {current_sex} 전국 통계 값 범위 오류')
            records.append(dict(month=month[:4]+'-'+month[4:],sex='거세우' if current_sex=='거세' else '암소',count=int(nums[0]),live=nums[1],weight=nums[2],fat=nums[3],rea=nums[4],marbling=nums[6],price=nums[7]))
    records.sort(key=lambda r:(r['month'],0 if r['sex']=='거세우' else 1))
    if len(records)!=len(national)*2:raise ValueError(f'한우 거세우·암소 행 누락: {len(records)}개')
    if any(r['month']<'2026-01' for r in records): records=[r for r in records if r['month']>='2026-01']
    return records

def build(response,template,destination):
    records=parse_saved_response(response)
    # Preserve historical months when the official site only returns a recent window.
    previous=ROOT/'data.json'
    if previous.exists():
        old=json.loads(previous.read_text(encoding='utf-8'))
        merged={(r['month'],r['sex']):r for r in old.get('records',[]) if r['month'] >= '2026-01'}
        merged.update({(r['month'],r['sex']):r for r in records})
        records=sorted(merged.values(),key=lambda r:(r['month'],0 if r['sex']=='거세우' else 1))
    # Never publish an incomplete male/female month.
    by_month={}
    for r in records: by_month.setdefault(r['month'],set()).add(r['sex'])
    if any(v!={'거세우','암소'} for v in by_month.values()): raise ValueError('한우 성별 데이터 누락: 갱신 중단')
    html=Path(template).read_text(encoding='utf-8')
    payload=json.dumps(records,ensure_ascii=False,separators=(',',':'))
    html,n=re.subn(r'const DATA=\[.*?\];\s*const METRICS=',lambda m:'const DATA='+payload+';\nconst METRICS=',html,count=1,flags=re.S)
    if n!=1:raise ValueError('홈페이지 DATA 코드 위치를 찾지 못했습니다.')
    # Timestamp only when a response has been parsed and validated; not an official release time.
    checked=datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')
    meta={'last_success_kst':checked,'official_published_at':None,'validation':'success'}
    html,n_meta=re.subn(r'const UPDATE_META=\{.*?\};',lambda m:'const UPDATE_META='+json.dumps(meta,ensure_ascii=False)+';',html,count=1,flags=re.S)
    if n_meta!=1:raise ValueError('홈페이지 갱신 메타데이터 코드 위치를 찾지 못했습니다.')

    last=records[-1]['month'];first=records[0]['month']
    html=re.sub(r'2026\.01 — 2026\.09',f'{first.replace("-",".")} — {last.replace("-",".")}',html)
    html=html.replace('2026년 1~9월 (현재 확보한 자료)',f'{first} ~ {last} (저장된 응답 기준)')
    html=html.replace('2026년 9월까지의 저장 데이터',f'{last}까지의 저장 데이터')
    html=html.replace('공식 API의 연계 방법이 확인되면', '정기 수집 연계 방식이 확정되면')
    html=html.replace('공식 API 미연결 · 제공 통계 스냅샷','자동 연동 미설정 · 저장된 공식 통계 응답')
    dest=Path(destination);dest.write_text(html,encoding='utf-8')
    (ROOT/'data.json').write_text(json.dumps({'source':SOURCE,'latest_month':last,'last_success_kst':checked,'official_published_at':None,'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser(description='저장된 통계누리 응답 JSON → 한우 홈페이지 갱신')
    p.add_argument('--response',required=True,help='Chrome Network > Response에서 복사하여 저장한 JSON 텍스트 파일')
    p.add_argument('--template',default=str(ROOT/'dashboard_template.html'))
    p.add_argument('--output',default=str(ROOT/'index.html'))
    a=p.parse_args()
    rows=build(a.response,a.template,a.output)
    print(f'완료: {len(rows)}개 월별/성별 행, {rows[0]["month"]} ~ {rows[-1]["month"]}. 홈페이지: {a.output}')
