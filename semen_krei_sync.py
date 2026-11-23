#!/usr/bin/env python3
"""Automatically backfill official KREI Hanwoo semen sales from image-based outlook PDFs.

Scope: read-only official www.aglook.kr quarterly report PDFs. Never infer
unpublished months, mix regional series, overwrite conflicting values, or
interpret sales as completed inseminations.

KREI tables are image-only. OCR is a last-resort parser with strict
cross-report month controls, geometry, confidence, contiguous-month and
published-total checks. On any uncertainty the historical JSON stays intact.
"""
from __future__ import annotations
import argparse,datetime,json,os,re,statistics,tempfile
from pathlib import Path
from urllib.parse import urljoin,urlparse
from zoneinfo import ZoneInfo
import fitz
from PIL import Image
import pytesseract
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
DEST=ROOT/"semen_sales_data.json"
STATUS=ROOT/"semen_krei_status.json"
INDEX="https://www.aglook.kr/main/uObserveMonth/OVR0000000015"
UA={"User-Agent":"Mozilla/5.0 (compatible; HANWOO-INSIGHT verified public statistics)"}
REFERENCE_2025=[139.1,142.9,117.7,139.6,178.7,157.6,166.3,218.7,223.4,195.0,221.0,196.1]
REFERENCE_2024=[127.7,206.1,140.1,161.9,193.0,194.9,187.9,168.2,179.6,164.6,132.6,161.4]

def now():
    return datetime.datetime.now(ZoneInfo("Asia/Seoul"))

def atomic_json(path,content):
    fd,tmp=tempfile.mkstemp(dir=ROOT,prefix=".hanwoo_verified_",suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf8") as handle:
            json.dump(content,handle,ensure_ascii=False,indent=2)
            handle.write("\n")
        os.replace(tmp,path)
    finally:
        Path(tmp).unlink(missing_ok=True)

def discover(session,current_year=None):
    """Find current and previous year's real official PDFs on KREI's published index."""
    year=current_year or now().year
    found={}
    for y in (year,year-1):
        response=session.get(INDEX,params={"queryType":str(y)},headers=UA,timeout=30)
        response.raise_for_status()
        soup=BeautifulSoup(response.text,"html.parser")
        for row in soup.select(".table-row-group .table-row"):
            title=row.get_text(" ",strip=True)
            match=re.search(r"한육우\s+(20\d{2})년\s*(\d{1,2})월호",title)
            if not match:continue
            issue=f"{int(match.group(1)):04d}-{int(match.group(2)):02d}"
            anchor=row.select_one("a[href*='/ORGTEXT_FILE']")
            if not anchor:continue
            url=urljoin(response.url,anchor["href"])
            parts=urlparse(url)
            if parts.netloc not in ("www.aglook.kr","aglook.kr") or not parts.path.startswith("/main/uObserveMonth/OVR0000000015/download/"):
                continue
            found[issue]=url
    return sorted(found.items(),reverse=True)

def known_value(existing,year,month):
    if year==2025:return REFERENCE_2025[month-1]
    if year==2024:return REFERENCE_2024[month-1]
    record=next((r for r in existing.get("records",[]) if r.get("month")==f"{year}-{month:02d}" and "KREI" in r.get("source_name","")),None)
    return float(record["sold_thousand_str"]) if record else None

def ocr_tokens(page):
    zoom=2.4
    pix=page.get_pixmap(matrix=fitz.Matrix(zoom,zoom),alpha=False)
    img=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
    # The only table read is in the upper-middle part of a published outlook page.
    box=(int(pix.width*.07),int(pix.height*.23),int(pix.width*.94),int(pix.height*.48))
    region=img.crop(box)
    data=pytesseract.image_to_data(region,lang="eng",
        config="--psm 11 -c tessedit_char_whitelist=0123456789.,",
        output_type=pytesseract.Output.DICT)
    tokens=[]
    for i,raw in enumerate(data["text"]):
        word=raw.strip()
        if word:
            tokens.append(dict(word=word,x=data["left"][i]+box[0],
                 y=data["top"][i]+box[1],confidence=float(data["conf"][i])))
    return pix.width,tokens

def read_table_on_page(page,existing):
    width,tokens=ocr_tokens(page)
    year_rows={}
    for t in tokens:
        digits=re.sub(r"\D","",t["word"])
        if t["x"]<width*.16 and re.match(r"20(?:2\d|3\d)",digits):
            year=int(digits[:4])
            year_rows[year]=t["y"]
    if len(year_rows)<3:return None
    decimal=re.compile(r"\d{2,3}\.\d")
    # Calibrate twelve month positions against any complete historic table row.
    calibration=[]
    for year,y0 in year_rows.items():
        row=sorted((t for t in tokens if abs(t["y"]-y0)<12 and
            width*.155<t["x"]<width*.86 and decimal.fullmatch(t["word"])),
            key=lambda t:t["x"])
        if len(row)==12:
            diffs=[row[i+1]["x"]-row[i]["x"] for i in range(11)]
            step=statistics.median(diffs)
            if width*.045<step<width*.09 and max(abs(d-step) for d in diffs)<step*.22:
                known=sum(known_value(existing,year,i+1) is not None and
                    abs(float(t["word"])-known_value(existing,year,i+1))<=.11 for i,t in enumerate(row))
                calibration.append((known,year,row[0]["x"],step))
    if not calibration:return None
    matches,control_year,x_first,step=max(calibration)
    if matches<6:return None  # no independently known official control row
    # Confirm ALL recognizable reference cells, never trust a partial accidental match.
    control_values=[]
    for month in range(1,13):
        val=known_value(existing,control_year,month)
        if val is not None:control_values.append(val)
    if not control_values:return None
    rows={}
    for year,y0 in year_rows.items():
        cells={}
        total=None
        for t in tokens:
            if abs(t["y"]-y0)>12:continue
            if t["x"]>width*.86 and re.fullmatch(r"[\d,]+",t["word"]):
                total=int(t["word"].replace(",",""))
            if not(width*.155<t["x"]<width*.86 and decimal.fullmatch(t["word"])):
                continue
            month=round((t["x"]-x_first)/step)+1
            if not(1<=month<=12 and abs(t["x"]-x_first-(month-1)*step)<=step*.3):
                continue
            if month in cells:return None
            cells[month]=(float(t["word"]),t["confidence"])
        # Rows must contain January through last disclosed month without gaps.
        ordered=list(range(1,len(cells)+1))
        if not cells or sorted(cells)!=ordered:continue
        if any(not 25<=cells[m][0]<=400 or cells[m][1]<72 for m in ordered):
            continue
        nums=[cells[m][0] for m in ordered]
        if total is None or abs(sum(nums)-total)>2.5:continue
        rows[year]=nums
    if control_year not in rows:return None
    # Full independent comparison of the known control row.
    checks=0
    for month,val in enumerate(rows[control_year],1):
        prior=known_value(existing,control_year,month)
        if prior is None:continue
        if abs(val-prior)>.11:return None
        checks+=1
    if checks<6:return None
    return rows

def extract_pdf(blob,existing):
    if not blob.startswith(b"%PDF") or len(blob)>25_000_000:
        raise ValueError("Not a bounded official PDF")
    doc=fitz.open(stream=blob,filetype="pdf")
    if not 3<=len(doc)<=40:raise ValueError("Unexpected PDF pages")
    candidates=[]
    for ix in range(1,min(6,len(doc))):
        found=read_table_on_page(doc[ix],existing)
        if found:
            candidates.append((len(found),found,ix+1))
    if not candidates:raise ValueError("No OCR table passed independent official controls")
    _,rows,page=max(candidates,key=lambda a:a[0])
    return rows,page

def merge(previous,candidates):
    old={r["month"]:r for r in previous.get("records",[])}
    last_closed=now().year*12+now().month-2
    new=[]
    conflicts=[]
    for issue,url,rows in candidates:
        for year,vals in rows.items():
            if year<2025:continue
            for i,value in enumerate(vals):
                if year*12+i>last_closed:continue
                month=f"{year}-{i+1:02d}"
                prior=old.get(month)
                if prior is not None:
                    if abs(float(prior["sold_thousand_str"])-value)>.11 and "KREI" in prior.get("source_name",""):
                        conflicts.append({"month":month,"saved":prior["sold_thousand_str"],"new":value,"report":issue})
                    continue
                old[month]={"month":month,"sold_thousand_str":value,"source_url":url,
                  "source_name":f"한국농촌경제연구원(KREI) {issue[:4]}년 {int(issue[5:])}월 한육우 축산관측",
                  "source_unit":"천 스트로 (소수 첫째 자리)",
                  "source_type":"국책연구기관 공표 / 원자료 농협중앙회 가축개량원"}
                new.append(month)
    records=[old[k] for k in sorted(old)]
    if len(records)!=len({r["month"] for r in records}):raise ValueError("Duplicate month detected")
    if any(not 25<=float(r["sold_thousand_str"])<=400 for r in records):raise ValueError("Value range")
    return records,sorted(new),conflicts

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--dry-run",action="store_true")
    arg.add_argument("--self-check",action="store_true",help="Validate seeded 2026 KREI documents, no data writes")
    args=arg.parse_args()
    previous=json.loads(DEST.read_text(encoding="utf8"))
    s=requests.Session()
    if args.self_check:
        for issue,url,month in [
            ("2026-03","https://www.aglook.kr/upload/observeFiles/cb83caf9fe9648a58f43611e1d0c06b3.pdf","2026-02"),
            ("2026-09","https://www.aglook.kr/main/uObserveMonth/OVR0000000015/download/8752/ORGTEXT_FILE","2026-07")
        ]:
            response=s.get(url,headers=UA,timeout=45);response.raise_for_status()
            parsed,page=extract_pdf(response.content,previous)
            assert abs(parsed[2026][1]-201.8)<.01 and (issue!="2026-09" or abs(parsed[2026][6]-171.3)<.01)
            print("KREI_OCR_SELF_CHECK",issue,"PASS","page",page,"months",len(parsed[2026]))
        return
    reports=[]
    errors=[]
    try:
        discovery=discover(s)
    except Exception as exc:
        discovery=[];errors.append("KREI publication index: "+str(exc)[:160])
    for issue,url in discovery[:4]:
        try:
            response=s.get(url,headers=UA,timeout=45);response.raise_for_status()
            rows,page=extract_pdf(response.content,previous)
            print("KREI_REPORT_VERIFIED",issue,"table page",page,"years",dict((k,len(v)) for k,v in rows.items()))
            reports.append((issue,url,rows))
        except Exception as exc:
            errors.append(issue+" OCR rejection: "+str(exc)[:140])
    # Latest report goes first; preserve newer source link.
    records,added,conflicts=merge(previous,reports)
    status={"checked_at_kst":now().strftime("%Y-%m-%d %H:%M KST"),
      "status":"updated" if added else ("verified_no_new_months" if reports else "source_unverifiable"),
      "last_verified_month":records[-1]["month"],"new_months":added,
      "verified_issues":[r[0] for r in reports],"source_errors":errors[:8],
      "conflicts_preserved":conflicts[:12],
      "method":"KREI official image-PDF OCR with strict historical control and published total verification"}
    print("KREI_SEMEN_RESULT",json.dumps(status,ensure_ascii=False))
    if args.dry_run:return
    if added:
        atomic_json(DEST,{**previous,"records":records,
          "coverage":f"{records[0]['month']} ~ {records[-1]['month']} (공식 확인된 월만)",
          "last_verified_kst":status["checked_at_kst"]})
    atomic_json(STATUS,status)
    if not reports:raise RuntimeError("No verified official KREI monthly semen table; old data preserved")

if __name__=="__main__":main()
