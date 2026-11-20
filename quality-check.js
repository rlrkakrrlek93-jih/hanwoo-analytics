/* HANWOO INSIGHT v1.4 — read-only data quality panel.
 * Displays results from auto_quality.py; never changes any statistic.
 */
(()=>{'use strict';
 const OFFICIAL='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2';
 const METRIC={count:'판정두수',weight:'평균 도체중',marbling:'근내지방도',rea:'등심단면적',fat:'등지방두께',live:'평균 생체중',price:'경락단가'};
 const LIMITS={count:0.30,weight:0.05,marbling:0.20,rea:0.10,fat:0.25,live:0.10,price:0.15};
 const $=id=>document.getElementById(id);
 const el=(tag,cl,content)=>{const n=document.createElement(tag);if(cl)n.className=cl;if(content!==undefined)n.textContent=content;return n};
 const monthOK=v=>/^\d{4}-(0[1-9]|1[0-2])$/.test(String(v||''));
 const num=v=>typeof v==='number'&&Number.isFinite(v);
 const safe=v=>v&&Array.isArray(v.records)?v.records:[];
 const request=async path=>{const r=await fetch(path+'?check='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(path+' HTTP '+r.status);return r.json()};
 const css=`#hq{max-width:1440px;margin:28px auto 48px;padding:0 32px;color:#243950;font:inherit}#hq *{box-sizing:border-box}#hq .hq-card{border:1px solid #dfe8f2;border-radius:16px;padding:24px;background:#fff;box-shadow:0 6px 22px #18324b0a}#hq h2{font-size:21px;margin:0 0 8px}#hq .hq-sub{color:#60748d;line-height:1.6;font-size:14px}#hq .hq-badges{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}#hq .hq-pill{display:inline-block;padding:8px 11px;border-radius:8px;background:#edf3f8;font-size:13px}#hq .hq-good{background:#e9f7ee;color:#17613e}#hq .hq-warn{background:#fff1df;color:#8c561b}#hq .hq-bad{background:#fdebea;color:#9a2727}#hq button{border:1px solid #b7cddd;padding:10px 15px;background:#f4f8fc;color:#24415d;border-radius:9px;cursor:pointer;font-weight:700}#hq .hq-actions{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:15px 0}#hq .hq-details{margin:12px 0}#hq .hq-table{overflow:auto;max-height:380px;margin-top:10px}#hq table{border-collapse:collapse;width:100%;font-size:13px}#hq th,#hq td{border-bottom:1px solid #e7edf5;text-align:left;padding:11px}#hq th{background:#f5f8fc;color:#5e738b}#hq .hq-message{font-size:13px;line-height:1.8;white-space:pre-wrap;color:#36526d;margin:12px 0}#hq details summary{cursor:pointer;font-weight:700}#hq a{color:#176b9c}#hq .hq-quiet{color:#60748d;font-size:12px;line-height:1.6}#hq input[type=file]{font-size:12px;max-width:100%}@media(max-width:600px){#hq{padding:0 14px}#hq .hq-card{padding:15px}}`;
 const style=el('style');style.textContent=css;document.head.append(style);
 const panel=el('section');panel.id='hq';const card=el('div','hq-card');panel.append(card);
 card.append(el('h2','', '데이터 신뢰성 검사'),el('p','hq-sub','내부 검사와 공식 원본 재수집 검사를 구분합니다. 전월 대비 변동은 오류가 아닌 참고 정보입니다.'));
 const badges=el('div','hq-badges'),actions=el('div','hq-actions'),btn=el('button','','현재 데이터 다시 검사'),file=el('input');
 btn.type='button';file.type='file';file.accept='.json,application/json';file.setAttribute('aria-label','공식 자료 비교 파일 선택');
 actions.append(btn,el('span','','원본 JSON 직접 비교:'),file);
 const status=el('div','hq-message','검사를 준비하고 있습니다…');const link=el('a','', '축산유통 통계누리 공식 통계표 열기');link.href=OFFICIAL;link.target='_blank';link.rel='noopener noreferrer';
 const details=el('details','hq-details'),sum=el('summary','', '검사 결과 상세보기'),tableHolder=el('div','hq-table');details.append(sum,tableHolder);
 card.append(badges,actions,status,link,details,el('p','hq-quiet','정밀도 안내: 현재 공식 소도체 항목별 평균표에서 근내지방도 등 평균 지표는 정수로 제공됩니다. 예를 들어 7.0 표시는 원본 정수 7의 화면 표기이지, 실제 평균이 소수 첫째 자리까지 7.0이라는 증거가 아닙니다. 동일 집계 기준의 소수점 공식 원본은 아직 확보되지 않았습니다.'),el('p','hq-quiet','공식 자동 검증의 범위는 수집한 응답에 포함된 월에 한정됩니다. 파일 수동 업로드만으로 출처가 인증되지는 않습니다.'));
 const anchor=document.querySelector('main .footer')||document.querySelector('footer');if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(panel,anchor);else (document.querySelector('main')||document.body).append(panel);
 let current=null;
 const badge=(title,value,type='')=>badges.append(el('span','hq-pill '+(type?'hq-'+type:''),title+': '+value));
 const entry=(severity,type,id,message)=>({severity,type,id,message});
 function inspect(doc){
  const rows=safe(doc),errors=[],notices=[],keys=new Set(),months=new Set();
  if(!rows.length)errors.push(entry('오류','구조','data.json','records 배열이 없습니다.'));
  for(const r of rows){
   const id=(r.month||'?')+' / '+(r.sex||'?');
   if(!monthOK(r.month))errors.push(entry('오류','월 형식',id,'YYYY-MM 형식이 아닙니다.'));
   if(!['거세우','암소'].includes(r.sex))errors.push(entry('오류','성별',id,'거세우 또는 암소만 허용합니다.'));
   if(keys.has(id))errors.push(entry('오류','중복',id,'중복된 월/성별입니다.'));keys.add(id);months.add(r.month);
   for(const [k,n] of Object.entries(METRIC))if(!num(r[k])||r[k]<0)errors.push(entry('오류','수치',id,n+' 누락 또는 수치 형식 오류'));
   if(num(r.marbling)&&(r.marbling<1||r.marbling>9))errors.push(entry('오류','범위',id,'근내지방도 범위를 벗어남'));
  }
  const all=[...months].filter(monthOK).sort();
  if(all.length){let y=+all[0].slice(0,4),m=+all[0].slice(5);while(y*12+m<=+all.at(-1).slice(0,4)*12+(+all.at(-1).slice(5))){
   const mon=y+'-'+String(m).padStart(2,'0');for(const sex of ['거세우','암소'])if(!keys.has(mon+' / '+sex))errors.push(entry('오류','자료 누락',mon+' / '+sex,'월별 데이터가 없습니다.'));
   if(++m>12){y++;m=1;}
  }}
  for(const sex of ['거세우','암소']){
   const seq=rows.filter(r=>r.sex===sex&&monthOK(r.month)).sort((a,b)=>a.month.localeCompare(b.month));
   for(let i=1;i<seq.length;i++)for(const [k,name] of Object.entries(METRIC)){
    const p=seq[i-1][k],v=seq[i][k];if(!num(p)||!num(v)||p<=0)continue;
    const pct=Math.abs((v/p-1)*100);if(pct>LIMITS[k]*100)notices.push(entry('참고','월간 변동',seq[i].month+' / '+sex,`${name} 전월 대비 ${pct.toFixed(1)}% 변동. 통계 오류로 판정하지 않습니다.`));
   }
  }
  const latest=all.at(-1)||'미확인';
  if(doc.latest_month&&doc.latest_month!==latest)errors.push(entry('오류','최신 월 메타데이터','latest_month',`선언 월 ${doc.latest_month}, 실제 월 ${latest}`));
  return {errors,notices,latest,total:rows.length};
 }
 function draw(items){tableHolder.replaceChildren();if(!items.length){tableHolder.append(el('p','hq-quiet','검사에서 오류·검토 항목을 찾지 못했습니다.'));return;}
  const t=el('table'),head=el('tr');for(const name of ['구분','유형','대상','내용'])head.append(el('th','',name));t.append(head);
  for(const it of items.slice(0,150)){const tr=el('tr');for(const x of [it.severity,it.type,it.id,it.message])tr.append(el('td','',String(x)));t.append(tr);}tableHolder.append(t);
 }
 async function run(){badges.replaceChildren();status.textContent='저장된 통계를 다시 확인하고 있습니다…';try{
  const results=await Promise.allSettled(['data.json','grade_data.json','age_data.json','quality_report.json'].map(request));
  if(results[0].status!=='fulfilled')throw results[0].reason;
  const data=results[0].value,report=results[3].status==='fulfilled'?results[3].value:null;
  current=data;const result=inspect(data),errors=result.errors,notices=result.notices;
  for(let i=1;i<=2;i++)if(results[i].status!=='fulfilled')notices.push(entry('참고','보조 데이터',i===1?'grade_data.json':'age_data.json','별도 통계 파일을 확인하지 못했습니다.'));
  badge('최신 저장 월',result.latest);badge('저장 행 수',result.total+'행');
  badge('데이터 구조 오류',errors.length+'건',errors.length?'bad':'good');
  badge('변동 참고',notices.length+'건',notices.length?'warn':'good');
  let agent='미설정',detailMessage='';
  if(report&&report.status==='verified_current_source'){
   agent='최근 공식 수집 검증';
   const months=Array.isArray(report.verified_months)?report.verified_months:[];
   detailMessage=`공식 응답을 재수집해 확인한 월: ${months.length?months.join(', '):'없음'}\n`;badge('자동 검증',agent,'good');
   badge('자동 수정·추가',Array.isArray(report.corrections)?report.corrections.length+'행':'미확인');
  }else if(report&&report.status==='blocked_kept_previous'){
   agent='오류 차단·기존 자료 보존';badge('자동 검증',agent,'warn');
  }else badge('자동 검증',agent,'warn');
  status.textContent=`마지막 저장 월: ${result.latest}\n자동 검증 실행 시각: ${report?.checked_at_kst||'아직 없음'}\n${detailMessage}${report?.message||'자동 검증 보고서가 아직 없습니다.'}\n공식 통계 발표시각: ${data.official_published_at||'미확인'}\n※ 전체 과거 데이터의 독립 출처 대조를 의미하지 않습니다.`;
  const all=[...errors,...notices];draw(all);details.open=errors.length>0;
 }catch(err){badge('검사','불러오기 실패','bad');status.textContent='검사 실패: '+err.message+'\n홈페이지 데이터는 변경하지 않았습니다.';draw([entry('오류','연결','data.json',err.message)]);details.open=true;}}
 file.addEventListener('change',async()=>{const f=file.files&&file.files[0];if(!f||!current)return;try{
  const value=JSON.parse(await f.text()),rows=Array.isArray(value)?value:safe(value);
  if(!rows.length)throw Error('JSON의 records 배열이 비어 있습니다.');const lookup=new Map(),diff=[];
  for(const r of rows){const k=r.month+' / '+r.sex;if(lookup.has(k))diff.push(entry('오류','원본 중복',k,'동일 월·성별 중복'));lookup.set(k,r)}
  let matched=0;for(const r of safe(current)){const k=r.month+' / '+r.sex,o=lookup.get(k);if(!o){diff.push(entry('미포함','원본 범위',k,'비교 파일에 없는 자료'));continue;}matched++;
   for(const [key,label] of Object.entries(METRIC)){if(!num(o[key]))diff.push(entry('오류','원본 결측',k,label+' 값 없음'));else if(+r[key]!==+o[key])diff.push(entry('차이','수치 불일치',k,`${label}: 홈페이지 ${r[key]} / 업로드 ${o[key]}`));}}
  badges.replaceChildren();badge('대조 행',matched+'개');badge('확인 사항',diff.length+'건',diff.length?'warn':'good');badge('파일 출처','진위 미확인','warn');
  status.textContent=`${f.name}: ${matched}개 행 비교, 차이 또는 범위 확인 ${diff.length}건. 업로드 파일이 공식 자료인지는 인증되지 않았습니다.`;
  draw(diff);details.open=true;
 }catch(err){status.textContent='비교 실패: '+err.message;}});
 btn.addEventListener('click',run);run();
})();
