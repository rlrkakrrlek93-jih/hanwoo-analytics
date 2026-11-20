#!/usr/bin/env python3
"""Trace public Hanwoo semen sales sources, without touching site data."""
import json, pathlib, re
from playwright.sync_api import sync_playwright
SOURCES={
 "old_kape":"https://www.ekapepia.com/web/product/semen/cow.do?menuSn=171",
 "candidate_v3":"https://www.ekapepia.com/v3/supplyTrend/statistics/semen/cow.do",
 "candidate_v3_sales":"https://www.ekapepia.com/v3/supplyTrend/statistics/semenSales/cow.do",
 "hanwoo_report":"https://www.ihanwoo.org/20928",
 "hanwoo_reports":"https://www.ihanwoo.org/board/sub4?Ncode=publication&code=2&tabsNum=2",
 "hanwoo_reports_all":"https://www.ihanwoo.org/board/sub4?Ncode=publication",
 "limc":"https://www.limc.co.kr/Know/Sales_List_iframe.asp"
}
folder=pathlib.Path('semen_probe_result');folder.mkdir(exist_ok=True)
out={}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 try:
  context=browser.new_context(locale='ko-KR',timezone_id='Asia/Seoul',ignore_https_errors=True)
  for key,url in SOURCES.items():
   page=context.new_page();capt=[]
   def catch(resp):
    if resp.request.resource_type in ('fetch','xhr'):
     if len(capt)<40:capt.append({'url':resp.url[:260],'status':resp.status,'method':resp.request.method})
   page.on('response',catch)
   result={'url':url}
   try:
    response=page.goto(url,wait_until='domcontentloaded',timeout=19000)
    page.wait_for_timeout(2000)
    result.update({'status':response.status if response else None,'final_url':page.url,
      'title':page.title(),'text':page.locator('body').inner_text(timeout=4500)[:3200],
      'links':page.locator('a[href]').evaluate_all('xs=>xs.map(x=>({text:x.innerText.trim().slice(0,120),href:x.href})).filter(x=>/pdf|정액|판매|동향|download|semen/i.test(x.text+" "+x.href)).slice(0,35)'),
      'xhr':capt})
   except Exception as exc:result['error']=str(exc)[:280]
   out[key]=result
   print('SOURCE',key,json.dumps({k:v for k,v in result.items() if k in ('status','final_url','title','error')},ensure_ascii=False))
   page.close()
 finally:browser.close()
(folder/'summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
