/* HANWOO INSIGHT independent data-quality panel, v1.3.1.
   Read-only: never overwrites collection, dashboard records, or source files. */
(()=>{'use strict';
const FILES=['data.json','grade_data.json','age_data.json'];
const FIELDS={count:'판정두수',weight:'도체중',marbling:'근내지방도',rea:'등심단면적',fat:'등지방두께',live:'생체중',price:'경락단가'};
const LIMITS={count:0.30,weight:0.05,marbling:0.20,rea:0.10,fat:0.25,live:0.10,price:0.15};
const SRC='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2';
const $=id=>document.getElementById(id);
const h=(tag,attrs={},value)=>{const e=document.createElement(tag);for(const [k,v] of Object.entries(attrs)){if(k==='className')e.className=v;else e.setAttribute(k,v)}if(value!==undefined)e.textContent=value;return e};
const n=v=>Number(v).toLocaleString('ko-KR',{maximumFractionDigits:2});
function safeRows(v){return (v&&Array.isArray(v.records))?v.records:[]}
function isMonth(x){return /^\d{4}-(0[1-9]|1[0-2])$/.test(String(x||''))}
function textAt(id,text){$(id).textContent=text}
const style=h('style');style.textContent=`#hq{max-width:1440px;margin:26px auto 44px;padding:0 32px;color:#243950;font:inherit}#hq *{box-sizing:border-box}#hq .hq-card{background:#fff;border:1px solid #dfe8f2;border-radius:16px;padding:22px;box-shadow:0 8px 24px #132f4a08}#hq h2{font-size:21px;margin:0 0 9px}#hq p,#hq small{color:#60748d;line-height:1.6}#hq button{border:1px solid #b7cddd;padding:9px 13px;background:#f4f8fc;border-radius:9px;color:#24415d;cursor:pointer;font-weight:700}#hq button:hover{background:#e7f3fc}#hq .hq-badges{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}#hq .hq-pill{padding:8px 11px;border-radius:8px;background:#edf3f8;font-size:13px}#hq .hq-good{background:#e9f7ee;color:#17613e}#hq .hq-warn{background:#fff1df;color:#8c561b}#hq .hq-bad{background:#fdebea;color:#9a2727}#hq table{width:100%;border-collapse:collapse;font-size:13px}#hq td,#hq th{text-align:left;border-bottom:1px solid #e8eef4;padding:10px 8px}#hq th{color:#637991;background:#f6f9fc}#hq .hq-table{max-height:340px;overflow:auto;margin-top:10px}#hq .hq-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:15px 0}#hq input[type=file]{max-width:100%;font-size:12px}#hq .hq-quiet{font-size:12px;color:#667b90}#hq a{color:#176b9c}#hq .hq-message{margin:12px 0;white-space:pre-wrap;font-size:13px}#hq details{margin-top:12px}#hq summary{cursor:pointer;font-weight:700}@media(max-width:600px){#hq{padding:0 16px}#hq .hq-card{padding:14px}}`;
(document.head||document.documentElement).append(style);
const panel=h('section',{id:'hq'}),card=h('div',{className:'hq-card'});panel.append(card);
card.append(h('h2',{},'데이터 신뢰성 검사'),h('p',{},'현재 공개된 데이터를 읽기 전용으로 검사합니다. 내부 검사는 공식 원본 일치 검증과 다릅니다.'));
const badges=h('div',{className:'hq-badges',id:'hq-badges'}),actions=h('div',{className:'hq-actions'}),run=h('button',{type:'button'},'현재 데이터 다시 검사'),file=h('input',{type:'file',accept:'.json,application/json','aria-label':'공식 원본 비교용 JSON 파일 선택'});
actions.append(run,h('label',{},'공식 원본 JSON 파일 비교: '),file);card.append(badges,actions);
card.append(h('div',{className:'hq-message',id:'hq-message'},'검사 준비 중…'));
const link=h('a',{href:SRC,target:'_blank',rel:'noopener noreferrer'},'축산유통 통계누리 원본 통계표 열기');card.append(link);
const detail=h('details');detail.append(h('summary',{},'검사 결과 상세보기'),h('div',{className:'hq-table',id:'hq-detail'}));card.append(detail);
card.append(h('p',{className:'hq-quiet'},'비교용 JSON은 축산물품질평가원 자료에서 생성한 검증 가능한 원본이어야 합니다. 브라우저에 업로드한 임의 파일은 공식 출처가 자동으로 인증되지 않습니다.'));
const locate=document.querySelector('main .footer')||document.querySelector('footer');if(locate&&locate.parentNode){locate.parentNode.insertBefore(panel,locate)}else(document.querySelector('main')||document.body).append(panel);
let current=null, lastIssues=[];
function badge(title,value,kind=''){badges.append(h('span',{className:'hq-pill '+(kind?'hq-'+kind:'')},title+': '+value))}
function showIssues(items){const holder=$('hq-detail');holder.replaceChildren();if(!items.length){holder.append(h('p',{},'검사 대상에서 구조상 문제나 설정된 이상치 경고가 발견되지 않았습니다.'));return}
 const t=h('table'),head=h('tr');for(const x of ['분류','대상','내용'])head.append(h('th',{},x));t.append(head);
 for(const it of items.slice(0,120)){let tr=h('tr');for(const s of [it.type,it.id,it.message])tr.append(h('td',{},String(s)));t.append(tr)}holder.append(t);
 if(items.length>120)holder.append(h('small',{},`나머지 ${items.length-120}건은 화면 표시에서 생략`));}
const issue=(issues,type,id,message)=>issues.push({type,id,message});
function inspect(data,related){const rows=safeRows(data);const issues=[],keys=new Set(),months=new Set();
 if(!rows.length)issue(issues,'구조 오류','data.json','records 배열이 비어 있거나 없습니다.');
 for(const r of rows){const key=`${r.month||'?'} / ${r.sex||'?'}`;
 if(!isMonth(r.month))issue(issues,'월 형식',key,'YYYY-MM 형식이 아닙니다.');
 if(!['거세우','암소'].includes(r.sex))issue(issues,'성별 형식',key,'거세우 또는 암소가 아닙니다.');
 if(keys.has(key))issue(issues,'중복',key,'같은 월·성별이 중복되었습니다.');keys.add(key);months.add(r.month);
 for(const [field,name] of Object.entries(FIELDS)){const v=r[field];if(v===undefined||v===null||v===''||!Number.isFinite(Number(v))||Number(v)<0)issue(issues,'누락/숫자 오류',key,name+' 값이 잘못되었습니다.');}
 if(Number.isFinite(+r.marbling)&&(+r.marbling<1||+r.marbling>9))issue(issues,'범위 확인',key,'근내지방도 1~9 범위를 벗어났습니다.');
 }
 const ordered=[...months].filter(isMonth).sort();if(ordered.length){let cursor=ordered[0];while(cursor<=ordered.at(-1)){for(const sex of ['거세우','암소'])if(!keys.has(`${cursor} / ${sex}`))issue(issues,'월·성별 누락',`${cursor} / ${sex}`,'해당 월/성별 행이 없습니다.');const [y,m]=cursor.split('-').map(Number);cursor=`${y+(m===12)}-${String(m===12?1:m+1).padStart(2,'0')}`;}}
 for(const sex of ['거세우','암소']){const seq=rows.filter(r=>r.sex===sex&&isMonth(r.month)).sort((a,b)=>a.month.localeCompare(b.month));for(let i=1;i<seq.length;i++){const a=seq[i-1],b=seq[i];for(const [f,label] of Object.entries(FIELDS)){let p=+a[f],v=+b[f];if(!Number.isFinite(p)||!Number.isFinite(v)||p<=0)continue;const pct=Math.abs(v/p-1);if(pct>LIMITS[f])issue(issues,'변동 검토',`${b.month} / ${sex}`,`${label} 전월 대비 ${Math.round(pct*1000)/10}% 변동 (초기 기준 ${LIMITS[f]*100}%). 통계 오류 확정은 아닙니다.`)}}}
 for(const [name,data2] of Object.entries(related)){if(!data2)issue(issues,'자료 확인',name,'파일을 읽지 못했습니다.');else if(!Array.isArray(data2.records))issue(issues,'구조 확인',name,'records 배열이 없습니다.');}
 return {issues,latest:ordered.at(-1)||'미확인',rows:rows.length};}
async function load(path){const sep=path.includes('?')?'&':'?';let res=await fetch(path+sep+'hq='+Date.now(),{cache:'no-store'});if(!res.ok)throw Error(path+': HTTP '+res.status);return res.json()}
async function runCheck(){badges.replaceChildren();textAt('hq-message','저장된 공개 파일을 다시 조회하고 있습니다…');try{
 const results=await Promise.allSettled(FILES.map(load));if(results[0].status==='rejected')throw results[0].reason;
 const main=results[0].value,related={};FILES.slice(1).forEach((f,i)=>related[f]=results[i+1].status==='fulfilled'?results[i+1].value:null);
 current=main;const result=inspect(main,related);lastIssues=result.issues;
 badge('최신 저장 월',result.latest);badge('저장 행 수',result.rows+'행');badge('내부 경고',result.issues.length+'건',result.issues.length?'warn':'good');
 badge('공식 원본 대조','미검증','warn');
 const claim=main.latest_month||'미기재',sync=main.last_success_kst||'미기재';
 if(claim!==result.latest){issue(lastIssues,'메타데이터 불일치','latest_month',`선언값 ${claim}, 실제 데이터 최종월 ${result.latest}`)}
 textAt('hq-message',`데이터 파일에서 확인된 마지막 월: ${result.latest}\n수집 성공시각 메타데이터: ${sync}\n공식 발표일: ${main.official_published_at||'미확인'}\n공식 원본과의 독립 대조는 아직 수행되지 않았습니다.`);
 showIssues(lastIssues);if(lastIssues.length)detail.open=true;
 }catch(err){badge('검사 상태','데이터 불러오기 실패','bad');textAt('hq-message',`검사 실패: ${err.message}. 원래 대시보드 데이터는 변경되지 않았습니다.`);showIssues([{type:'읽기 실패',id:'data.json',message:err.message}]);}}
function normalizeDoc(obj){if(Array.isArray(obj))return obj;if(obj&&Array.isArray(obj.records))return obj.records;throw Error('JSON 배열 또는 records 배열이 필요합니다.')}
file.addEventListener('change',async()=>{const f=file.files?.[0];if(!f||!current)return;try{const raw=JSON.parse(await f.text()),official=normalizeDoc(raw),local=safeRows(current),lookup=new Map();const differences=[];
 for(const r of official){if(!isMonth(r.month)||!['거세우','암소'].includes(r.sex))continue;const k=r.month+' / '+r.sex;if(lookup.has(k))issue(differences,'원본 중복',k,'원본 파일에 중복 항목');lookup.set(k,r)}
 let matched=0;for(const r of local){const k=r.month+' / '+r.sex,o=lookup.get(k);if(!o){issue(differences,'원본 미포함',k,'업로드된 JSON에 해당 월/성별이 없습니다.');continue}matched++;
 for(const [key,label] of Object.entries(FIELDS)){if(!Number.isFinite(Number(o[key]))){issue(differences,'원본 결측',k,label+' 원본 값 없음');continue}if(Math.abs(+r[key]-(+o[key]))>1e-7)issue(differences,'수치 불일치',k,`${label}: 홈페이지 ${r[key]} / 비교 파일 ${o[key]}`)}}
 for(const k of lookup.keys())if(!local.some(r=>r.month+' / '+r.sex===k))issue(differences,'홈페이지 미반영',k,'비교 파일에 있으나 홈페이지에 없는 월/성별');
 badges.replaceChildren();badge('업로드 파일',f.name);badge('비교된 월·성별',matched+'건');badge('수치/범위 불일치',differences.length+'건',differences.length?'bad':'good');badge('출처 진위','미확인','warn');
 textAt('hq-message',`${matched}개 월·성별 행을 비교했습니다. ${differences.length}개 차이 또는 확인 필요 사항이 있습니다.\n주의: 이 파일의 공식 출처 진위 및 집계 조건은 자동으로 인증하지 않았습니다.`);
 showIssues(differences);detail.open=true;
 }catch(err){textAt('hq-message','비교 실패: '+err.message)}});
run.addEventListener('click',runCheck);runCheck();
})();
