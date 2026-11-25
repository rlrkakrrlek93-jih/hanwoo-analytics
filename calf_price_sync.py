#!/usr/bin/env python3
"""Archive confirmed nationwide calf market prices from official eKAPEpia.
The source is the NongHyup livestock auction price survey published via KAPE:
Hanwoo male/female calves aged 6-7 months, KRW 1,000 per head.
Do not invent regional values or zero-fill days without livestock auctions.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "calf_price_data.json"
URL = "https://www.ekapepia.com/v3/price/livestock/cow/producer.do"
KST = dt.timezone(dt.timedelta(hours=9))

def as_price(text: str):
    # Cell labels sometimes include an icon's change count; use the first numeric token.
    raw = re.sub(r"\s+", " ", text).strip().replace("\xa0", " ")
    parts = re.findall(r"(?<![\d.])(?:\d{1,3}(?:,\d{3})+|\d{4,5})(?![\d.])", raw)
    if not parts:
        return None
    result = int(parts[0].replace(",", ""))
    return result if 500 <= result <= 15000 else None

def normalize_label(t: str):
    return re.sub(r"\s+", "", t)

def table_rows(html: str):
    soup=BeautifulSoup(html, "html.parser")
    for row in soup.select("tr"):
        cells=row.find_all(["td","th"],recursive=False)
        if len(cells)<6:continue
        label=normalize_label(cells[0].get_text(" ",strip=True))
        if not any(word in label for word in ("금일","전월평균","전일")):
            continue
        vals=[as_price(cell.get_text(" ",strip=True)) for cell in cells[1:]]
        # Producer page column ordering: large cow, female 4-5m, male 4-5m,
        # female 6-7m, male 6-7m, beef cattle and older cattle columns...
        if len(vals)<5:continue
        female,male=vals[3],vals[4]
        if female is None or male is None:continue
        if not 1000<=female<=9000 or not 1500<=male<=12000:
            continue
        yield label,male,female

def extract(html: str,year: int):
    report = None
    monthly = None
    for label,male,female in table_rows(html):
        daymatch=re.search(r"(\d{1,2})월(\d{1,2})일",label)
        if "금일" in label and daymatch:
            date=dt.date(year,int(daymatch.group(1)),int(daymatch.group(2)))
            # Year rollover: page might show late December while current date is January.
            today=dt.datetime.now(KST).date()
            if date>today+dt.timedelta(days=1):
                date=date.replace(year=year-1)
            if (today-date).days<0 or (today-date).days>40:
                raise ValueError("Published price date not within 40-day freshness window")
            report={"date":date.isoformat(),"region":"전국","male_6_7":male,"female_6_7":female}
        elif "전월평균" in label:
            match=re.search(r"(\d{2,4})년(\d{1,2})월",label)
            if match:
                y=int(match.group(1))
                if y<100:y+=2000
                month=f"{y:04d}-{int(match.group(2)):02d}"
                monthly={"month":month,"region":"전국","male_6_7":male,"female_6_7":female}
    return report,monthly

def download():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            page=browser.new_page(locale="ko-KR",timezone_id="Asia/Seoul")
            page.goto(URL,wait_until="domcontentloaded",timeout=60000)
            # Data is sometimes rendered asynchronously on the official page.
            page.wait_for_timeout(4500)
            html=page.content()
            return extract(html,dt.datetime.now(KST).year)
        finally:
            browser.close()

def main():
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--html",help="Use saved official HTML to test parser without network")
    opts=a.parse_args()
    report,month=extract(Path(opts.html).read_text(encoding="utf8"),dt.datetime.now(KST).year) if opts.html else download()
    if report is None:
        raise ValueError("Official calf prices not parsed; existing published observations left untouched")
    old=json.loads(DATA.read_text(encoding="utf8"))
    records={r["date"]:r for r in old["records"] if r.get("region")=="전국"}
    references={r["month"]:r for r in old.get("monthly_reference",[]) if r.get("region")=="전국"}
    records[report["date"]]=report
    if month:references[month["month"]]=month
    old["records"]=[records[k] for k in sorted(records)]
    old["monthly_reference"]=[references[k] for k in sorted(references)]
    old["last_verified_date"]=max(records)
    old["last_success_kst"]=dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    # Region records must only be sourced and independently validated by a regional survey.
    # Smart auctions currently cover a non-representative subset; never synthesize averages.
    fd,tmp=tempfile.mkstemp(prefix=".calf_price_",suffix=".json",dir=ROOT)
    try:
        with os.fdopen(fd,"w",encoding="utf8") as f:
            json.dump(old,f,ensure_ascii=False,indent=2)
            f.write("\n")
        os.replace(tmp,DATA)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print("Verified official nationwide 6-7-month calf auction prices:",report)
    if month:print("Previous official monthly mean:",month)
    print("Archived confirmed days:",len(records))

if __name__=="__main__":
    main()
