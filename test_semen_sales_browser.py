#!/usr/bin/env python3
"""Chromium regression: official straw-sales comparison and honest source gaps."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
            try:
                page=browser.new_page(locale="ko-KR",viewport={"width":1440,"height":1100})
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.goto(f"http://127.0.0.1:{server.server_port}/index.html",wait_until="domcontentloaded",timeout=30000)
                scope=page.locator("#semenSalesScope")
                scope.locator('circle[data-year="2024"]').first.wait_for(timeout=20000)
                svg=scope.locator("svg")
                assert scope.count()==1
                assert svg.locator('circle[data-year="2024"]').count()==12
                assert svg.locator('circle[data-year="2025"]').count()==5
                assert svg.locator('circle[data-year="2026"]').count()==0
                assert svg.locator('path[data-year="2024"]').count()==1
                assert svg.locator('path[data-year="2025"]').count()==1
                assert svg.locator('path[data-year="2026"]').count()==0
                assert svg.locator('path[data-year="2024"]').get_attribute("d").startswith("M")
                assert svg.locator('path[data-year="2025"]').get_attribute("d").startswith("M")
                jan24=svg.locator('circle[data-year="2024"][data-month="1"]').get_attribute("cx")
                jan25=svg.locator('circle[data-year="2025"][data-month="1"]').get_attribute("cx")
                assert jan24==jan25
                labels=svg.locator("text").all_text_contents()
                assert all(f"{i}월" in labels for i in range(1,13))
                assert "128천 str" in svg.locator('circle[data-year="2024"][data-month="1"] title').text_content()
                assert "139천 str" in svg.locator('circle[data-year="2025"][data-month="1"] title').text_content()
                assert "2025년 6월 이후" in scope.inner_text()
                folder=ROOT/"test_artifacts"
                folder.mkdir(exist_ok=True)
                scope.screenshot(path=str(folder/"semen_sales_annual_compare.png"))
                scope.locator("input").nth(0).uncheck()
                assert svg.locator('path[data-year="2024"]').count()==0
                assert svg.locator('path[data-year="2025"]').count()==1
                assert not errors, errors[:3]
                print("PASS: semen Jan-Dec year overlay, 17 confirmed months, unpublished months hidden")
            finally:browser.close()
    finally:server.shutdown();server.server_close()
if __name__=="__main__":
    main()
