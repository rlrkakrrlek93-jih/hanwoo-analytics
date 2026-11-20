#!/usr/bin/env python3
"""Exploratory public-source probe, does not change website data."""
import json, pathlib, urllib.parse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

SOURCES={
  'hanwoo_inventory':'https://mtrace.go.kr/statHtml/statHtml.do?conn_path=I2&orgId=323&tblId=DT_323901_A100000011',
  'hanwoo_inventory_by_sex':'https://mtrace.go.kr/statHtml/statHtml.do?conn_path=I2&orgId=323&tblId=DT_323901_A100000003',
  'semen_sales':'https://www.ekapepia.com/web/product/semen/cow.do?menuSn=171',
}
def text_table(html):
    soup=BeautifulSoup(html,'html.parser');table=soup.select_one('#mainTable')
    if not table:return {'table_found':False,'html_start':html[:450]}
    headings=[]
    for row in table.select('thead tr')[:4]:
        headings.append([{'name':x.get('name'),'title':x.get('title'),'text':x.get_text(' ',strip=True)[:40],
                          'colspan':x.get('colspan'),'rowspan':x.get('rowspan')}
                        for x in row.find_all(['th','td'],recursive=False)[:35]])
    rows=[]
    for tr in table.select('tbody tr')[:15]:
        vals=[{'text':v.get_text(' ',strip=True)[:34],'title':v.get('title'),'name':v.get('name')}
              for v in tr.find_all(['th','td'],recursive=False)]
        rows.append({'count':len(vals),'first':vals[:16]})
    return {'table_found':True,'header':headings,'rows':rows,'total_rows':len(table.select('tbody tr'))}

def main():
    dest=pathlib.Path('market_probe_output');dest.mkdir(exist_ok=True)
    report={}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        try:
            for ident,url in SOURCES.items():
                page=browser.new_page(locale='ko-KR',timezone_id='Asia/Seoul')
                api=[]
                def receive(resp):
                    try:
                        u=resp.url
                        if '/statHtml/html.do' in u and resp.request.method=='POST' and resp.ok:
                            d=resp.json()
                            if isinstance(d,dict) and isinstance(d.get('result'),list) and d['result'] and 'mainTable' in str(d['result'][0]):
                                api.append({'url':u,'post_data':resp.request.post_data or '',
                                            'json':d})
                    except Exception:pass
                page.on('response',receive)
                try:
                    res=page.goto(url,wait_until='domcontentloaded',timeout=55000)
                    page.wait_for_timeout(8500)
                    if ident.startswith('hanwoo') and not api:
                        try:page.get_by_text('통계표조회',exact=True).first.click(timeout=5000);page.wait_for_timeout(6500)
                        except Exception:pass
                    summary={'status_code':res.status if res else None,'final_url':page.url,'title':page.title(),
                             'body_text':page.locator('body').inner_text(timeout=3500)[:1500],
                             'requests':len(api)}
                    if api:
                        rec=api[-1]
                        summary['post_head']=rec['post_data'][:4500]
                        summary.update(text_table(rec['json']['result'][0]))
                        (dest/f'{ident}_source_response.json').write_text(json.dumps(rec['json'],ensure_ascii=False),encoding='utf-8')
                        (dest/f'{ident}_source_request.txt').write_text(rec['post_data'],encoding='utf-8')
                    if ident=='semen_sales':
                        summary['semen_keywords']=[s for s in ('정액','판매량','2026','2025','지역별') if s in summary['body_text']]
                        summary['response_urls']=[]
                        page.on('response',lambda resp:summary['response_urls'].append({'status':resp.status,'url':resp.url[:250]}) if any(x in resp.url.lower() for x in ('semen','cow','sale','json','ajax')) else None)
                        page.wait_for_timeout(3000)
                        summary['html_inputs']=[{'tag':e.tag_name if hasattr(e,'tag_name') else '', 'id':e.get_attribute('id'),'name':e.get_attribute('name')} for e in page.locator('select,input').all()[:35]]
                    report[ident]=summary
                except Exception as ex:report[ident]={'error':str(ex)[:400]}
                finally:page.close()
        finally:browser.close()
    (dest/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SOURCE_PROBE_SUMMARY '+json.dumps({k:{'status':v.get('status_code'),'table':v.get('table_found'),'rows':v.get('total_rows'),'requests':v.get('requests'),'error':v.get('error'),'keywords':v.get('semen_keywords')} for k,v in report.items()},ensure_ascii=False))

if __name__=='__main__':main()
