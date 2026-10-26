#!/usr/bin/env python3
"""Read a publicly displayed Mtrace table using a browser; no secret API key.
Requires Playwright Chromium. Runs once per invocation. Data is verified before replacement.
"""
import argparse
import json
import os
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from update import ROOT, build, parse_saved_response

URL = 'https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2'


def collect(timeout_ms=45000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(locale='ko-KR', timezone_id='Asia/Seoul', viewport={'width':1440,'height':1000})
        responses = []
        def capture(response):
            if '/statHtml/html.do' not in response.url or response.request.method != 'POST' or response.status != 200:
                return
            try:
                obj = response.json()
                if isinstance(obj,dict) and isinstance(obj.get('result'), list) and obj['result'] and 'mainTable' in str(obj['result'][0]):
                    responses.append(obj)
            except Exception:
                pass
        page.on('response', capture)
        try:
            page.goto(URL, wait_until='domcontentloaded', timeout=timeout_ms)
            # The table may load automatically. Otherwise try the on-page search action.
            try:
                page.wait_for_timeout(8000)
                if not responses:
                    candidates = page.get_by_text('통계표조회', exact=True)
                    if candidates.count():
                        candidates.first.click(timeout=5000)
                        page.wait_for_timeout(8000)
            except Exception:
                pass
            if not responses:
                raise RuntimeError('공식 통계표 응답을 받지 못했습니다. 페이지 구조 또는 접근 정책을 확인하세요.')
            # The page may fetch multiple table layouts. Only accept a response
            # that matches the expected 8-item monthly table and has both sexes.
            failures=[]
            for obj in reversed(responses):
                with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',suffix='.json',delete=False) as f:
                    json.dump(obj,f,ensure_ascii=False)
                    candidate=Path(f.name)
                try:
                    parsed=parse_saved_response(candidate)
                    if len(parsed)>=2:
                        return obj
                except Exception as exc:
                    failures.append(str(exc))
                finally:
                    candidate.unlink(missing_ok=True)
            raise RuntimeError('조회 응답은 받았으나 필요한 표 형식과 일치하지 않습니다. '                               +' | '.join(failures[:2]))
        finally:
            browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from-response',help='저장된 공식 응답 JSON으로 오프라인 테스트')
    args = ap.parse_args()
    if args.from_response:
        raw = json.loads(Path(args.from_response).read_text(encoding='utf-8-sig'))
    else:
        raw = collect()
    # Save a new, non-sensitive response snapshot for troubleshooting.
    fd, tmp_path = tempfile.mkstemp(prefix='hanwoo_',suffix='.json')
    os.close(fd)
    try:
        Path(tmp_path).write_text(json.dumps(raw,ensure_ascii=False),encoding='utf-8')
        rows = build(tmp_path,ROOT/'dashboard_template.html',ROOT/'index.html')
        print(f'성공: {len(rows)}행 저장, 최신 월 {max(r["month"] for r in rows)}')
    finally:
        Path(tmp_path).unlink(missing_ok=True)

if __name__ == '__main__':
    main()
