#!/usr/bin/env python3
"""Read official public report PDFs and extract Hanwoo semen monthly table fragments."""
import json,re
from pathlib import Path
import requests,fitz
SOURCES={
 "2025-feb":"https://www.ihanwoo.org/file_c/file_download?fname=ax_6049658841.pdf&furl=%2Fupload&orifname=2025%EB%85%84+2%EC%9B%94+%ED%95%9C%EC%9A%B0+%EB%8F%99%ED%96%A5+%EB%B6%84%EC%84%9D.pdf",
 "2025-jun":"https://www.ihanwoo.org/file_c/file_download?furl=/upload&fname=ax_9838022113.pdf&orifname=2025%EB%85%84+6%EC%9B%94+%ED%95%9C%EC%9A%B0+%EB%8F%99%ED%96%A5+%EB%B6%84%EC%84%9D.pdf"
}
out={}
for name,url in SOURCES.items():
  row={'url':url}
  try:
    response=requests.get(url,timeout=45,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.ihanwoo.org/20928'})
    row['http']=response.status_code;row['type']=response.headers.get('Content-Type');row['size']=len(response.content)
    if response.status_code==200 and response.content.startswith(b'%PDF'):
      doc=fitz.open(stream=response.content,filetype='pdf')
      hit=[]
      for i,page in enumerate(doc):
        t=page.get_text(sort=True)
        if '정액' in t and any(s in t for s in ('천str','천 str','정액판매','정액 판매','표 6')):
          idx=t.find('정액')
          hit.append({'page':i+1,'fragment':t[max(0,idx-100):idx+1800]})
      row['pages']=doc.page_count;row['hits']=hit[-6:]
    else:row['preview']=response.text[:500]
  except Exception as e:row['error']=str(e)[:400]
  out[name]=row
  print('REPORT',name,'http',row.get('http'),'size',row.get('size'),'hits',len(row.get('hits',[])))
Path('semen_probe_result').mkdir(exist_ok=True)
Path('semen_probe_result/reports.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
