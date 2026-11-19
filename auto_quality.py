#!/usr/bin/env python3
"""HANWOO INSIGHT safe collection gate.

Keeps current website/files on failed or ambiguous official collection.
Requires the existing collect.py and update.py; does NOT replace either.
Writes quality_report.json with explicit scope of the official recheck.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import collect
import update

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data.json'
INDEX = ROOT / 'index.html'
CSV = ROOT / 'data.csv'
REPORT = ROOT / 'quality_report.json'
TRACKED = (DATA, INDEX, CSV)
FIELDS = ('count', 'weight', 'marbling', 'rea', 'fat', 'live', 'price')
SEXES = ('거세우', '암소')
OFFICIAL_URL = update.SOURCE
MONTH_RE = re.compile(r'^20\d\d-(0[1-9]|1[0-2])$')
MAX_ATTEMPTS = 3


def now_kst():
    return datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M KST')


def month_index(month):
    y, m = map(int, month.split('-'))
    return y * 12 + m


def last_complete_month():
    t = datetime.now(ZoneInfo('Asia/Seoul'))
    y, m = t.year, t.month - 1
    if not m:
        y, m = y - 1, 12
    return f'{y:04d}-{m:02d}'


def numeric(value):
    # reject bools, nonfinite numbers and text masquerading as a statistic
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def row_errors(r):
    if not isinstance(r, dict):
        return ['레코드가 객체가 아닙니다']
    out = []
    if not MONTH_RE.fullmatch(str(r.get('month', ''))):
        out.append('월 형식 오류')
    if r.get('sex') not in SEXES:
        out.append('성별 오류')
    ranges = {
        'count': (1, 1000000), 'weight': (150, 800),
        'marbling': (1, 9), 'rea': (30, 250),
        'fat': (0, 70), 'live': (250, 1600), 'price': (1000, 100000),
    }
    for f, (low, high) in ranges.items():
        v = r.get(f)
        if not numeric(v) or not low <= v <= high:
            out.append(f'{f} 비정상')
        if f == 'count' and numeric(v) and int(v) != v:
            out.append('count 정수 아님')
    return out


def validate(rows, *, enforce_contiguous=True, enforce_published=True):
    if not isinstance(rows, list) or not rows:
        raise ValueError('records 배열이 비어 있습니다')
    seen = set()
    months = {}
    for r in rows:
        problems = row_errors(r)
        if problems:
            raise ValueError(f'{r.get("month", "?") if isinstance(r, dict) else "?"} / '
                             f'{r.get("sex", "?") if isinstance(r, dict) else "?"}: {", ".join(problems)}')
        key = (r['month'], r['sex'])
        if key in seen:
            raise ValueError('월·성별 중복: ' + str(key))
        seen.add(key)
        months.setdefault(r['month'], set()).add(r['sex'])
        if enforce_published and r['month'] > last_complete_month():
            raise ValueError('아직 종료되지 않은 월 데이터: ' + r['month'])
    if any(sexes != set(SEXES) for sexes in months.values()):
        raise ValueError('월별 거세우/암소 자료가 모두 있어야 합니다')
    ordered = sorted(months)
    if enforce_contiguous and ordered and month_index(ordered[-1]) - month_index(ordered[0]) + 1 != len(ordered):
        raise ValueError('중간 월 데이터 누락')
    return { (r['month'], r['sex']): r for r in rows }


def parse_capture(capture):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as f:
        json.dump(capture, f, ensure_ascii=False)
        path = Path(f.name)
    try:
        rows = update.parse_saved_response(path)
    finally:
        path.unlink(missing_ok=True)
    validate(rows, enforce_contiguous=False)
    return rows


def digest_by_key(rows):
    return { (r['month'], r['sex']): tuple(r[x] for x in FIELDS) for r in rows }


def snapshot():
    return {p: p.read_bytes() if p.exists() else None for p in TRACKED}


def restore(saved):
    for path, data in saved.items():
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(data)


def write_json_atomic(path, payload):
    fd, filename = tempfile.mkstemp(prefix='.hanwoo_', suffix='.json', dir=ROOT)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(filename, path)
    finally:
        Path(filename).unlink(missing_ok=True)


def load_previous():
    if not DATA.exists():
        return []
    obj = json.loads(DATA.read_text(encoding='utf-8'))
    rows = obj.get('records')
    if not isinstance(rows, list):
        raise ValueError('기존 data.json에 records 배열이 없습니다')
    return rows


def salvage_previous(previous, new):
    """Auto-repair only when a fresh official response covers invalid keys."""
    official = {(r['month'], r['sex']): r for r in new}
    good, invalid = [], []
    for r in previous:
        if not isinstance(r, dict) or not isinstance(r.get('month'), str) or r.get('sex') not in SEXES:
            raise ValueError('기존 데이터에 식별 불가능한 행이 있어 자동 복구할 수 없습니다')
        if row_errors(r):
            invalid.append((r['month'], r['sex']))
        else:
            good.append(r)
    if any(k not in official for k in invalid):
        raise ValueError('오류 행에 해당하는 공식 원본이 없어 자동 수정하지 않습니다: ' + str(invalid[:3]))
    # A complete month must be available for an invalid monthly row.
    for month, _ in invalid:
        if not all((month, s) in official for s in SEXES):
            raise ValueError('공식 원본에서 누락된 성별이 있어 복구를 보류합니다: ' + month)
    # A duplicate pair is not auto-resolved unless freshly sourced.
    counts = {}
    for r in good:
        k = (r['month'], r['sex'])
        counts[k] = counts.get(k, 0) + 1
    duplicates = [k for k, n in counts.items() if n > 1]
    if any(k not in official for k in duplicates):
        raise ValueError('중복 데이터에 대한 공식 원본을 확보하지 못했습니다')
    return list({(r['month'], r['sex']): r for r in good}.values()), invalid, duplicates


def verify_published(official_rows, old_rows):
    obj = json.loads(DATA.read_text(encoding='utf-8'))
    published = obj.get('records')
    official = validate(official_rows, enforce_contiguous=False)
    combined = validate(published)
    for k, r in official.items():
        if k not in combined or any(combined[k][f] != r[f] for f in FIELDS):
            raise ValueError('공식 응답과 저장된 자료가 다릅니다: ' + str(k))
    old_keys = {(r['month'], r['sex']) for r in old_rows}
    if not old_keys.issubset(combined):
        raise ValueError('기존 월별 데이터가 삭제되었습니다')
    latest = max(k[0] for k in combined)
    if obj.get('latest_month') != latest:
        raise ValueError('최신 월 메타데이터 불일치')
    html = INDEX.read_text(encoding='utf-8')
    match = re.search(r'const DATA=(\[.*?\]);\s*const METRICS=', html, re.S)
    if not match:
        raise ValueError('생성된 index.html에 DATA 배열이 없습니다')
    embedded = json.loads(match.group(1))
    if digest_by_key(embedded) != digest_by_key(published):
        raise ValueError('화면 내부 데이터와 data.json이 불일치합니다')
    with CSV.open(encoding='utf-8-sig', newline='') as fp:
        csv_rows = list(csv.DictReader(fp))
    if len(csv_rows) != len(published):
        raise ValueError('CSV 행 수가 data.json과 다릅니다')
    return latest, len(published)


def run():
    prev_bytes = snapshot()
    report = {
        'schema_version': 1, 'checked_at_kst': now_kst(),
        'source_table_id': 'DT_323903_E1080008',
        'official_source_url': OFFICIAL_URL,
        'status': 'unverified', 'message': '',
        'scope': '최근 공식 응답에 포함된 월만 재검증하며 전체 과거 기록의 독립 검증은 아닙니다.',
        'verified_months': [], 'corrections': [], 'attempts': 0,
    }
    try:
        previous = load_previous()
        response = None
        rows = None
        failures = []
        for attempt in range(1, MAX_ATTEMPTS + 1):
            report['attempts'] = attempt
            try:
                response = collect.collect()
                rows = parse_capture(response)
                break
            except Exception as exc:
                failures.append(f'{attempt}차 실패: {exc}')
                if attempt < MAX_ATTEMPTS:
                    time.sleep(5 * attempt)
        if response is None or rows is None:
            raise RuntimeError('공식 수집 재시도 실패: ' + ' | '.join(failures))

        # Confirm new/revised records with a second official read, not a guess.
        new_map = digest_by_key(rows)
        previous_ok = [r for r in previous if isinstance(r, dict) and not row_errors(r)]
        old_map = digest_by_key(previous_ok)
        changed = [k for k, v in new_map.items() if old_map.get(k) != v]
        if changed:
            response2 = collect.collect()
            rows2 = parse_capture(response2)
            second_map = digest_by_key(rows2)
            if any(second_map.get(k) != new_map[k] for k in changed):
                raise ValueError('2회 공식 수집 결과가 일치하지 않아 자동 변경을 보류합니다')
            response, rows = response2, rows2
            new_map = second_map

        good_previous, invalid, duplicates = salvage_previous(previous, rows)
        if invalid or duplicates:
            prior_obj = json.loads(DATA.read_text(encoding='utf-8'))
            prior_obj['records'] = good_previous
            write_json_atomic(DATA, prior_obj)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as f:
            json.dump(response, f, ensure_ascii=False)
            raw_path = Path(f.name)
        try:
            update.build(raw_path, ROOT / 'dashboard_template.html', INDEX)
        finally:
            raw_path.unlink(missing_ok=True)
        latest, count = verify_published(rows, previous)
        report.update({
            'status': 'verified_current_source',
            'message': '공식 통계 응답을 수집·검증하고 기존 자료를 보존한 채 반영했습니다.',
            'latest_month': latest, 'published_rows': count,
            'verified_months': sorted({r['month'] for r in rows}),
            'corrections': [
                {'month': k[0], 'sex': k[1], 'kind': '신규 또는 공식 자료 변경'}
                for k in changed
            ],
            'repaired_invalid_records': len(invalid) + len(duplicates),
        })
        print(f'[HANWOO 품질검사 통과] {latest}, {count}행, 수집 변경 {len(changed)}개')
    except Exception as exc:
        restore(prev_bytes)
        report.update({
            'status': 'blocked_kept_previous',
            'message': '검증에 실패하여 기존 홈페이지와 데이터 파일을 보존했습니다: ' + str(exc)[:800],
            'latest_month': None,
        })
        print('[HANWOO 품질검사 보류] 기존 데이터 보존: ' + str(exc))
    finally:
        write_json_atomic(REPORT, report)
    # Exit 0: let the other independent workflows continue, and publish the report.
    # The update step commits data only if the protective checks completed.
    return report


if __name__ == '__main__':
    run()
