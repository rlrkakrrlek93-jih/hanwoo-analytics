/* Shared 2024–2026 historical nationwide Hanwoo calf monthly chart.
   Monthly rows are a third-party aggregation of original eKAPEpia daily auction prices.
   Never mix official day prices or separate official reference monthly prices into this series.
*/
(function(){
'use strict';
const YEARS=[2024,2025,2026], COLORS={2024:'#487ab5',2025:'#d18a4a',2026:'#248677'};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KR=n=>Number(n).toLocaleString('ko-KR',{maximumFractionDigits:1,minimumFractionDigits:1});
const monthOf=m=>Number(m.slice(-2));
function valid(d){
 const all=Array.isArray(d?.monthly_series)?d.monthly_series:[];
 const items=all.filter(r=>/^202[456]-(0[1-9]|1[0-2])$/.test(r.month||'')&&r.region==='전국'
  &&Number.isFinite(r.male_6_7)&&Number.isFinite(r.female_6_7)&&r.male_6_7>500&&r.female_6_7>500);
 return items.sort((a,b)=>a.month.localeCompare(b.month));
}
function percent(a,b){return b?((a-b)/b*100):null;}
function render(data,sex='male',compact=false){
 const rows=valid(data),key=sex==='female'?'female_6_7':'male_6_7';
 if(!rows.length)return '<div class="calf-history-empty">2024~2026년 월별 송아지 가격 데이터를 확인하는 중입니다.</div>';
 const selected=rows.filter(r=>r.month.startsWith('2026-')).at(-1)||rows.at(-1);
 const previous=rows.find(r=>r.month===selected.month.slice(0,4)+'-'+String(monthOf(selected.month)-1).padStart(2,'0'));
 const val=selected[key],prior=previous?.[key],delta=Number.isFinite(prior)?val-prior:null,chg=percent(val,prior);
 const change=delta==null?'비교 자료 없음':(delta>0?'▲ 상승':delta<0?'▼ 하락':'→ 보합')+' '+(delta>0?'+':'')+KR(delta/10)+'만원 ('+(chg>0?'+':'')+KR(chg)+'%)';
 const changeClass=delta==null?'':delta>0?'rising':delta<0?'falling':'stable';
 const all=rows.map(r=>r[key]),min=Math.floor((Math.min(...all)-220)/100)*100,max=Math.ceil((Math.max(...all)+220)/100)*100;
 const w=1030,h=350,l=91,right=970,top=42,bottom=285;
 const X=m=>l+(m-1)*(right-l)/11;
 const Y=v=>bottom-(v-min)/(max-min)*(bottom-top);
 const series=YEARS.map(y=>({year:y,items:rows.filter(r=>r.month.startsWith(String(y))).map(r=>({month:monthOf(r.month),price:r[key]}))}));
 const grid=[0,1,2,3,4].map(i=>{const py=top+i*(bottom-top)/4,v=max-i*(max-min)/4;return '<path d="M'+l+' '+py+'H'+right+'" stroke="#e8eae6" stroke-width="1"/><text x="'+(l-16)+'" y="'+(py+4)+'" text-anchor="end" font-size="11" fill="#92a099">'+Math.round(v/10)+'</text>';}).join('');
 const dates=Array.from({length:12},(_,i)=>'<text x="'+X(i+1)+'" y="328" text-anchor="middle" font-size="13" fill="#75887e">'+(i+1)+'월</text>').join('');
 const paths=series.map(s=>{
  let d='';
  s.items.forEach((v,i)=>{d+=(i?' L':'M')+X(v.month).toFixed(1)+' '+Y(v.price).toFixed(1)});
  const color=COLORS[s.year],width=s.year===2026?4:2.7;
  return '<path d="'+d+'" stroke="'+color+'" stroke-width="'+width+'" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'+
   s.items.map(v=>'<circle cx="'+X(v.month).toFixed(1)+'" cy="'+Y(v.price).toFixed(1)+'" r="'+(s.year===2026?5.3:4.3)+'" stroke="'+color+'" stroke-width="2.3" fill="#fff"><title>'+s.year+'년 '+v.month+'월 '+KR(v.price/10)+'만원</title></circle>').join('');
 }).join('');
 // Avoid overlapping value labels across years at the same month.
 // Resolve collisions vertically, while preserving line positions and original values.
 let leaders='',labels='';
 for(let m=1;m<=12;m++){
  const points=series.flatMap(s=>s.items.filter(v=>v.month===m).map(v=>({year:s.year,price:v.price,y:Y(v.price),want:Y(v.price)-12}))).sort((a,b)=>a.want-b.want);
  const gap=18,low=23,high=306;
  points.forEach((p,i)=>{p.label=Math.max(low+i*gap,Math.min(p.want,high-(points.length-i-1)*gap));if(i>0)p.label=Math.max(p.label,points[i-1].label+gap)});
  let over=points.length&&points.at(-1).label-high;
  if(over>0)points.forEach(p=>p.label-=over);
  points.forEach(p=>{
   const xx=X(m),c=COLORS[p.year];
   if(Math.abs(p.label-(p.y-12))>11)leaders+='<path d="M'+xx+' '+(p.y-4).toFixed(1)+'L'+xx+' '+(p.label+3).toFixed(1)+'" stroke="'+c+'" stroke-opacity=".34" stroke-width="1"/>';
   labels+='<text x="'+xx+'" y="'+p.label.toFixed(1)+'" font-size="12" font-weight="'+(p.year===2026?850:720)+'" fill="'+c+'" text-anchor="middle" stroke="white" stroke-width="3" stroke-linejoin="round" paint-order="stroke">'+KR(p.price/10)+'</text>';
  });
 }
 const legend=series.map(s=>'<span class="calf-legend-year"><i style="background:'+COLORS[s.year]+'"></i>'+s.year+'년</span>').join('');
 const monthTable=Array.from({length:12},(_,i)=>{
  const month=i+1,td=YEARS.map(y=>{const row=rows.find(r=>r.month===y+'-'+String(month).padStart(2,'0'));return '<td class="'+(y===2026?'is-current':'')+'">'+(row?KR(row[key]/10):'—')+'</td>';}).join('');
  return '<tr><th>'+month+'월</th>'+td+'</tr>';
 }).join('');
 const sexName=sex==='female'?'암송아지':'수송아지';
 return '<div class="calf-history-wrap '+(compact?'is-compact':'')+'">'+
  '<div class="calf-history-top"><div><strong>'+sexName+' · 2024~2026 월별 가격</strong><small>6~7개월령 · 전국 · 만원/마리</small></div><div class="calf-history-move '+changeClass+'"><span>'+selected.month.replace('-','년 ')+'월</span><b>'+KR(val/10)+'만원</b><small>전월 대비 '+change+'</small></div></div>'+
  '<div class="calf-history-legend">'+legend+'</div>'+
  '<div class="calf-history-scroll"><div class="calf-history-canvas"><svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+sexName+' 2024년부터 2026년 월별 가격 비교 그래프. 각 점에 만원 단위 값 표시">'+
  grid+paths+leaders+labels+dates+'</svg></div></div>'+
  (compact?'<p class="calf-history-swipe">숫자가 겹치지 않도록 가로로 밀어 확인할 수 있어요.</p>':'')+
  '<details class="calf-history-data"><summary>월별 정확한 수치표 펼치기</summary><div class="calf-history-table-scroll"><table><thead><tr><th>월</th>'+YEARS.map(y=>'<th>'+y+'년</th>').join('')+'</tr></thead><tbody>'+monthTable+'</tbody></table></div></details>'+
  '<p class="calf-history-source">월별 값: <a href="https://agropick.martius.kr/indicator/calf-'+(sex==='female'?'female':'male')+'" target="_blank" rel="noopener noreferrer">아그로픽 월평균 재집계</a> · 원자료: <a href="https://www.ekapepia.com/v3/price/livestock/cow/producer.do" target="_blank" rel="noopener noreferrer">축산유통정보 다봄</a>. 공식 산지가격 화면의 전월 평균과 집계방식에 따라 다를 수 있습니다. 미발표 월은 연결하지 않습니다.</p>'+
 '</div>';
}
window.HanwooCalfChart=Object.freeze({render,valid});
})();
