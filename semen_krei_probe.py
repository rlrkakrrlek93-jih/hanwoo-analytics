#!/usr/bin/env python3
"""Diagnostic-only extraction of published KREI Hanwoo semen sales tables."""
from __future__ import annotations
import json, pathlib, re
import requests, fitz
from playwright.sync_api import sync_playwright
PDF="https://www.aglook.kr/upload/observeFiles/cb83caf9fe9648a58f43611e1d0c06b3.pdf"
HOME="https://www.aglook.kr/main/uObserveMonth/OVR0000000015"
out=pathlib.Path("krei_probe_output");out.mkdir(exist_ok=True)
report={}
try:
 r=requests.get(PDF,timeout=45,headers={"User-Agent":"Mozilla/5.0"})
 report["pdf_http"]=r.status_code;report["pdf_content_type"]=r.headers.get("Content-Type");report["pdf_bytes"]=len(r.content)
 if r.ok and r.content[:4]==b"%PDF":
  doc=fitz.open(stream=r.content,filetype="pdf")
  report["pdf_pages"]=len(doc)
  report["pdf_text_samples"]=[{"page":i+1,"text":page.get_text(sort=True)[:1400]} for i,page in enumerate(doc) if i<4]
  (out/"krei_march_2026.pdf").write_bytes(r.content)
  for i,page in enumerate(doc):
   raw=page.get_text(sort=True)
   if "정액" in raw and "2025" in raw:
    tables=[]
    try:
     tabs=page.find_tables()
     tables=[{"rows":len(t.extract()),"sample":t.extract()[:8]} for t in tabs.tables[:8]]
    except Exception as e:tables=[{"error":str(e)}]
    report.setdefault("semen_pages",[]).append({"page":i+1,"text":raw[:9000],"tables":tables,"words":page.get_text("words")[:100]})
except Exception as e:report["pdf_error"]=str(e)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
  page=browser.new_page(locale="ko-KR")
  events=[]
  page.on("response",lambda resp:events.append({"url":resp.url[:350],"status":resp.status}) if "download" in resp.url.lower() or "observe" in resp.url.lower() else None)
  page.goto(HOME,wait_until="domcontentloaded",timeout=40000);page.wait_for_timeout(4500)
  report["site"]={"url":page.url,"title":page.title(),
    "body_head":page.locator("body").inner_text()[:2500],
    "links":page.locator("a").evaluate_all("els=>els.filter(x=>/PDF|다운로드|한육우/.test(x.innerText||'')).map(x=>({text:x.innerText.slice(0,70),href:x.href,onclick:x.getAttribute('onclick')})).slice(0,35)"),
    "events":events[:30]}
  for ident,href in [('sep_2026','https://www.aglook.kr/main/uObserveMonth/OVR0000000015/download/8752/ORGTEXT_FILE'),
     ('jun_2026','https://www.aglook.kr/main/uObserveMonth/OVR0000000015/download/8708/ORGTEXT_FILE')]:
    try:
     req=page.request.get(href,timeout=35000,headers={'Referer':HOME})
     body=req.body()
     item={'status':req.status,'bytes':len(body),'type':req.headers.get('content-type'),'prefix':repr(body[:20])}
     if body[:4]==b'%PDF' and len(body)<25000000:
       (out/(ident+'.pdf')).write_bytes(body)
       pdf=fitz.open(stream=body,filetype='pdf')
       item['pages']=len(pdf)
       item['text_sample']=[{'page':i+1,'text':pg.get_text(sort=True)[:1500]} for i,pg in enumerate(pdf) if i<5]
     report[ident]=item
    except Exception as e:report[ident]={'error':str(e)[:350]}
  browser.close()
except Exception as e:report["site_error"]=str(e)
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("KREI PROBE",json.dumps({"pdf":report.get("pdf_http"),"pages":report.get("pdf_pages"),"sales_pages":len(report.get("semen_pages",[])),"site":report.get("site",{}).get("title"),"site_error":report.get("site_error")},ensure_ascii=False))
