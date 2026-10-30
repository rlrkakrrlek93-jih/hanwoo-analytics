#!/usr/bin/env python3
"""Read-only probe. Captures public statistical table structures, never edits published data.
Run in existing GitHub Actions Playwright environment. No API key required.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

TABLES = {
  'herd_population': 'DT_323901_A100000003',
  'beef_steer_quality': 'DT_APGS_011',
  'beef_steer_grade_counts': 'DT_APGS_001',
  'slaughter_age': 'DT_323901_A300000005',
}
OUT = Path('new_stats_probe')
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    for label, table_id in TABLES.items():
        responses=[]
        page=browser.new_page(locale='ko-KR',timezone_id='Asia/Seoul')
        def capture(response):
            if '/statHtml/html.do' in response.url and response.request.method=='POST' and response.status==200:
                try:
                    data=response.json()
                    if isinstance(data,dict) and data.get('result'):
                        responses.append(data)
                except Exception:
                    pass
        page.on('response',capture)
        url=f'https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId={table_id}&conn_path=I2'
        try:
            page.goto(url,wait_until='domcontentloaded',timeout=45000)
            page.wait_for_timeout(9000)
            if not responses:
                try:
                    page.get_by_text('통계표조회',exact=True).first.click(timeout=4000)
                    page.wait_for_timeout(6000)
                except Exception:
                    pass
            record={'table_id':table_id,'url':url,'responses':len(responses)}
            if responses:
                raw=responses[-1]
                # Save public HTML only; do not save authentication or request headers.
                html=str(raw['result'][0])
                (OUT/f'{label}_table.html').write_text(html,encoding='utf-8')
                from bs4 import BeautifulSoup
                soup=BeautifulSoup(html,'html.parser')
                tr=soup.select('tr')
                record.update({'row_count':len(tr),'first_rows':[[c.get_text(' ',strip=True)[:100] for c in row.select('th,td')[:12]] for row in tr[:8]]})
            (OUT/f'{label}_summary.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            print(f'{label}: {record["responses"]} response(s), {record.get("row_count",0)} rows')
        except Exception as exc:
            print(f'{label}: ERROR {type(exc).__name__}: {exc}')
        finally:
            page.close()
    browser.close()
print('Done: diagnostic files in new_stats_probe/ (original website untouched)')
