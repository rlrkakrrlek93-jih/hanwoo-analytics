#!/usr/bin/env python3
"""Read-only inspection of precision in public KAPE/Mtrace statistics.

DOES NOT modify index.html, data.json, data.csv or any production file.
Responses are diagnostic evidence, not permission to replace statistics.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

SOURCES = {
    "current_E1080008": "https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2",
    "candidate_APGS_011": "https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_APGS_011&conn_path=I2",
}
NUMBER = re.compile(r"^-?\d[\d,]*(?:\.\d+)?$")

def summarize_table(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("#mainTable")
    if table is None:
        raise ValueError("mainTable missing from official HTML payload")
    head = [
        [{"text": c.get_text(" ", strip=True)[:80], "name": c.get("name", ""), "colspan": c.get("colspan", "1")}
         for c in tr.find_all(["th", "td"], recursive=False)][:40]
        for tr in table.select("thead tr")[:4]
    ]
    rows, decimal_samples, integer_samples = [], [], []
    numeric_count = 0
    for i, tr in enumerate(table.select("tbody tr")):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"], recursive=False)]
        if i < 18:
            rows.append({"row_number": i, "labels": cells[:4], "numeric_sample": cells[4:16]})
        for j, raw in enumerate(cells):
            normalized = raw.replace(" ", "")
            if not NUMBER.fullmatch(normalized):
                continue
            numeric_count += 1
            sample = {"row": i, "column": j, "value": normalized}
            if "." in normalized and re.search(r"\.[0-9]*[1-9]", normalized):
                if len(decimal_samples) < 20:
                    decimal_samples.append(sample)
            elif len(integer_samples) < 10:
                integer_samples.append(sample)
    return {
        "data_row_count": len(table.select("tbody tr")),
        "numeric_cell_count": numeric_count,
        "nonzero_decimal_samples": decimal_samples,
        "integer_or_zero_decimal_samples": integer_samples,
        "header_sample": head,
        "row_sample": rows,
        "warning": "Decimal cells alone do not establish which metric or population they belong to.",
    }

def capture_page(browser, identifier: str, url: str, out_dir: Path) -> dict:
    page = browser.new_page(locale="ko-KR", timezone_id="Asia/Seoul",
                            viewport={"width": 1440, "height": 1000})
    responses, failures = [], []
    def capture(resp):
        try:
            if "/statHtml/html.do" not in resp.url or resp.request.method != "POST" or resp.status != 200:
                return
            obj = resp.json()
            result = obj.get("result") if isinstance(obj, dict) else None
            if isinstance(result, list) and result and isinstance(result[0], str) and "mainTable" in result[0]:
                responses.append(obj)
        except Exception as exc:
            failures.append(str(exc)[:120])
    page.on("response", capture)
    result = {"source": identifier, "url": url, "captured": False}
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(8500)
        if not responses:
            candidates = page.get_by_text("통계표조회", exact=True)
            if candidates.count():
                candidates.first.click(timeout=6000)
                page.wait_for_timeout(8500)
        if not responses:
            result["error"] = "No parseable public mainTable response captured"
        else:
            payload = responses[-1]
            result.update({"captured": True, "responses_count": len(responses),
                           "table": summarize_table(payload["result"][0])})
            (out_dir / f"{identifier}_raw_response.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
    finally:
        if failures:
            result["capture_errors"] = failures[:3]
        page.close()
    return result

def main() -> None:
    ap = argparse.ArgumentParser(description="Read-only public-source precision audit")
    ap.add_argument("--output-dir", default="precision_probe_result")
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "checked_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST"),
        "status": "diagnostic_only_no_published_data_changed",
        "sources": [],
        "guardrail": "Do not replace production values until month, breed, sex, geography, counts, units and rounded measures agree.",
    }
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                for identifier, url in SOURCES.items():
                    report["sources"].append(capture_page(browser, identifier, url, out_dir))
            finally:
                browser.close()
    except Exception as exc:
        report["runtime_error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
    (out_dir / "precision_probe_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": report["status"],
        "sources": [{"id": x["source"], "captured": x["captured"], "error": x.get("error")}
                    for x in report["sources"]]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
