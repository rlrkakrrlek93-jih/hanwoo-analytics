#!/usr/bin/env python3
"""Machine-readable health report for all independently updated HANWOO INSIGHT datasets."""
from __future__ import annotations
import json,os,tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent
SOURCE={
 "quality":("data.json","도체중·근내지방도·경락가격"),
 "grades":("grade_data.json","육질등급"),
 "ages":("age_data.json","평균 도축개월령"),
 "market":("market_supply_data.json","한우 사육두수·판정두수·경락가격"),
 "semen_association":("semen_sales_data.json","정액 판매량: 전국한우협회"),
 "semen_krei":("semen_sales_data.json","정액 판매량: KREI"),
 "beef":("beef_national_data.json","육우 거세우")
}
def now():return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST")
def main():
    data={}
    for key,(name,label) in SOURCE.items():
        path=ROOT/name
        result={"label":label,"filename":name,"collector_outcome":os.getenv("COLLECT_"+key.upper(),"unknown")}
        try:
            d=json.loads(path.read_text(encoding="utf8"))
            records=d.get("records",[])
            if not records or not isinstance(records,list):raise ValueError("No validated records")
            months=sorted(r["month"] for r in records if "month" in r)
            result.update(latest_published_month=months[-1],record_count=len(records),
                last_collected_at_kst=d.get("last_success_kst") or d.get("last_verified_kst") or None,
                state="check_failed" if result["collector_outcome"]=="failure" else "reported_data_preserved")
        except Exception as exc:
            result.update(state="invalid_or_missing",reason=str(exc)[:120])
        data[key]=result
    status_path=ROOT/"semen_krei_status.json"
    if status_path.exists():
        try:
            status=json.loads(status_path.read_text(encoding="utf8"))
            data["semen_krei"].update(krei_check_status=status.get("status"),
                krei_last_check_at=status.get("checked_at_kst"),
                krei_verified_issues=status.get("verified_issues",[]),
                krei_new_months=status.get("new_months",[]),
                krei_source_errors=status.get("source_errors",[]),
                krei_conflicts_preserved=status.get("conflicts_preserved",[]))
        except (ValueError,OSError):
            pass
    payload={"schema_version":1,"checked_at_kst":now(),"kind":"collector_run_status_not_official_release_time",
       "note":"수집 성공은 공식 데이터의 새 월 공개를 의미하지 않습니다. 갱신 월은 각 지표별 공표 시점에 따릅니다.",
       "datasets":data}
    fd,tmp=tempfile.mkstemp(dir=ROOT,prefix=".hanwoo_health_",suffix=".json")
    try:
        with os.fdopen(fd,"w",encoding="utf8") as f:
            json.dump(payload,f,ensure_ascii=False,indent=2);f.write("\n")
        os.replace(tmp,ROOT/"auto_update_status.json")
    finally:Path(tmp).unlink(missing_ok=True)
    print("HANWOO_DATA_HEALTH",json.dumps({k:(v["collector_outcome"],v.get("latest_published_month")) for k,v in data.items()},ensure_ascii=False))
    if any(x.get("state")=="invalid_or_missing" for x in data.values()):
        raise RuntimeError("At least one published dataset is missing/invalid; status JSON persisted")

if __name__=="__main__":main()
