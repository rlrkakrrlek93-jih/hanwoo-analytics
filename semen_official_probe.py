#!/usr/bin/env python3
"""Inspect only public official Hanwoo semen data pages and PDF reports. Diagnostic, never writes user statistics."""
from __future__ import annotations
import json,re,pathlib
import requests
from bs4 import BeautifulSoup
import fitz

DIR=pathlib.Path("semen_source_probe");DIR.mkdir(exist_ok=True)
URLS={
 "limc":"https://www.limc.co.kr/Know/Sales_List_iframe.asp",
 "ekapepia_v2":"https://www.ekapepia.com/web/product/semen/cow.do?menuSn=171",
 "ekapepia_v3":"https://www.ekapepia.com/v3/supplyTrend/productTrend/semen/cow.do",
 "krei":"https://www.aglook.kr/main/uObserveMonth/OVR0000000015",
 "krei_sep26":"https://www.aglook.kr/main/uObserveMonth/OVR0000000015/download/8752/ORGTEXT_FILE",
 "krei_mar26":"https://www.aglook.kr/upload/observeFiles/cb83caf9fe9648a58f43611e1d0c06b3.pdf",
}
headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
out={}
session=requests.Session()
for key,url in URLS.items():
 try:
  r=session.get(url,headers=headers,timeout=30,allow_redirects=True)
  info=dict(code=r.status_code,final_url=r.url,content_type=r.headers.get('Content-Type'),bytes=len(r.content),encoding=r.encoding,header=r.content[:35].hex())
  if r.content.startswith(b'%PDF'):
   pdf=fitz.open(stream=r.content,filetype='pdf')
   info['pages']=len(pdf)
   info['page_samples']=[]
   for i in range(min(len(pdf),6)):
    pg=pdf[i]
    t=pg.get_text(sort=True)
    info['page_samples'].append(dict(page=i+1,text_length=len(t),text=t[:9500],images=len(pg.get_images()),tables=[z.extract()[:12] for z in pg.find_tables().tables[:2]]))
  else:
   r.encoding=r.apparent_encoding or r.encoding
   html=r.text
   soup=BeautifulSoup(html,'html.parser')
   info['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
   info['body']=soup.get_text(' ',strip=True)[:4500]
   info['scripts']=[x.get('src') for x in soup.select('script[src]')][-35:]
   info['links']=[dict(t=a.get_text(' ',strip=True)[:90],href=a.get('href')) for a in soup.select('a[href]') if re.search('정액|2026|한우|다운로드|검색|판매',a.get_text(' ',strip=True))][:55]
   info['forms']=[dict(action=f.get('action'),method=f.get('method'),fields=[{"name":e.get('name'),"value":str(e.get('value',''))[:50]} for e in f.select('[name]')][:40]) for f in soup.select('form')][:3]
   info['fragments']=[html[max(0,m.start()-200):m.end()+220] for m in list(re.finditer('정액판매량|정액판매|semenSales|salesData|semenInfo|ajax|2026년',html,re.I))[:20]]
   (DIR/(key+'.html')).write_text(html,encoding='utf8')
  out[key]=info
 except Exception as e:out[key]={'error':str(e)}
 (DIR/'probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 print("PROBE",key,json.dumps({k:v for k,v in out[key].items() if k not in ('body','page_samples','fragments','forms','scripts','links')},ensure_ascii=False))
print("SUMMARY "+json.dumps({key:{k:v for k,v in obj.items() if k in('code','bytes','pages','error','final_url','encoding')} for key,obj in out.items()},ensure_ascii=False))
