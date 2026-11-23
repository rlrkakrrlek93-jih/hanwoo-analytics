#!/usr/bin/env python3
"""Live local-browser regression test for 2024/25/26 overlay without modifying site files."""
from __future__ import annotations

import contextlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

def test_page():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 960}, locale="ko-KR")
                page.goto(f"http://127.0.0.1:{server.server_port}/index.html",
                          wait_until="domcontentloaded", timeout=30000)
                svg = page.locator("#marketScope svg")
                svg.locator('path[data-year="2024"]').first.wait_for(timeout=18000)
                assert svg.locator("path[data-year]").count() == 9, "3 metrics x 3 yearly lines required"
                assert svg.locator('circle[data-metric="graded_head"]').count()==34
                assert svg.locator('circle[data-metric="auction_price"]').count()==34
                assert svg.locator('circle[data-metric="inventory_head"]').count() in (33,34), "One historical stock value may be quarantined pending official recheck"
                assert svg.locator('circle[data-year]').count() in (101,102)
                assert svg.locator('circle[data-year="2024"][data-metric="graded_head"]').count() == 12
                assert svg.locator('circle[data-year="2025"][data-metric="graded_head"]').count() == 12
                assert svg.locator('circle[data-year="2026"][data-metric="graded_head"]').count() == 10
                jan = [
                    svg.locator(f'circle[data-year="{y}"][data-month="1"][data-metric="inventory_head"]')
                    .get_attribute("cx")
                    for y in ("2024", "2025", "2026")
                ]
                assert len(set(jan)) == 1, "January points must share identical X position"
                months = page.locator("#marketScope svg text").all_text_contents()
                assert all(f"{i}월" in months for i in range(1, 13)), "Jan-Dec axis is not complete"
                first_title = svg.locator('circle[data-year="2024"][data-month="1"][data-metric="auction_price"] title').text_content()
                assert "17,609" in first_title and "원/kg" in first_title, "2024 Jan steer price mismatched"
                labels = svg.locator('text[data-value-label="true"]')
                assert labels.count() == svg.locator('circle[data-year]').count(), "Every displayed data point should have a matching value label"
                assert svg.locator('text[data-value-label="true"][data-year="2024"][data-month="1"][data-metric="inventory_head"]').text_content() == "335.8"
                assert svg.locator('text[data-value-label="true"][data-year="2024"][data-month="1"][data-metric="graded_head"]').text_content() == "123.6"
                assert svg.locator('text[data-value-label="true"][data-year="2024"][data-month="1"][data-metric="auction_price"]').text_content() == "17,609"
                assert svg.locator('text[data-value-label="true"][data-year="2026"][data-month="11"]').count() == 0
                assert page.locator('#marketScope .mk-value-toggle input').is_checked()
                panel = page.locator("#marketScope")
                output = ROOT / "test_artifacts"
                output.mkdir(exist_ok=True)
                panel.screenshot(path=str(output / "hanwoo_yearly_overlay.png"))
                page.locator('#marketScope select').select_option('female')
                cow_title = svg.locator('circle[data-year="2024"][data-month="1"][data-metric="auction_price"] title').text_content()
                assert "14,360" in cow_title, "Cow auction price selector is not changing the plot"
                assert svg.locator('text[data-value-label="true"][data-year="2024"][data-month="1"][data-metric="auction_price"]').text_content() == "14,360"
                page.locator('#marketScope .mk-year input[value="2025"]').uncheck()
                assert svg.locator("path[data-year]").count() == 6, "Year toggle should hide 2025 plots"
                assert svg.locator("path[data-year='2025']").count() == 0
                assert labels.count() == 66, "Hiding one complete year should hide its numeric labels"
                page.locator('#marketScope .mk-value-toggle input').uncheck()
                assert labels.count() == 0, "Label checkbox should hide numbers without hiding curves"
                assert svg.locator('path[data-year]').count() == 6
                page.locator('#marketScope .mk-value-toggle input').check()
                assert labels.count() == 66
                assert svg.locator("circle[data-year='2026'][data-month='11']").count() == 0
                assert svg.locator("circle[data-year='2026'][data-month='12']").count() == 0
                quality = page.locator("#maleChart")
                quality.locator('[data-quality-value="true"]').first.wait_for(timeout=7000)
                assert quality.locator('text[data-quality-value="true"]').count() == quality.locator("circle").count()
                assert page.locator("#femaleChart text[data-quality-value='true']").count() == page.locator("#femaleChart circle").count()
                assert quality.locator('text[data-quality-value="true"]').first.text_content().strip()
                metric_button=page.get_by_role("button",name="경락단가",exact=True)
                metric_button.click()
                assert quality.locator('text[data-quality-value="true"][data-metric="price"]').count()>0
                assert quality.locator('text[data-quality-value="true"][data-metric="price"]').first.text_content().strip().replace(',','').isdigit()
                grade=page.locator('#gradeMale')
                grade.locator('small').first.wait_for(timeout=8000)
                assert grade.locator('small').count()==5, "Each grade bar should show its official headcount"
                assert all('두' in x for x in grade.locator('small').all_text_contents())
                print("PASS: market, quality trend and grade-bar numeric labels, filters and source counts")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    test_page()
