(function(){
'use strict';
const source='https://www.ekapepia.com/v3/price/livestock/cow/producer.do';
const regionSource='https://xn--e20bw05b.kr/dashboard/main';
const fmt=n=>new Intl.NumberFormat('ko-KR').format(n*1000)+'원';
const valid=r=>r&&r.region==='전국'&&/^20\d{2}-\d{2}-\d{2}$/.test(r.date)&&['male_6_7','female_6_7'].every(k=>Number.isFinite(r[k])&&r[k]>=500&&r[k]<=15000);
const safe=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const el=document.createElement('section');el.id='calfPrices';el.className='tc-calf-desktop';el.setAttribute('aria-label','한우 송아지 전국 평균가격');
el.innerHTML='<h2>한우 송아지 전국 평균가격</h2><p>공식 송아지 가격 불러오는 중…</p>';
const filter=document.querySelector('main .filterbox');if(filter)filter.insertAdjacentElement('afterend',el);else(document.querySelector('main')||document.body).prepend(el);
function trend(data){
 const rows=data.slice(-15);if(rows.length<2)return '<p class="tc-calf-muted">확인된 날짜가 쌓이면 가격 변화를 표시합니다.</p>';
 const l=60,r=670,t=26,b=155,w=720,h=195;
 const all=rows.flatMap(a=>[a.male_6_7,a.female_6_7]);const mn=Math.min(...all)-200,mx=Math.max(...all)+200;
 const X=i=>l+(r-l)*i/(rows.length-1),Y=v=>b-(v-mn)/(mx-mn)*(b-t);
 let str='';
 for(const [k,color] of [['male_6_7','#367d6c'],['female_6_7','#c27d5a']]){
  str+='<path fill="none" stroke="'+color+'" stroke-width="3" d="'+rows.map((a,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(a[k]).toFixed(1)).join(' ')+'"/>';
  str+=rows.map((a,i)=>'<circle cx="'+X(i)+'" cy="'+Y(a[k])+'" r="5" fill="white" stroke="'+color+'" stroke-width="3"><title>'+safe(a.date)+' '+safe(fmt(a[k]))+'</title></circle>').join('');
 }
 str+=rows.map((a,i)=>(i===0||i===rows.length-1||rows.length<=5)?'<text x="'+X(i)+'" y="184" text-anchor="middle" font-size="12" fill="#829388">'+safe(a.date.slice(5).replace('-','/'))+'</text>':'').join('');
 return '<svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="한우 6~7개월령 수송아지와 암송아지 확인일별 가격 추이">'+str+'</svg>';
}
function draw(data){
 const arr=(data?.records||[]).filter(valid).sort((a,b)=>a.date.localeCompare(b.date));const item=arr.at(-1);
 if(!item){el.innerHTML='<h2>한우 송아지 전국 평균가격</h2><p>공식 가격 확인 중입니다. <a href="'+source+'" target="_blank" rel="noopener noreferrer">공식 산지가격 페이지</a></p>';return}
 const month=(data.monthly_reference||[]).filter(x=>x.region==='전국'&&/^20\d{2}-\d{2}$/.test(x.month)&&Number.isFinite(x.male_6_7)&&Number.isFinite(x.female_6_7)).sort((a,b)=>a.month.localeCompare(b.month)).at(-1);
 el.innerHTML='<div class="tc-calf-head"><div><div class="tc-calf-eyebrow">CALF PRICE · OFFICIAL MARKET SURVEY</div><h2>한우 송아지 전국 평균가격</h2><p>6~7개월령 · 가축시장 조사 · 수송아지/암송아지</p></div><div class="tc-calf-date">확인 '+safe(item.date.replaceAll('-','.'))+'</div></div>'+
 '<div class="tc-calf-cards"><article><span>수송아지</span><strong>'+fmt(item.male_6_7)+'</strong><small>전국 · 6~7개월령</small></article><article class="female"><span>암송아지</span><strong>'+fmt(item.female_6_7)+'</strong><small>전국 · 6~7개월령</small></article></div>'+
 '<div class="tc-calf-lower"><div class="tc-calf-plot"><strong>확인일별 가격 흐름</strong><div class="tc-calf-legend"><span>● 수송아지</span><span>● 암송아지</span></div>'+trend(arr)+'</div>'+
 '<aside><strong>직전 공식 월평균</strong><p>'+(month?safe(month.month.replace('-','년 ')+'월'):'확인 중')+'</p><div>수송아지 <b>'+(month?fmt(month.male_6_7):'—')+'</b></div><div>암송아지 <b>'+(month?fmt(month.female_6_7):'—')+'</b></div><small>일별 최신 가격과 월평균은 서로 다른 집계기간입니다.</small></aside></div>'+
 '<div class="tc-calf-foot"><p>지역별은 전국 조사와 동일 기준의 검증된 집계가 아직 없어 임의 평균을 표시하지 않습니다.</p><div><a href="'+regionSource+'" target="_blank" rel="noopener noreferrer">지역 가축시장 확인</a><a href="'+source+'" target="_blank" rel="noopener noreferrer">공식 출처</a></div></div>';
}
fetch('./calf_price_data.json?v='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(draw).catch(()=>draw(null));
})();
