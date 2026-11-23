#!/usr/bin/env python3
"""Native-style HANWOO INSIGHT mobile application regression, running without network APIs."""
from __future__ import annotations
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def run():
 from test_mobile_pwa_browser import verify_png
 for path,size in [('pwa/icon-192.png',192),('pwa/icon-512.png',512),('pwa/apple-touch-icon.png',180)]:
  verify_png(path,size)
 manifest=json.loads((ROOT/'manifest.webmanifest').read_text('utf8'))
 assert manifest['start_url']=='./app.html'
 for name in ['app.html','app.css','app.js','service-worker.js','index.html','dashboard_template.html']:
  assert (ROOT/name).exists(),name
 for name in ['index.html','dashboard_template.html']:
  assert "location.replace('./app.html'" in (ROOT/name).read_text('utf8')
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
 Thread(target=server.serve_forever,daemon=True).start()
 base=f'http://127.0.0.1:{server.server_port}'
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
   try:
    for size in [(390,844),(375,812),(768,1024)]:
     w,h=size
     ctx=browser.new_context(viewport={'width':w,'height':h},is_mobile=True,has_touch=True,
       device_scale_factor=2,locale='ko-KR',service_workers='allow')
     page=ctx.new_page();errors=[]
     page.on('pageerror',lambda exc:errors.append(str(exc)))
     page.goto(base+'/index.html',wait_until='domcontentloaded',timeout=30000)
     page.wait_for_url('**/app.html*',timeout=12000)
     assert page.locator('.app-screen').count()==4
     assert page.locator('.bottom-tabs a').count()==4
     page.locator('#home .overview-hero .lead-number').wait_for(timeout=18000)
     assert '24,616' in page.locator('#home .overview-hero .lead-number').inner_text()
     assert '313.9' in page.locator('#home .stat-grid').inner_text()
     assert '171.3' in page.locator('#home .stat-grid').inner_text()
     assert page.locator('#home').is_visible()
     dims=page.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})')
     assert dims['scroll']<=dims['viewport']+2,('page horizontal overflow',w,dims)
     page.locator('a[data-tab="market"]').click()
     page.locator('#market').wait_for(state='visible',timeout=10000)
     page.locator('#home').wait_for(state='hidden',timeout=10000)
     assert page.locator('#market .data-table tbody tr').count()==12
     assert page.locator('#market [data-chart-point="market"]').count()>25
     market_lines=page.locator('#market svg [data-chart-line="market"]')
     assert market_lines.count()==3
     for line in market_lines.all():
      assert line.get_attribute('d').startswith('M '), "SVG year paths must begin with move-to"
      assert ' L ' in line.get_attribute('d'), "Months must join with solid line segments"
      assert line.get_attribute('stroke-width')=='1.9'
      assert line.get_attribute('stroke-dasharray') is None

     page.locator('[data-market-metric="graded"]').click()
     assert '판정두수' in page.locator('#marketContent .chart-heading').inner_text()
     page.locator('[data-market-metric="price"]').click()
     page.locator('#marketSex').select_option('female')
     assert '암소 경락가격' in page.locator('#marketContent .chart-heading').inner_text()
     assert '21,722' in page.locator('#marketContent .kpi-mini').first.inner_text()
     page.locator('button[data-month-choice="market"][data-month="1"]').click()
     assert '1월 · 암소 경락가격' in page.locator('#marketContent .month-detail b').inner_text()
     page.locator('a[data-tab="semen"]').click()
     page.locator('#semen').wait_for(state='visible',timeout=10000)
     assert page.locator('#semen .data-table tbody tr').count()==12
     assert page.locator('#semen .data-table thead th').count()==6
     assert page.locator('#semen .data-table tbody tr').nth(5).locator('td').nth(4).inner_text()=='157.6'
     assert page.locator('#semen .data-table tbody tr').nth(6).locator('td').nth(5).inner_text()=='171.3'
     assert page.locator('#semen [data-chart-point="semen"]').count()==55
     semen_lines=page.locator('#semen svg [data-chart-line="semen"]')
     assert semen_lines.count()==5
     for line in semen_lines.all():
      assert line.get_attribute('d').startswith('M ')
      assert ' L ' in line.get_attribute('d'), "Semen sale monthly dots should be connected"
      assert line.get_attribute('stroke-width')=='1.9'
     july_2026=page.locator('#semen svg path[data-chart-line="semen"][data-year="2026"]')
     assert july_2026.get_attribute('d').count(' L ')==6, "2026 seven published months yield six line segments"

     assert page.locator('#semen .data-table tbody tr').nth(6).locator('td').nth(5).locator('a').get_attribute('href').startswith('https://')
     page.locator('button[data-semen-year="2023"]').click()
     assert page.locator('#semen [data-chart-point="semen"]').count()==43
     page.locator('a[data-tab="quality"]').click()
     page.locator('#quality').wait_for(state='visible',timeout=10000)
     assert page.locator('#quality .grade-item').count()==5
     # The summary uses the separately published grade-distribution table.
     top_grade=page.locator('#quality .stat-card').nth(2)
     assert '1++ 출현율' in top_grade.inner_text()
     assert '48.3' in top_grade.inner_text() and '%' in top_grade.inner_text()
     assert '16,604두' in top_grade.inner_text()
     assert '평균 근내지방도' not in top_grade.inner_text()
     assert page.locator('#quality [data-quality-mode="month"]').get_attribute('aria-selected')=='true'
     page.locator('#quality [data-quality-mode="ytd"]').click()
     assert page.locator('#quality [data-quality-mode="ytd"]').get_attribute('aria-selected')=='true'
     assert '46.2%' in page.locator('#quality .stat-card').nth(2).inner_text()
     assert '175,381두' in page.locator('#quality .stat-card').nth(2).inner_text()
     assert '379,210' in page.locator('#quality .stat-card').nth(3).inner_text()
     assert '누적' in page.locator('#quality .quality-rollup-note').first.inner_text()
     assert '월별 성적 추이' in page.locator('#qualityContent').inner_text()
     page.locator('#qualityMonth').select_option('2026-09')
     assert '1~9월' in page.locator('#quality .stat-card').nth(2).inner_text()
     page.locator('#qualityMonth').select_option('2026-10')
     assert '46.2%' in page.locator('#quality .stat-card').nth(2).inner_text()
     # Regression: cattle category is not a calendar year ("거세우년").
     assert page.locator('#quality .chart-legend').inner_text().strip()=='거세우'
     assert '거세우년' not in page.locator('#qualityContent').inner_text()
     assert page.locator('#quality svg [data-chart-point="quality"]').first.get_attribute('aria-label').startswith('거세우 2026년')
     page.locator('[data-quality-sex="암소"]').click()
     assert '16.8%' in page.locator('#quality .stat-card').nth(2).inner_text()
     assert '60,583두' in page.locator('#quality .stat-card').nth(2).inner_text()
     assert '358,938' in page.locator('#quality .stat-card').nth(3).inner_text()
     page.locator('[data-quality-mode="month"]').click()
     assert '18.5%' in page.locator('#quality .stat-card').nth(2).inner_text()
     assert page.locator('#quality .chart-legend').inner_text().strip()=='암소'
     assert '암소년' not in page.locator('#qualityContent').inner_text()
     assert page.locator('[data-quality-sex="암소"]').get_attribute('aria-selected')=='true'
     page.locator('#qualityMetric').select_option('marbling')
     assert '근내지방도' in page.locator('#qualityContent .chart-heading').inner_text()
     quality_line=page.locator('#quality svg path[data-chart-line="quality"]')
     assert quality_line.count()==1
     assert quality_line.get_attribute('d').startswith('M ')
     assert ' L ' in quality_line.get_attribute('d')

     if w==390:
      output=ROOT/'test_artifacts';output.mkdir(exist_ok=True)
      page.locator('#quality').screenshot(path=str(output/'native_mobile_quality.png'))
      page.locator('a[data-tab="home"]').click()
      page.locator('#home').screenshot(path=str(output/'native_mobile_home.png'))
      page.locator('a[data-tab="market"]').click()
      page.locator('#market').screenshot(path=str(output/'native_mobile_market.png'))
      page.locator('a[data-tab="semen"]').click()
      page.locator('#semen').screenshot(path=str(output/'native_mobile_semen.png'))
      # Offline launch should use the cache populated by the service worker.
      page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller !== null",timeout=25000)
      ctx.set_offline(True)
      page.reload(wait_until='domcontentloaded',timeout=20000)
      assert page.locator('#offlineNotice').is_visible()
      assert page.locator('#appMain').count()==1
      assert page.locator('#semen .data-table tbody tr').count()==12
      ctx.set_offline(False)
     assert not errors,errors[:4]
     ctx.close()
    # Unchanged large-screen desktop site and explicit override for mobile.
    desktop=browser.new_context(viewport={'width':1280,'height':900},locale='ko-KR')
    dpage=desktop.new_page()
    dpage.goto(base+'/index.html',wait_until='domcontentloaded',timeout=30000)
    dpage.locator('#marketScope .mk-card').first.wait_for(timeout=18000)
    assert '/app.html' not in dpage.url
    assert dpage.locator('#semenSalesScope .ss-table tbody tr').count()==12
    assert not dpage.locator('#marketScope').evaluate("node=>Boolean(node.closest('#hanwooAdminDetails'))"),"public market chart must be outside admin details"
    assert not dpage.locator('#semenSalesScope').evaluate("node=>Boolean(node.closest('#hanwooAdminDetails'))"),"public semen chart must be outside admin details"
    assert dpage.locator('#hanwooAdminDetails').count()==1
    assert not dpage.locator('#hanwooAdminDetails').get_attribute('open'),"diagnostic info should be collapsed"
    desktop.close()
    forced=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    fpage=forced.new_page()
    fpage.goto(base+'/index.html?desktop=1',wait_until='domcontentloaded',timeout=30000)
    assert '/app.html' not in fpage.url
    forced.close()
   finally:browser.close()
 finally:server.shutdown();server.server_close()
 print('PASS: dedicated mobile native-style UI, 4 tabs, market/semen/quality interactions, 55 semen records, offline, desktop preserved')

if __name__=='__main__':run()
