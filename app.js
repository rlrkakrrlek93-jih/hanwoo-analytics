/* HANWOO INSIGHT — standalone native-style mobile interface.
   Live data is read-only; official source files are shared with desktop dashboard. */
(()=>{'use strict';
const $=selector=>document.querySelector(selector);
const nf=new Intl.NumberFormat('ko-KR');
const fmt=(n,d=0)=>Number.isFinite(Number(n))?Number(n).toLocaleString('ko-KR',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validLink=u=>{try{const x=new URL(u,location.href);return x.protocol==='https:'?esc(x.href):'#'}catch(_){return '#'}};
const yearColors={'2022':'#8969c0','2023':'#c76e78','2024':'#4c83bd','2025':'#d69a45','2026':'#2c9481'};
const names={steer:'거세우',female:'암소',male:'수소'};
const screenNames=['home','market','semen','quality'];
const state={data:{},screen:'home',metric:'price',sex:'steer',marketMonth:10,semenMonth:7,marketYears:new Set(['2024','2025','2026']),semenYears:new Set(['2022','2023','2024','2025','2026']),qualitySex:'거세우',qualityMonth:'',qualityMetric:'weight'};
let loading=false,installPrompt=null;
const tabs=[...document.querySelectorAll('.bottom-tabs [data-tab]')];
const sourceLine=(label,url)=>'<p class="source-line">자료 출처 · <a href="'+validLink(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+'</a></p>';
const dateText=month=>month?month.slice(0,4)+'년 '+Number(month.slice(5))+'월':'미확인';
const logoText='HANWOO INSIGHT';

function setScreen(name,scroll=true){
 const screen=screenNames.includes(name)?name:'home';
 state.screen=screen;
 for(const section of document.querySelectorAll('.app-screen'))section.hidden=section.dataset.screen!==screen;
 for(const tab of tabs){if(tab.dataset.tab===screen)tab.setAttribute('aria-current','page');else tab.removeAttribute('aria-current')}
 if(scroll)window.scrollTo({top:0,behavior:'instant'});
 document.title=({home:'홈',market:'시장 분석',semen:'정액 판매량',quality:'품질 성적'}[screen])+' | '+logoText;
}
function route(){setScreen(location.hash.replace('#','')||'home')}
window.addEventListener('hashchange',route);route();

function updateNet(){
 const off=!navigator.onLine;$('#offlineNotice').hidden=!off;
 $('#networkFlag').innerHTML=off?'오프라인':'<i></i>공식 데이터';
}
window.addEventListener('online',updateNet);window.addEventListener('offline',updateNet);updateNet();
async function loadJSON(path){
 const response=await fetch('./'+path+'?v='+Date.now(),{cache:'no-store'});
 if(!response.ok)throw Error(path+': HTTP '+response.status);
 const result=await response.json();
 if(!Array.isArray(result.records))throw Error(path+': 형식 오류');
 return result;
}
async function loadAll(){
 if(loading)return;loading=true;
 const refresh=$('#refreshBtn');refresh.disabled=true;
 refresh.style.opacity='.5';
 const files={market:'market_supply_data.json',semen:'semen_sales_data.json',quality:'data.json',grades:'grade_data.json',ages:'age_data.json'};
 const results=await Promise.allSettled(Object.entries(files).map(async([k,path])=>[k,await loadJSON(path)]));
 for(let i=0;i<results.length;i++){
  const result=results[i];
  if(result.status==='fulfilled')state.data[result.value[0]]=result.value[1];
  else console.warn('HANWOO official dataset not loaded:',Object.values(files)[i],String(result.reason).slice(0,200));
 }
 for(const [key,fn] of [['home',renderHome],['market',renderMarket],['semen',renderSemen],['quality',renderQuality]]){
  try{fn()}catch(e){console.error('HANWOO '+key+' UI:',e);$('#'+key+'Content').innerHTML='<div class="loading-block">이 화면의 데이터를 불러오지 못했습니다.<br/>상단 새로고침을 눌러 주세요.</div>'}
 }
 loading=false;refresh.disabled=false;refresh.style.opacity='';
}
$('#refreshBtn').addEventListener('click',loadAll);

function latestRow(dataset){return dataset?.records?.at(-1)}
function deltaPct(latest,prev){if(!Number.isFinite(latest)||!Number.isFinite(prev)||prev===0)return '비교 자료 없음';const v=(latest-prev)/prev*100;return '전월 대비 '+(v>0?'+':'')+fmt(v,1)+'%'}
function card(icon,name,val,unit,note,type=''){
 return '<article class="stat-card '+type+'"><div class="stat-icon">'+icon+'</div><div class="stat-name">'+esc(name)+'</div><div class="stat-val">'+esc(val)+' <small>'+esc(unit)+'</small></div><div class="stat-note">'+esc(note)+'</div></article>';
}
function homeInsights(m,s){
 const inventory=m?.records||[],latest=inventory.at(-1),prev=inventory.at(-2);
 const priceNote=latest&&prev?'경락단가 '+deltaPct(latest.auction_price_by_sex.steer,prev.auction_price_by_sex.steer):'가격 비교 자료 확인 중';
 return '<div class="section-intro"><h2>지금 주목할 지표</h2><span class="meta-dot">공식 월별 발표값</span></div>'+
 '<div class="paper-card insight-stack">'+
 '<div class="insight-item"><span class="insight-dot">↗</span><div><b>거세우 경락단가</b><small>'+esc(priceNote)+'</small></div></div>'+
 '<div class="insight-item"><span class="insight-dot">▥</span><div><b>한우 사육두수</b><small>월말 재고 기준 · 시장 공급 규모를 보여줍니다.</small></div></div>'+
 '<div class="insight-item"><span class="insight-dot">♧</span><div><b>한우 정액 판매량</b><small>판매량은 실제 인공수정 사용량과 다릅니다.</small></div></div></div>';
}
function renderHome(){
 const m=state.data.market,s=state.data.semen,q=state.data.quality;
 const last=latestRow(m),prev=m?.records?.at(-2),semen=latestRow(s);
 if(!last){$('#homeContent').innerHTML='<div class="loading-block">시장 데이터를 불러올 수 없습니다. 네트워크 연결을 확인해 주세요.</div>';return}
 const price=last.auction_price_by_sex.steer;
 $('#homeContent').innerHTML=
  '<div class="overview-hero"><div class="hero-meta"><span>전국 한우 시장 리포트</span><span>'+esc(dateText(last.month))+'</span></div>'+
  '<div class="lead-label">거세우 평균 경락단가</div><div class="lead-number">'+fmt(price)+'<small>원/kg</small></div>'+
  '<div class="hero-line"><span>전월 대비 경락가격</span><b>'+esc(deltaPct(price,prev?.auction_price_by_sex?.steer))+'</b></div></div>'+
  '<div class="stat-grid">'+
  card('▤','한우 사육두수',fmt(last.inventory_head/10000,1),'만 두',dateText(last.month)+' · 월말')+
  card('▥','등급 판정두수',fmt(last.graded_head),'두',dateText(last.month)+' · 월별')+
  card('₩','암소 경락단가',fmt(last.auction_price_by_sex.female),'원/kg',dateText(last.month)+' · 월평균','price')+
  card('♧','한우 정액 판매량',semen?fmt(semen.sold_thousand_str,1):'—','천 str',semen?dateText(semen.month)+' · 최근 확보':'공식 자료 미확보','semen')+
  '</div>'+
  homeInsights(m,s)+
  '<div class="section-intro"><h2>시장 가격 흐름</h2><a href="#market">자세히 보기 →</a></div>'+
  miniTrend(m.records.filter(r=>r.month.startsWith('2026-')).map(r=>r.auction_price_by_sex.steer),'2026년 거세우 경락단가 (원/kg)')+
  '<div class="section-intro"><h2>분석 바로가기</h2></div>'+
  '<div class="quick-actions"><a class="quick-action" href="#market">사육·가격 분석 <span>↗</span></a><a class="quick-action" href="#semen">정액 판매량 <span>↗</span></a><a class="quick-action" href="#quality">품질 성적 <span>↗</span></a><a class="quick-action" href="./?desktop=1">PC 홈페이지 <span>↗</span></a></div>'+
  '<p class="source-line">통계 갱신 · '+esc(m.last_success_kst||'미확인')+'<br/>각 지표는 공식 공표 주기가 달라 마지막 수집월이 다를 수 있습니다.</p>';
}
function miniTrend(vals,label){
 if(!vals.length)return '';
 const min=Math.min(...vals)-500,max=Math.max(...vals)+500;
 const xx=i=>16+i*(308/Math.max(vals.length-1,1)),yy=v=>106-(v-min)/(max-min)*75;
 const points=vals.map((v,i)=>[xx(i),yy(v)]);
 const path=points.map(([x,y],i)=>(i?'L':'M')+x.toFixed(1)+','+y.toFixed(1)).join(' ');
 return '<div class="chart-surface"><div class="chart-heading"><strong>'+esc(label)+'</strong><span>1~'+vals.length+'월</span></div>'+
 '<svg viewBox="0 0 340 125" role="img" aria-label="'+esc(label)+' 추세">'+
 '<path d="'+esc(path)+'" stroke="#bd6653" stroke-width="3.3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'+
 points.map(([x,y])=>'<circle cx="'+x+'" cy="'+y+'" r="3.8" fill="#fff" stroke="#bd6653" stroke-width="2.1"/>').join('')+
 '</svg><div class="chart-note">최신 값 '+fmt(vals.at(-1))+'원/kg · 자세한 연도별 비교는 시장 탭에서 확인</div></div>';
}

function panelMetric(row,key,sex){
 if(key==='inventory')return row?.inventory_head;
 if(key==='graded')return row?.graded_head;
 if(key==='price')return row?.auction_price_by_sex?.[sex];
 return null;
}
function marketUnit(key){return key==='price'?'원/kg':'두'}
function lineChart(series,{label,unit,metric,monthKey}){
 const entries=series.flatMap(s=>s.values.filter(r=>Number.isFinite(r.value)).map(r=>r.value));
 if(!entries.length)return '<div class="loading-block">그래프 데이터가 없습니다.</div>';
 const low=Math.min(...entries),high=Math.max(...entries);
 const spread=Math.max(high-low,1),min=Math.max(0,low-spread*.17),max=high+spread*.17;
 const x=m=>28+(m-1)*(304/11),y=v=>160-(v-min)/(max-min)*122;
 const ticks=[0,1,2,3].map(i=>({v:min+(max-min)*i/3,y:160-i*(122/3)}));
 const axis=ticks.map(z=>'<line x1="28" y1="'+z.y.toFixed(1)+'" x2="332" y2="'+z.y.toFixed(1)+'" stroke="#edf1eb"/><text x="26" y="'+(z.y+3).toFixed(1)+'" text-anchor="end" font-size="8" fill="#9ca89f">'+esc(shortNum(z.v))+'</text>').join('');
 const monthLabels=[1,3,5,7,9,12].map(m=>'<text x="'+x(m).toFixed(1)+'" y="188" text-anchor="middle" font-size="10" fill="#9aa89f">'+m+'월</text>').join('');
 const lines=series.map(s=>{
  let path='',prev=0;
  for(const v of s.values){if(!Number.isFinite(v.value))continue;path+=(prev===v.month-1?' L':' M')+x(v.month).toFixed(1)+' '+y(v.value).toFixed(1);prev=v.month}
  const dots=s.values.filter(r=>Number.isFinite(r.value)).map(v=>'<circle data-chart-point="'+esc(metric)+'" data-month="'+v.month+'" data-year="'+esc(s.year)+'" tabindex="0" role="button" aria-label="'+esc(s.year+'년 '+v.month+'월 '+fmt(v.value,1)+' '+unit)+'" cx="'+x(v.month).toFixed(1)+'" cy="'+y(v.value).toFixed(1)+'" r="'+(v.month===monthKey?4.8:3.1)+'" fill="'+esc(s.color)+'" stroke="#fff" stroke-width="1.6"><title>'+esc(s.year+'년 '+v.month+'월 '+fmt(v.value,1)+' '+unit)+'</title></circle>').join('');
  return '<path d="'+path.trim()+'" fill="none" stroke="'+esc(s.color)+'" stroke-width="2.7" stroke-linejoin="round" stroke-linecap="round"/>'+dots;
 }).join('');
 const legend=series.map(s=>'<span><i style="background:'+s.color+'"></i>'+esc(s.year)+'년</span>').join('');
 return '<div class="chart-surface"><div class="chart-heading"><strong>'+esc(label)+'</strong><span>'+esc(unit)+'</span></div>'+
 '<svg viewBox="0 0 360 201" role="img" aria-label="'+esc(label+' 연도별 월간 비교')+'">'+axis+monthLabels+lines+'</svg>'+
 '<div class="chart-legend">'+legend+'</div><p class="chart-note">점을 누르면 해당 월 수치가 아래에 표시됩니다. 미발표 월은 연결하지 않습니다.</p></div>';
}
function shortNum(v){return Math.abs(v)>=1000000?fmt(v/1000000,1)+'M':Math.abs(v)>=1000?fmt(v/1000,0)+'k':fmt(v,0)}
function pills(key,value){
 return '<div class="month-pills" role="group" aria-label="비교할 월 선택">'+Array.from({length:12},(_,i)=>{
 const m=i+1;return '<button type="button" data-month-choice="'+esc(key)+'" data-month="'+m+'" aria-pressed="'+(m===value)+'">'+m+'월</button>'
 }).join('')+'</div>';
}
function monthDetail(rows,month,label,unit){
 return '<div class="month-detail"><b>'+month+'월 · '+esc(label)+'</b><div class="detail-list">'+rows.map(r=>
 '<div class="detail-row"><span><i style="background:'+r.color+'"></i>'+esc(r.year)+'년</span><strong>'+ (Number.isFinite(r.value)?fmt(r.value,r.decimal||0)+' '+esc(unit):'자료 미확인')+'</strong></div>'
 ).join('')+'</div></div>';
}
function headerSmall(title,right=''){return '<div class="section-intro"><h2>'+esc(title)+'</h2><span class="meta-dot">'+esc(right)+'</span></div>'}
function marketSeries(){
 const m=state.data.market,years=['2024','2025','2026'];
 return years.filter(y=>state.marketYears.has(y)).map(year=>({
  year,color:yearColors[year],values:Array.from({length:12},(_,i)=>{
   const mon=i+1,row=m.records.find(r=>r.month===year+'-'+String(mon).padStart(2,'0'));
   const value=panelMetric(row,state.metric,state.sex);
   return {month:mon,value:Number.isFinite(value)?value:null};
  })
 }));
}
function renderMarket(){
 const m=state.data.market;
 if(!m){$('#marketContent').innerHTML='<div class="loading-block">시장 통계를 불러올 수 없습니다.</div>';return}
 const latest=m.records.at(-1);
 const metricNames={inventory:'사육두수',graded:'판정두수',price:'경락가격'};
 const label=(state.metric==='price'?names[state.sex]+' ':'')+metricNames[state.metric];
 const activeYears=marketSeries();
 const toggles=['2024','2025','2026'].map(y=>'<button type="button" data-market-year="'+y+'" aria-pressed="'+state.marketYears.has(y)+'" style="--year-color:'+yearColors[y]+'">'+y.slice(2)+'년</button>').join('');
 const controls='<div class="segmented" role="group" aria-label="시장 지표">'+[
  ['inventory','사육두수'],['graded','판정두수'],['price','경락가격']
 ].map(([id,name])=>'<button type="button" data-market-metric="'+id+'" aria-selected="'+(state.metric===id)+'">'+name+'</button>').join('')+'</div>';
 const sexSelect=state.metric==='price'?'<div class="select-row"><label for="marketSex">경락가격 분류</label><select class="mini-select" id="marketSex">'+Object.entries(names).map(([id,n])=>'<option value="'+id+'"'+(id===state.sex?' selected':'')+'>'+n+'</option>').join('')+'</select></div>':'';
 const selector='<div class="year-toggles" role="group" aria-label="비교 연도">'+toggles+'</div>';
 const detail=monthDetail(activeYears.map(s=>({...s,value:s.values[state.marketMonth-1]?.value})),state.marketMonth,label,marketUnit(state.metric));
 const numbers='<div class="kpi-strip">'+
   '<div class="kpi-mini"><span>최신 '+esc(label)+'</span><strong>'+fmt(panelMetric(latest,state.metric,state.sex),0)+'</strong><small>'+dateText(latest.month)+' · '+marketUnit(state.metric)+'</small></div>'+
   '<div class="kpi-mini highlight"><span>현재 데이터</span><strong>'+fmt(m.records.length)+'</strong><small>2024년 1월부터 · 확인된 월</small></div></div>';
 const tableRows=Array.from({length:12},(_,i)=>{
 const month=i+1;return '<tr><td>'+month+'월</td>'+['2024','2025','2026'].map(y=>{
  const row=m.records.find(r=>r.month===y+'-'+String(month).padStart(2,'0'));
  const v=panelMetric(row,state.metric,state.sex);
  return '<td'+(!Number.isFinite(v)?' class="missing"':'')+'>'+(Number.isFinite(v)?fmt(v):'—')+'</td>';
 }).join('')+'</tr>';
 }).join('');
 const table='<div class="data-table-card"><div class="data-table-header"><h2>월별 전체 수치</h2><span class="meta-dot">'+marketUnit(state.metric)+'</span></div>'+
 '<div class="scroll-table"><table class="data-table"><thead><tr><th>월</th><th>2024년</th><th>2025년</th><th>2026년</th></tr></thead><tbody>'+tableRows+'</tbody></table></div><p class="table-hint">숫자는 공표된 원자료 기준 · 미발표 월은 — 표시</p></div>';
 $('#marketContent').innerHTML=numbers+controls+sexSelect+selector+
 lineChart(activeYears,{label,unit:marketUnit(state.metric),metric:'market',monthKey:state.marketMonth})+
 pills('market',state.marketMonth)+detail+
 headerSmall('월별 비교표','1~12월')+table+
 sourceLine('축산물품질평가원 · 전국 한우 공식 월별 통계',m.source_grading);
}
function semenSeries(){
 const data=state.data.semen;
 return ['2022','2023','2024','2025','2026'].filter(y=>state.semenYears.has(y)).map(year=>({
 year,color:yearColors[year],values:Array.from({length:12},(_,i)=>{
 const mon=i+1,r=data.records.find(v=>v.month===year+'-'+String(mon).padStart(2,'0'));
 return {month:mon,value:r?.sold_thousand_str??null};
 })}));
}
function renderSemen(){
 const s=state.data.semen;
 if(!s){$('#semenContent').innerHTML='<div class="loading-block">정액 판매량 자료를 불러올 수 없습니다.</div>';return}
 const last=s.records.at(-1),series=semenSeries();
 const info='<div class="overview-hero semen-hero"><div class="hero-meta"><span>번식 동향 지표</span><span>'+dateText(last.month)+'</span></div><div class="lead-label">최근 확인된 정액 판매량</div><div class="lead-number">'+fmt(last.sold_thousand_str,1)+'<small>천 str</small></div>'+
 '<div class="hero-line"><span>전국한우협회·KREI 공표값</span><b>총 '+s.records.length+'개월</b></div></div>';
 const tabs='<div class="year-toggles semen-years" role="group" aria-label="정액 판매량 연도 선택">'+['2022','2023','2024','2025','2026'].map(y=>
 '<button type="button" data-semen-year="'+y+'" aria-pressed="'+state.semenYears.has(y)+'" style="--year-color:'+yearColors[y]+'">'+y.slice(2)+'년</button>').join('')+'</div>';
 const selected=series.map(s=>({...s,value:s.values[state.semenMonth-1]?.value,decimal:1}));
 const tableRows=Array.from({length:12},(_,i)=>{
  const mon=i+1;return '<tr><td>'+mon+'월</td>'+['2022','2023','2024','2025','2026'].map(y=>{
   const r=s.records.find(v=>v.month===y+'-'+String(mon).padStart(2,'0'));
   if(!r)return '<td class="missing">—</td>';
   return '<td><a href="'+validLink(r.source_url)+'" target="_blank" rel="noopener noreferrer" title="'+esc(r.source_name||'전국한우협회 한우 동향 분석')+'">'+fmt(r.sold_thousand_str,1)+'</a></td>';
  }).join('')+'</tr>';
 }).join('');
 const table='<div class="data-table-card"><div class="data-table-header"><h2>2022~2026 월별 판매량</h2><span class="meta-dot">천 str</span></div><div class="scroll-table"><table class="data-table"><thead><tr><th>월</th>'+['2022','2023','2024','2025','2026'].map(y=>'<th>'+y+'</th>').join('')+'</tr></thead><tbody>'+tableRows+'</tbody></table></div>'+
 '<p class="table-hint">숫자를 터치하면 해당 발표기관의 원본 PDF가 열립니다. —는 미확인 월입니다.</p></div>';
 $('#semenContent').innerHTML=info+headerSmall('연도별 판매량 비교','1~12월')+tabs+
 lineChart(series,{label:'정액 판매량',unit:'천 str',metric:'semen',monthKey:state.semenMonth})+
 pills('semen',state.semenMonth)+monthDetail(selected,state.semenMonth,'정액 판매량','천 str')+
 '<div class="paper-card" style="margin:18px 0 5px;background:#fffbf6"><strong style="display:block;font-size:12px;margin-bottom:7px">자료 해석 안내</strong><span style="display:block;color:#89958b;font-size:11px;line-height:1.8">정액 판매량과 실제 인공수정 사용량은 다릅니다. 2022~2025년 5월은 전국한우협회, 이후는 KREI 공표값이므로 제공기관 및 숫자 정밀도가 다릅니다.</span></div>'+
 headerSmall('전체 월별 숫자표','출처 링크 포함')+table+
 sourceLine('전국한우협회·KREI 공식자료',last.source_url);
}
function renderQuality(){
 const d=state.data.quality,g=state.data.grades,a=state.data.ages;
 if(!d){$('#qualityContent').innerHTML='<div class="loading-block">품질 데이터를 불러올 수 없습니다.</div>';return}
 const months=[...new Set(d.records.map(r=>r.month))].sort();
 if(!state.qualityMonth||!months.includes(state.qualityMonth))state.qualityMonth=months.at(-1);
 const row=d.records.find(r=>r.month===state.qualityMonth&&r.sex===state.qualitySex);
 const gr=g?.records?.find(r=>r.month===state.qualityMonth&&r.sex===state.qualitySex);
 const age=a?.records?.find(r=>r.month===state.qualityMonth&&r.sex===state.qualitySex);
 const ss='<div class="segmented" role="group" aria-label="성별 선택">'+['거세우','암소'].map(sex=>'<button data-quality-sex="'+sex+'" type="button" aria-selected="'+(state.qualitySex===sex)+'">'+sex+'</button>').join('')+'</div>';
 const sel='<div class="quality-selects"><select class="mini-select" id="qualityMonth" aria-label="통계 월 선택">'+months.map(m=>'<option value="'+m+'"'+(m===state.qualityMonth?' selected':'')+'>'+dateText(m)+'</option>').join('')+'</select><select class="mini-select" id="qualityMetric" aria-label="그래프 지표 선택">'+[
 ['weight','평균 도체중'],['price','경락가격'],['marbling','근내지방도'],['rea','등심단면적']
 ].map(([key,n])=>'<option value="'+key+'"'+(state.qualityMetric===key?' selected':'')+'>'+n+'</option>').join('')+'</select></div>';
 const cards=row?'<div class="stat-grid">'+
  card('▣','평균 도체중',fmt(row.weight),'kg',dateText(row.month))+
  card('₩','평균 경락단가',fmt(row.price),'원/kg',dateText(row.month),'price')+
  card('✦','평균 근내지방도',fmt(row.marbling),'No.',dateText(row.month))+
  card('◷','평균 도축개월령',age?fmt(age.age_months,1):'—','개월',age?'공식 발표 자료':'해당 월 미발표')+
 '</div>':'<div class="loading-block">선택한 월·성별 자료가 없습니다.</div>';
 const metricMap={weight:['평균 도체중','kg'],price:['경락단가','원/kg'],marbling:['근내지방도','No.'],rea:['등심단면적','㎠']};
 const [label,unit]=metricMap[state.qualityMetric];
 const series=[{year:state.qualitySex,color:state.qualitySex==='거세우'?'#357d73':'#ca776d',values:Array.from({length:12},(_,i)=>{
   const mon=i+1,r=d.records.find(r=>r.month===state.qualityMonth.slice(0,4)+'-'+String(mon).padStart(2,'0')&&r.sex===state.qualitySex);
   return {month:mon,value:r?.[state.qualityMetric]??null};
 })}];
 const grades=gr?['1++','1+','1','2','3'].map((key,i)=>{
  const v=gr.grades?.[key];
  const percent=v?.rate??0,col=['#b45f4d','#d39763','#dfa970','#8bae98','#8caaa0'][i];
  return '<div class="grade-item"><span>'+key+'</span><div class="grade-bar"><i style="width:'+Math.min(100,Math.max(0,percent))+'%;background:'+col+'"></i></div><div class="grade-number">'+fmt(percent,1)+'%<small>'+fmt(v?.count)+'두</small></div></div>';
 }).join(''):'<p style="font-size:12px;color:#819084">이 월의 등급 비율 자료가 없습니다.</p>';
 $('#qualityContent').innerHTML=ss+sel+cards+
 headerSmall('월별 성적 추이',state.qualitySex)+lineChart(series,{label,unit,metric:'quality',monthKey:Number(state.qualityMonth.slice(5))})+
 headerSmall('육질등급 출현율',dateText(state.qualityMonth))+'<div class="paper-card"><div class="grade-list">'+grades+'</div></div>'+
 '<div class="paper-card" style="margin-top:12px"><strong style="font-size:12px">판정 통계 안내</strong><p class="chart-note">육질등급 출현율과 일반 품질 통계는 서로 다른 공식 표에서 수집되어 판정두수가 다를 수 있습니다. 공표 자료를 임의로 합치지 않습니다.</p></div>'+
 sourceLine('축산물품질평가원 · 전국 품질 성적 통계',d.source);
}
const main=$('#appMain');
main.addEventListener('click',event=>{
 const btn=event.target.closest('button');
 if(btn){
  if(btn.hasAttribute('data-market-metric')){state.metric=btn.dataset.marketMetric;renderMarket();return}
  if(btn.hasAttribute('data-market-year')){const y=btn.dataset.marketYear;if(state.marketYears.has(y)){if(state.marketYears.size>1)state.marketYears.delete(y)}else state.marketYears.add(y);renderMarket();return}
  if(btn.hasAttribute('data-semen-year')){const y=btn.dataset.semenYear;if(state.semenYears.has(y)){if(state.semenYears.size>1)state.semenYears.delete(y)}else state.semenYears.add(y);renderSemen();return}
  if(btn.hasAttribute('data-month-choice')){
   if(btn.dataset.monthChoice==='market'){state.marketMonth=Number(btn.dataset.month);renderMarket()}
   if(btn.dataset.monthChoice==='semen'){state.semenMonth=Number(btn.dataset.month);renderSemen()}
   return;
  }
  if(btn.hasAttribute('data-quality-sex')){state.qualitySex=btn.dataset.qualitySex;renderQuality();return}
 }
 const dot=event.target.closest('[data-chart-point]');
 if(dot){
  const month=Number(dot.dataset.month);
  if(dot.dataset.chartPoint==='market'){state.marketMonth=month;renderMarket()}
  if(dot.dataset.chartPoint==='semen'){state.semenMonth=month;renderSemen()}
  if(dot.dataset.chartPoint==='quality'){
    const candidate=state.qualityMonth.slice(0,4)+'-'+String(month).padStart(2,'0');
    if(state.data.quality?.records?.some(r=>r.month===candidate)){state.qualityMonth=candidate;renderQuality()}
  }
 }
});
main.addEventListener('keydown',event=>{
 if((event.key==='Enter'||event.key===' ')&&event.target.matches('[data-chart-point]')){event.preventDefault();event.target.dispatchEvent(new MouseEvent('click',{bubbles:true}))}
});
main.addEventListener('change',event=>{
 if(event.target.id==='marketSex'){state.sex=event.target.value;renderMarket()}
 if(event.target.id==='qualityMonth'){state.qualityMonth=event.target.value;renderQuality()}
 if(event.target.id==='qualityMetric'){state.qualityMetric=event.target.value;renderQuality()}
});
const style=document.createElement('style');
style.textContent='.year-toggles{display:flex;gap:7px;flex-wrap:wrap;margin:0 0 13px}.year-toggles button{border:1px solid #e1e6df;background:white;border-radius:9px;min-height:36px;padding:7px 12px;font-size:11px;font-weight:800;color:#77877b}.year-toggles button:before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--year-color);margin-right:6px;vertical-align:middle}.year-toggles button[aria-pressed="true"]{color:#2d4940;border-color:#b5d0bf;background:#f2f7f1}.year-toggles button[aria-pressed="false"]{opacity:.48}.semen-hero{background:linear-gradient(135deg,#694c79,#49395c);box-shadow:0 12px 25px #59436925}.semen-hero:after{content:"♧"}.app-screen [data-chart-point]{cursor:pointer;outline:none}.app-screen [data-chart-point]:focus{stroke:#131f1b;stroke-width:3}';
document.head.append(style);
let showSheet=(heading,message)=>{$('#sheetTitle').textContent=heading;$('#sheetText').textContent=message;$('#appDialog').hidden=false;$('#sheetClose').focus()};
$('#sheetClose').addEventListener('click',()=>$('#appDialog').hidden=true);
$('#appDialog').addEventListener('click',e=>{if(e.target.id==='appDialog')$('#appDialog').hidden=true});
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('#appDialog').hidden=true});
window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event});
function installInfo(){
 const apple=/iPhone|iPad|iPod/i.test(navigator.userAgent);
 if(apple)showSheet('홈 화면에 설치','Safari 하단 공유 버튼을 누른 뒤 ‘홈 화면에 추가’ → ‘추가’를 선택하세요. 설치 후 앱 아이콘으로 실행할 수 있습니다.');
 else showSheet('홈 화면에 설치','브라우저 메뉴(⋮)에서 ‘앱 설치’ 또는 ‘홈 화면에 추가’를 선택하세요. 설치 후 앱 아이콘으로 실행할 수 있습니다.');
}
const installButton=document.createElement('button');installButton.className='icon-button';installButton.type='button';installButton.title='앱 설치 방법';installButton.setAttribute('aria-label','앱 설치 방법');installButton.textContent='＋';
$('.header-actions').prepend(installButton);
installButton.addEventListener('click',async()=>{
 if(installPrompt){
  const event=installPrompt;installPrompt=null;
  try{await event.prompt();await event.userChoice}catch(_){installInfo()}
 }else installInfo()
});
if(window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true)installButton.hidden=true;
if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('./service-worker.js',{scope:'./'}).catch(e=>console.warn('PWA offline:',e)))}
loadAll();
})();