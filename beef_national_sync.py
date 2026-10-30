#!/usr/bin/env python3
"""Official E1080008: 육우·거세·체중 전체·전국 only. Merge verified monthly records."""
import argparse,json,re,os,tempfile
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
URL='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2'
FIELDS=['count','live','weight','fat','area','yield_index','marbling','price']
def parse_table(html):
 s=BeautifulSoup(html,'html.parser'); t=s.select_one('table#mainTable')
 if not t:raise ValueError('mainTable missing')
 heads=t.select('thead tr');months=[h.get('name')[1:5]+'-'+h.get('name')[5:] for h in heads[0].find_all('th') if re.fullmatch(r'M20\d{4}',h.get('name',''))]
 if not months:raise ValueError('month headers missing')
 # Each month has one 전국 block, followed by separate slaughterhouse-specific blocks.
 spans=[]
 for h in heads[1].find_all('th'):
  spans.append((h.get('title',''),int(h.get('colspan') or 1)))
 ptr=0;month_offsets=[]
 for month in months:
  begin=ptr;found=False
  while ptr<len(spans):
   label,width=spans[ptr];ptr+=1
   if label=='전국':
    month_offsets.append((month,begin));found=True
    break
   begin+=width
  if not found:raise ValueError('전국 헤더 누락 '+month)
  # skip remaining market headers until next month block; count each month group from 1st header
  total_span=int(next(h.get('colspan') for h in heads[0].find_all('th') if h.get('name')=='M'+month.replace('-','')))
  used=sum(w for _,w in spans[:ptr]);target=sum(int(h.get('colspan') or 0) for h in heads[0].find_all('th') if h.get('name','').startswith('M20') and h.get('name')<='M'+month.replace('-',''))
  # Months are descending, so use total span relative to consumed header groups.
  while ptr<len(spans) and sum(w for _,w in spans[:ptr])<sum(int(h.get('colspan') or 0) for h in heads[0].find_all('th') if h.get('name','').startswith('M20') and months.index(h.get('name')[1:5]+'-'+h.get('name')[5:])<=months.index(month)):
   ptr+=1
 row=None
 for tr in t.select('tbody tr'):
  cells=[c.get('title','').strip() for c in tr.find_all('td',recursive=False)]
  if len(cells)>3 and cells[:3]==['육우','거세','전체']:row=cells;break
 if row is None:raise ValueError('육우/거세/전체 행 없음')
 records={};position=0
 for month in months:
  values=row[3+position:3+position+8]
  if len(values)<8:break
  try:nums=[float(v.replace(',','')) for v in values]
  except ValueError:nums=[]
  if nums and 100<=nums[0]<=30000 and 200<=nums[2]<=700 and 0<=nums[6]<=9:
   rec={'month':month,'breed':'육우','sex':'거세우'}
   for key,val in zip(FIELDS,nums):rec[key]=int(val) if key=='count' else val
   records[month]=rec
  mhead=next(h for h in heads[0].find_all('th') if h.get('name')=='M'+month.replace('-',''))
  position+=int(mhead.get('colspan'))
 if not records:raise ValueError('검증된 전국 육우 거세우 자료 없음')
 return records
def live():
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(locale='ko-KR',timezone_id='Asia/Seoul');answers=[]
  def capture(resp):
   if '/statHtml/html.do' not in resp.url or resp.request.method!='POST' or resp.status!=200:return
   try:
    obj=resp.json()
    if obj.get('result') and 'mainTable' in str(obj['result'][0]):answers.append(obj['result'][0])
   except Exception:pass
  page.on('response',capture)
  try:
   page.goto(URL,wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(8000)
   if not answers:
    try:page.get_by_text('통계표조회',exact=True).first.click(timeout=3000);page.wait_for_timeout(7000)
    except Exception:pass
   if not answers:raise RuntimeError('공식 통계표 응답 없음')
   return answers[-1]
  finally:b.close()
def parse_age(html):
 s=BeautifulSoup(html,'html.parser');out={}
 for tr in s.select('#mainTable tbody tr'):
  values=[td.get('title','').strip() for td in tr.find_all('td',recursive=False)]
  m=re.match(r'^(20\d{2})\.\s*(\d{2})$',values[0] if values else '')
  if m and len(values)>=11:
   try:out[m.group(1)+'-'+m.group(2)]=float(values[10])
   except ValueError:pass
 return out
def main():
 arg=argparse.ArgumentParser();arg.add_argument('--html',help='공식 HTML 응답으로 오프라인 검증');args=arg.parse_args()
 page_html=Path(args.html).read_text('utf-8') if args.html else live()
 newer=parse_table(page_html)
 # Optional second official table for slaughter ages; do not fail national quality update if unavailable.
 if not args.html:
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(locale='ko-KR',timezone_id='Asia/Seoul');answers=[]
    def cap(resp):
     if '/statHtml/html.do' in resp.url and resp.request.method=='POST' and resp.status==200:
      try:
       data=resp.json()
       if data.get('result') and 'mainTable' in str(data['result'][0]):answers.append(data['result'][0])
      except Exception:pass
    page.on('response',cap)
    try:page.goto('https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323901_A300000005&conn_path=I2',wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(7000)
    finally:browser.close()
    if answers:
     for m,age in parse_age(answers[-1]).items():
      if m in newer:newer[m]['age_months']=age
  except Exception as exc:print('Age data unavailable this run:',str(exc)[:160])
 file=ROOT/'beef_national_data.json';old={}
 if file.exists():
  try:old={r['month']:r for r in json.loads(file.read_text('utf-8')).get('records',[])}
  except Exception:pass
 for month,rec in newer.items():
  if 'age_months' not in rec and month in old and 'age_months' in old[month]:rec['age_months']=old[month]['age_months']
 old.update(newer)
 payload={'source_table':'DT_323903_E1080008','definition':'전국 육우 거세우, 체중간격 전체, 등급판정 항목별 평균','records':[old[k] for k in sorted(old)]}
 fd,tmp=tempfile.mkstemp(dir=ROOT,prefix='.beef_national_',suffix='.json')
 try:
  with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
  os.replace(tmp,file)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 print('Verified beef steer national:', ', '.join(sorted(newer)))
if __name__=='__main__':main()
