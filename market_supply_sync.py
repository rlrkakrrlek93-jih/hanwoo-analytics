#!/usr/bin/env python3
"""HANWOO INSIGHT monthly supply indicators. Public official table HTML; no keys.

Stock: nationwide Hanwoo farm inventory at month end (A100000011).
Flow: nationwide Hanwoo carcass-grade headcount during month (E1080008), including female, male and steer.
Never infer missing values or silently mix stock/flow populations.
On failure, the last verified production JSON remains unchanged.
"""
from __future__ import annotations
import argparse,json,os,re,tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl,urlencode
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'market_supply_data.json'
STATUS=ROOT/'market_supply_status.json'
INVENTORY_TABLE='DT_323901_A100000011'
GRADING_TABLE='DT_323903_E1080008'
BASE='https://mtrace.go.kr/statHtml/statHtml.do?conn_path=I2&orgId=323&tblId='
ENDPOINT='https://mtrace.go.kr/statHtml/html.do'
SEXES=('암','수','거세')
INTEGER=re.compile(r'^\d[\d,]*$')
MONTH_NAME=re.compile(r'M(20\d{4})$')

def kst_now():
    return datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')

def last_complete():
    t=datetime.now(ZoneInfo('Asia/Seoul'))
    y,m=t.year,t.month-1
    if not m:y,m=y-1,12
    return f'{y:04d}-{m:02d}'

def desired_months():
    end=last_complete()
    y,m=2024,1;out=[]
    while f'{y:04d}-{m:02d}'<=end:
        out.append(f'{y:04d}{m:02d}')
        m+=1
        if m>12:y,m=y+1,1
    return out

def cells(tr):
    return tr.find_all(['th','td'],recursive=False)

def repeat_names(items, prefix=None):
    out=[]
    for c in items:
        name=c.get('name','')
        if prefix and not re.fullmatch(prefix,name):continue
        out += [name]*int(c.get('colspan','1'))
    return out

def strict_int(cell):
    s=(cell.get('title') or cell.get_text(' ',strip=True)).replace(' ','').strip()
    if not INTEGER.fullmatch(s):raise ValueError('Non-integer official count: '+repr(s))
    return int(s.replace(',',''))

def table_of(response):
    if not isinstance(response,dict) or not isinstance(response.get('result'),list) or not response['result']:
        raise ValueError('Official response has no result table')
    table=BeautifulSoup(response['result'][0],'html.parser').select_one('table#mainTable')
    if table is None:raise ValueError('mainTable missing')
    return table

def month_header(table):
    head=table.select('thead tr')
    if not head:raise ValueError('Table heading missing')
    return head,repeat_names(cells(head[0]),r'M20\d{4}')

def parse_inventory(response):
    table=table_of(response);head,month_codes=month_header(table)
    if len(head)<2:raise ValueError('Inventory header is incomplete')
    farm=repeat_names(cells(head[1]))
    if len(month_codes)!=len(farm):raise ValueError('Inventory month/farm header mismatch')
    nationwide=[]
    for tr in table.select('tbody tr'):
        c=cells(tr)
        if c and (c[0].get('title') or c[0].get_text(' ',strip=True)).strip()=='전국':
            nationwide=c
            break
    if not nationwide:raise ValueError('Nationwide inventory row missing')
    if len(nationwide)-1!=len(month_codes):raise ValueError('Nationwide row width mismatch')
    result={};details={}
    for mo in sorted(set(month_codes)):
        columns={f:i for i,(month,f) in enumerate(zip(month_codes,farm)) if month==mo}
        if set(columns)!={'00','01','02','03'}:raise ValueError('Expected total+3 farm types for '+mo)
        vals={f:strict_int(nationwide[1+i]) for f,i in columns.items()}
        if vals['00'] != vals['01']+vals['02']+vals['03']:
            raise ValueError('Farm type subtotals inconsistent: '+mo)
        if not 1000000<=vals['00']<=6000000:raise ValueError('Nationwide Hanwoo inventory outside plausibility range')
        month=mo[1:5]+'-'+mo[5:]
        result[month]=vals['00']
        details[month]={'breeding':vals['01'],'fattening':vals['02'],'integrated':vals['03']}
    return result,details

def parse_grading(response):
    table=table_of(response);head,month_codes=month_header(table)
    if len(head)<3:raise ValueError('Grading header tiers missing')
    regions=repeat_names(cells(head[1]))
    metrics=repeat_names(cells(head[2]))
    if len(month_codes)!=len(regions) or len(month_codes)!=len(metrics):
        raise ValueError('Grading multiheader width mismatch')
    expected=set(month_codes)
    indexes={}
    for i,(mo,region,metric) in enumerate(zip(month_codes,regions,metrics)):
        if region=='00' and metric in ('T001','T008'):
            indexes.setdefault(mo,{})[metric]=i
    if set(indexes)!=expected or any(set(v)!={'T001','T008'} for v in indexes.values()):
        raise ValueError('National graded count and auction price fields missing')
    grouped={};prices={};breed=sex=''
    for tr in table.select('tbody tr'):
        c=cells(tr)
        if len(c)<4:continue
        labels=[x.get_text(' ',strip=True) for x in c[:3]]
        breed=labels[0] or breed
        sex=labels[1] or sex
        if breed!='한우' or sex not in SEXES or labels[2]!='전체':continue
        for month_code,fieldpos in indexes.items():
            countidx=fieldpos['T001']
            priceidx=fieldpos['T008']
            if 3+max(countidx,priceidx)>=len(c):
                raise ValueError('Grade/price column out of bounds')
            value=strict_int(c[3+countidx])
            if not 0<=value<=250000:raise ValueError('Grade count outside range')
            key=(month_code[1:5]+'-'+month_code[5:],sex)
            if key in grouped:raise ValueError('Duplicate grade sex '+str(key))
            grouped[key]=value
            try:
                price=strict_int(c[3+priceidx])
                if not 1000<=price<=100000:raise ValueError('Auction price outside plausible range')
            except ValueError:
                price=None
            prices[key]=price
    result={};details={}
    for month in sorted({k[0] for k in grouped}):
        if any((month,sex) not in grouped for sex in SEXES):
            raise ValueError('Hanwoo female+male+steer incomplete '+month)
        v={sex:grouped[(month,sex)] for sex in SEXES}
        total=sum(v.values())
        if not 10000<=total<=250000:raise ValueError('Invalid grading total '+month)
        result[month]=total
        details[month]={'female':v['암'],'male':v['수'],'steer':v['거세'],
                        'auction_price_by_sex':{
                          'female':prices.get((month,'암')),
                          'male':prices.get((month,'수')),
                          'steer':prices.get((month,'거세'))}}
    return result,details

def capture(ctx,table_id):
    url=BASE+table_id
    page=ctx.new_page()
    recorded=[]
    def on_response(resp):
        if '/statHtml/html.do' not in resp.url or resp.request.method!='POST' or resp.status!=200:return
        try:
            raw=resp.json()
            if isinstance(raw,dict) and raw.get('result') and 'mainTable' in str(raw['result'][0]):
                recorded.append((resp.request.post_data or '',raw))
        except Exception:pass
    page.on('response',on_response)
    try:
        page.goto(url,wait_until='domcontentloaded',timeout=55000)
        page.wait_for_timeout(8000)
        if not recorded:
            try:
                q=page.get_by_text('통계표조회',exact=True)
                if q.count():q.first.click(timeout=5000);page.wait_for_timeout(5500)
            except Exception:pass
        if not recorded:raise RuntimeError('Official table response not captured '+table_id)
        return recorded[-1]
    finally:page.close()

def query_months(ctx,table_id,post_data,months):
    """Reuse the actual site-generated, public form; change only month selection."""
    pairs=parse_qsl(post_data,keep_blank_values=True)
    matched=False
    rebuilt=[]
    for key,value in pairs:
        if key=='fieldList':
            fields=json.loads(value)
            for entry in fields:
                if entry.get('targetId')=='PRD':
                    entry['prdValue']='M,'+','.join(reversed(months))+',@'
                    entry['targetValue']=''
                    matched=True
            value=json.dumps(fields,ensure_ascii=False,separators=(',',':'))
        elif key=='timeChkM':
            continue
        rebuilt.append((key,value))
    if not matched:raise ValueError('Official query does not expose a PRD month field')
    rebuilt += [('timeChkM',mo) for mo in reversed(months)]
    response=ctx.request.post(ENDPOINT,data=urlencode(rebuilt),headers={
      'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With':'XMLHttpRequest','Referer':BASE+table_id},timeout=60000)
    if response.status!=200:raise RuntimeError(f'Official table HTTP {response.status} ({table_id})')
    raw=response.json()
    table_of(raw) # fail early on partial/error responses
    return raw

def collect_table(ctx,table_id,parser,months):
    original_form,original=capture(ctx,table_id)
    first,detail=parser(original)
    collected=dict(first);sub=dict(detail)
    missing=[mo for mo in months if mo[:4]+'-'+mo[4:] not in collected]
    for i in range(0,len(missing),3):
        batch=missing[i:i+3]
        if not batch:continue
        try:
            rows,parts=parser(query_months(ctx,table_id,original_form,batch))
            for mo in batch:
                key=mo[:4]+'-'+mo[4:]
                if key not in rows:raise ValueError('Official source omitted requested month '+key)
            collected.update(rows);sub.update(parts)
        except Exception as exc:
            print('Historical source query failed; no invented values:',table_id,batch,str(exc)[:220])
    return collected,sub

def verify_records(records):
    seen=set()
    for r in records:
        mo=r.get('month')
        if not isinstance(mo,str) or not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',mo) or mo>last_complete():
            raise ValueError('Bad month in supply record')
        if mo in seen:raise ValueError('Duplicate supply month '+mo)
        seen.add(mo)
        if type(r.get('inventory_head')) is not int or type(r.get('graded_head')) is not int:
            raise ValueError('Missing integer supply data')
        if not 1000000<=r['inventory_head']<=6000000 or not 10000<=r['graded_head']<=250000:
            raise ValueError('Implausible supply statistics')
        inv=r.get('inventory_by_farm',{})
        grade=r.get('graded_by_sex',{})
        if sum(inv.values())!=r['inventory_head'] or sum(grade.values())!=r['graded_head']:
            raise ValueError('Breakdown mismatch '+mo)
        price=r.get('auction_price_by_sex')
        if price is not None:
            if not isinstance(price,dict):raise ValueError('Invalid auction price object')
            for sex,val in price.items():
                if sex not in ('female','male','steer') or (val is not None and (type(val) is not int or not 1000<=val<=100000)):
                    raise ValueError('Invalid auction price '+mo+' '+sex)
    return True

def atomic_write(path,obj):
    fd,name=tempfile.mkstemp(dir=ROOT,prefix='.market_',suffix='.json')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)

def build(inv,inv_parts,graded,grade_parts,old=None):
    old=old or {}
    prior={r['month']:r for r in old.get('records',[])}
    for mo in set(inv)&set(graded):
        prior[mo]=dict(month=mo,inventory_head=inv[mo],graded_head=graded[mo],
                       inventory_by_farm=inv_parts[mo],
                       graded_by_sex={k:v for k,v in grade_parts[mo].items() if k!='auction_price_by_sex'},
                       auction_price_by_sex=grade_parts[mo].get('auction_price_by_sex',{}))
    records=[prior[x] for x in sorted(prior) if x>='2024-01']
    verify_records(records)
    if not records:raise ValueError('No matching official inventory and graded months')
    return dict(schema_version=1,source_inventory=BASE+INVENTORY_TABLE,
        source_grading=BASE+GRADING_TABLE,inventory_definition='월말 전국 한우 사육두수 (농장 사육형태 전체)',
        grading_definition='월중 전국 한우 도체 판정두수 (암·수·거세 포함)',
        price_definition='월중 전국 한우 성별 경락단가(원/kg), 공표 원본; 한우 전체 평균으로 혼합 계산하지 않음',
        last_success_kst=kst_now(),latest_month=records[-1]['month'],records=records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    try:
        with sync_playwright() as pl:
            browser=pl.chromium.launch(headless=True,args=['--no-sandbox'])
            try:
                ctx=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul')
                all_months=desired_months()
                old=json.loads(OUT.read_text(encoding='utf8')) if OUT.exists() else {}
                stored={r['month']:r for r in old.get('records',[]) if isinstance(r,dict) and 'month' in r}
                recent=set(all_months[-4:])
                missing={x for x in all_months if x[:4]+'-'+x[4:] not in stored}
                missing_price={x for x in all_months if
                    (r:=stored.get(x[:4]+'-'+x[4:])) is not None and
                    ('auction_price_by_sex' not in r or
                     any(r.get('auction_price_by_sex',{}).get(k) is None for k in ('steer','female')))}
                months=sorted(recent|missing|missing_price)
                print('Monthly source check:',len(months),'months;',len(missing),'new,',len(missing_price),'missing price,',len(recent),'recent')
                inv,inv_parts=collect_table(ctx,INVENTORY_TABLE,parse_inventory,months)
                grade,grade_parts=collect_table(ctx,GRADING_TABLE,parse_grading,months)
            finally:browser.close()
        result=build(inv,inv_parts,grade,grade_parts,old)
        print('Verified official supply',result['latest_month'],len(result['records']),
              'inventory',result['records'][-1]['inventory_head'],
              'graded',result['records'][-1]['graded_head'])
        if args.dry_run:
            print('MARKET_DATA_PAYLOAD='+json.dumps(result,ensure_ascii=False,separators=(',',':')))
        if not args.dry_run:
            atomic_write(OUT,result)
            atomic_write(STATUS,{'status':'verified','checked_at_kst':kst_now(),
                'latest_month':result['latest_month'],'rows':len(result['records'])})
    except Exception as exc:
        print('Supply update blocked, existing file retained:',str(exc))
        if not args.dry_run:
            atomic_write(STATUS,{'status':'blocked_previous_kept','checked_at_kst':kst_now(),
                'message':str(exc)[:450]})
        # A dry run must fail CI; scheduled updates preserve previous verified files.
        if args.dry_run: raise
        return 0
    return 0

if __name__=='__main__':
    raise SystemExit(main())
