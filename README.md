# 한우 통계 신뢰성 및 확장 v5

기존 디자인은 변경하지 않았습니다. 기존 GitHub 저장소의 `dashboard_template.html`, `update.py`, `collect.py`, `requirements.txt`, `data.csv`, `data.json`, `index.html`을 새 파일로 교체하세요. **`debug_response.json`이나 쿠키는 공개 저장소에 올리지 마세요.**

- 데이터 출처: 축산물품질평가원 축산유통 통계누리 (표 ID DT_323903_E1080008)
- 업데이트 성공 시 홈페이지에 **마지막 수집 성공 시각(한국시간)**, **최신 수록 월**, **검증 상태**를 표시합니다.
- **공식 통계 갱신일**은 현재 수집 응답에서 확인되지 않으므로 '원본 메타데이터 미확인'이라고 표시합니다. 수집 성공시각과 공식 통계 발표시각을 혼동하지 않습니다.
- **등급 1++·1+·1·2·3별 출현율** 및 **출하월령**은 아직 확보되지 않아 빈 자료 영역만 제공합니다. 추가 통계표를 찾으면 같은 전국·한우·성별·월 기준으로 별도 검증 후 연결해야 합니다.
- 누적 평균은 월별 공표 반올림값을 판정두수로 가중한 근사치입니다. 경락단가 가중치의 적절성도 공식 메타데이터와 대조해야 합니다.
- 기존 GitHub Actions 예약 자동화는 그대로 유지합니다. `.github/workflows/update.yml`은 바꾸지 않아도 됩니다.
- 오프라인 검증: `python3 collect.py --from-response debug_response.json` (공개 업로드 금지).
- 작업 파일 업로드 후 GitHub → Actions → Hanwoo Daily Update → Run workflow 로 테스트하세요.
