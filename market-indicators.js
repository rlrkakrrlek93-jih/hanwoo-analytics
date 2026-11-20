/* Read-only market supply chart, three color-coded annual comparison bands. */
(()=>{'use strict';
const css="#marketScope{max-width:1440px;margin:26px auto;padding:0 32px;font-family:inherit;color:#243449}#marketScope *{box-sizing:border-box}#marketScope .mk-panel{background:white;border:1px solid #e5ebf2;border-radius:18px;padding:24px;box-shadow:0 7px 25px #0d2e4a06}#marketScope .mk-top{display:flex;justify-content:space-between;align-items:start;gap:16px;flex-wrap:wrap}#marketScope h2{margin:0 0 7px;font-size:22px}#marketScope .mk-sub{font-size:13px;line-height:1.7;color:#64778b;margin:0}#marketScope .mk-status{font-size:12px;background:#eff4f8;padding:7px 10px;border-radius:8px}#marketScope .mk-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}#marketScope .mk-card{padding:16px;background:#f6f9fc;border-radius:12px}#marketScope .mk-card small{display:block;font-size:12px;color:#687c91;margin-bottom:8px}#marketScope .mk-card strong{font-size:25px;letter-spacing:-.6px}#marketScope .mk-card em{font-style:normal;font-size:12px;color:#6b7f91;display:block;margin-top:6px}#marketScope .mk-legend{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:13px;margin:14px 0;color:#3e566c}#marketScope .mk-year{display:inline-flex;align-items:center;gap:7px;padding:7px 10px;border:1px solid #dce5ee;border-radius:9px;background:#f9fbfd;cursor:pointer;font-weight:700}#marketScope .mk-year input{accent-color:#365e91;cursor:pointer}#marketScope .mk-hint{font-size:12px;color:#728396}#marketScope .mk-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px}#marketScope .mk-chartscroll{width:100%;overflow-x:auto}#marketScope svg{display:block;width:100%;min-width:650px;height:auto;font-family:inherit}#marketScope .mk-note{background:#f6f8fb;border-left:3px solid #89b7cb;border-radius:0 8px 8px 0;padding:13px 16px;font-size:12px;line-height:1.8;color:#536b81;margin-top:16px}#marketScope .mk-footer{font-size:12px;color:#708196;line-height:1.8;margin-top:14px}#marketScope a{color:#176b9c}#marketScope .mk-semen{margin-top:16px;border-top:1px solid #e9eef4;padding-top:16px}#marketScope .mk-semen strong{font-size:14px}#marketScope .mk-error{color:#9b3c31;font-size:13px;padding:15px 0}#marketScope .mk-filter{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px;color:#536a80}#marketScope select{font:inherit;padding:7px 10px;border:1px solid #d2e0eb;border-radius:7px;background:#fff;color:#344a60}#marketScope .mk-table-wrap{overflow:auto;max-height:340px}#marketScope table{border-collapse:collapse;width:100%;font-size:12px;white-space:nowrap}#marketScope td,#marketScope th{padding:9px 12px;text-align:right;border-bottom:1px solid #eaf0f4}#marketScope th:first-child,#marketScope td:first-child{text-align:left}#marketScope th{background:#f5f8fb;position:sticky;top:0}@media(max-width:680px){#marketScope{padding:0 14px}#marketScope .mk-panel{padding:16px}#marketScope h2{font-size:19px}#marketScope .mk-card strong{font-size:21px}#marketScope .mk-cards{grid-template-columns:1fr}}";
const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);
const el=(tag,cl,txt)=>{const x=document.createElement(tag);if(cl)x.className=cl;if(txt!==undefined)x.textContent=txt;return x};
const section=el('section');section.id='marketScope';const card=el('div','mk-panel');section.append(card);
const head=el('div','mk-top'),titles=el('div'),updated=el('span','mk-status','공식 자료 확인 중');
titles.append(el('h2','','한우 사육·판정·경락가격 흐름'),el('p','mk-sub','1~12월을 가로축으로 고정하고 2024·2025·2026년을 서로 다른 색으로 겹쳐 비교합니다.'));
head.append(titles,updated);card.append(head);
const cards=el('div','mk-cards'),stock=el('div','mk-card'),flow=el('div','mk-card'),priceCard=el('div','mk-card');
stock.append(el('small','','전국 한우 전체 사육두수 (월말)'),el('strong','','—'),el('em','','축산물이력제 기준'));
flow.append(el('small','','한우 전체 판정두수 (해당 월)'),el('strong','','—'),el('em','','암·수·거세 포함'));
priceCard.append(el('small','','한우 거세우 경락단가 (원/kg)'),el('strong','','—'),el('em','','공식 성별 발표값'));
cards.append(stock,flow,priceCard);card.append(cards);
const legend=el('div','mk-legend');legend.setAttribute('aria-label','연도별 표시 여부');
const filter=el('div','mk-filter');filter.append(el('span','','경락가격 성별:'),el('span','','공식 발표값 기준'));
const select=el('select');for(const [value,label] of [['steer','거세우'],['female','암소'],['male','수소']]){const op=el('option','',label);op.value=value;select.append(op)}filter.insertBefore(select,filter.children[1]);
card.append(filter,legend);
const scroll=el('div','mk-chartscroll'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
svg.setAttribute('viewBox','0 0 980 570');svg.setAttribute('role','img');svg.setAttribute('aria-label','1~12월을 기준으로 2024~2026년 사육두수 판정두수 경락가격을 색으로 겹쳐 비교한 3단 그래프');scroll.append(svg);card.append(scroll);
card.append(el('div','mk-note','해석 주의: 각 연도 1~12월을 같은 가로축 위치에서 비교합니다. 사육두수는 월말 재고량, 판정두수는 해당 월 암·수·거세 총판정두수, 경락가격은 선택한 성별의 공식 경락단가(원/kg)입니다. 지표별로 세로축을 독립적으로 사용하고, 미발표 월은 0으로 표시하지 않습니다.'));
const semen=el('div','mk-semen');
semen.append(el('strong','','번식 선행지표 · 한우 정액 판매량'),el('p','mk-sub','농협경제지주 한우개량사업소의 지역별·월별 정액 판매량 자료가 공개되어 있고, 축산물품질평가원 2026년 11월부터 발간하는 월간 수급 동향 보고서에도 포함됩니다. 현재 자동 수집 가능한 원자료를 검증 중이므로 숫자를 임의로 표시하지 않습니다. 정액 판매량은 실제 인공수정 실시 횟수가 아닙니다.'));
const semenLink=el('a','','공식 정액 판매량 자료 안내');semenLink.href='https://www.data.go.kr/data/15147844/fileData.do';semenLink.target='_blank';semenLink.rel='noopener noreferrer';semen.append(semenLink);const semenReport=el('a','',' / 최신 공식 월간 수급 보고서 안내');semenReport.href='https://www.ekape.or.kr/board/view.do?boardInfoNo=0025&boardNo=1439&menuId=menu160301';semenReport.target='_blank';semenReport.rel='noopener noreferrer';semen.append(semenReport);card.append(semen);
const footer=el('div','mk-footer'),invLink=el('a','','사육두수 공식 원표'),gradingLink=el('a','','판정두수 공식 원표');
invLink.href='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323901_A100000011&conn_path=I2';
gradingLink.href='https://mtrace.go.kr/statHtml/statHtml.do?orgId=323&tblId=DT_323903_E1080008&conn_path=I2';
for(const a of [invLink,gradingLink]){a.target='_blank';a.rel='noopener noreferrer'}
footer.append('출처: 축산물품질평가원 · ',invLink,' / ',gradingLink,' · 공식 원자료를 별도로 대조한 수치입니다.');card.append(footer);
const q=document.querySelector('#hq'),f=document.querySelector('main .footer')||document.querySelector('footer');
if(q&&q.parentNode)q.parentNode.insertBefore(section,q);else if(f&&f.parentNode)f.parentNode.insertBefore(section,f);
else (document.querySelector('main')||document.body).append(section);
const nf=n=>Number(n).toLocaleString('ko-KR'),svgNode=(tag,attrs,text)=>{
 const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
 Object.entries(attrs||{}).forEach(([k,v])=>e.setAttribute(k,String(v)));
 if(text!==undefined)e.textContent=text;return e;};
const colors={'2024':'#2563eb','2025':'#e27b29','2026':'#0d9475'};
const overflowColors=['#8b5cf6','#b35a8c','#64748b','#db2777'];
let selectedYears=new Set();
const yearColor=(year,years)=>colors[year]||overflowColors[Math.max(0,years.indexOf(year)-3)%overflowColors.length];
function makeYearLegend(rows){
 const years=[...new Set(rows.map(r=>r.month.slice(0,4)))].sort();
 selectedYears=new Set(years);
 legend.replaceChildren(el('strong','','연도별 비교'));
 for(const year of years){
   const item=el('label','mk-year'),checkbox=el('input'),dot=el('span','mk-dot');
   checkbox.type='checkbox';checkbox.value=year;checkbox.checked=true;
   checkbox.setAttribute('aria-label',year+'년 표시');
   dot.style.background=yearColor(year,years);
   checkbox.addEventListener('change',()=>{
     if(checkbox.checked)selectedYears.add(year);else selectedYears.delete(year);
     draw(cachedRows);
   });
   item.append(checkbox,dot,document.createTextNode(year+'년'));legend.append(item);
 }
 legend.append(el('span','mk-hint','체크로 연도를 선택할 수 있어요.'));
}
function draw(rows){
 svg.replaceChildren();
 const a=rows.slice().sort((x,y)=>x.month.localeCompare(y.month));
 if(!a.length)return;
 const years=[...new Set(a.map(r=>r.month.slice(0,4)))].sort();
 const byYear=new Map(years.map(year=>[year,new Map(a.filter(r=>r.month.startsWith(year+'-'))
   .map(r=>[Number(r.month.slice(5)),r]))]));
 const x0=91,x1=909,monthX=month=>x0+(month-1)*(x1-x0)/11;
 const sex=select.value;
 const panels=[
  {key:'inventory_head',title:'사육두수',unit:'만 두',y0:54,y1:162,
    get:r=>r.inventory_head,div:10000},
  {key:'graded_head',title:'판정두수',unit:'천 두',y0:214,y1:322,
    get:r=>r.graded_head,div:1000},
  {key:'auction_price',title:'경락가격 ('+({steer:'거세우',female:'암소',male:'수소'}[sex])+')',unit:'원/kg',
    y0:375,y1:483,get:r=>r.auction_price_by_sex?.[sex],div:1}
 ];
 for(let month=1;month<=12;month++){
   const xx=monthX(month);
   svg.append(svgNode('line',{x1:xx,y1:42,x2:xx,y2:490,
     stroke:month===1?'#cad6e5':'#edf1f5','stroke-dasharray':month===1?'0':'3 5'}));
   svg.append(svgNode('text',{x:xx,y:517,'text-anchor':'middle','font-size':12,fill:'#52687d'},month+'월'));
 }
 for(const p of panels){
   svg.append(svgNode('text',{x:9,y:p.y0-20,fill:'#324760','font-size':14,'font-weight':700},p.title+' · '+p.unit));
   const vals=a.map(p.get).filter(Number.isFinite);
   if(!vals.length){
      svg.append(svgNode('text',{x:490,y:(p.y0+p.y1)/2,'text-anchor':'middle',fill:'#94a3b8'},'공식 가격 미확보'));
      continue;
   }
   const minVal=Math.min(...vals),maxVal=Math.max(...vals);
   const pad=Math.max((maxVal-minVal)*.13,maxVal*.035,1);
   const lower=Math.max(0,minVal-pad),upper=maxVal+pad;
   const yy=v=>p.y1-(v-lower)/(upper-lower)*(p.y1-p.y0);
   for(let k=0;k<=3;k++){
     const y=p.y1-(p.y1-p.y0)*k/3;
     svg.append(svgNode('line',{x1:x0,y1:y,x2:x1,y2:y,stroke:'#dfe7f0','stroke-dasharray':k?'4 5':'0'}));
     svg.append(svgNode('text',{x:x0-11,y:y+4,'text-anchor':'end','font-size':11,fill:'#667d91'},
       ((lower+(upper-lower)*k/3)/p.div).toLocaleString('ko-KR',{maximumFractionDigits:1})));
   }
   for(const year of years){
     if(!selectedYears.has(year))continue;
     const col=yearColor(year,years),byMonth=byYear.get(year);
     let d='',prevMonth=0,hasPoints=false;
     for(let month=1;month<=12;month++){
       const r=byMonth.get(month),v=r?p.get(r):null;
       if(!Number.isFinite(v))continue;
       d+=(hasPoints&&month===prevMonth+1?' L':' M')+
          monthX(month).toFixed(1)+' '+yy(v).toFixed(1);
       hasPoints=true;prevMonth=month;
       const dot=svgNode('circle',{cx:monthX(month),cy:yy(v),r:3.7,
         stroke:col,'stroke-width':2.2,fill:'#fff',
         'data-year':year,'data-month':month,'data-metric':p.key});
       dot.append(svgNode('title',{},year+'년 '+month+'월 · '+p.title+' '+
         Number(v).toLocaleString('ko-KR')+(p.key==='auction_price'?'원/kg':'두')));
       svg.append(dot);
     }
     if(hasPoints)svg.append(svgNode('path',{d:d.trim(),stroke:col,
       'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round',
       fill:'none','data-year':year,'data-metric':p.key}));
   }
 }
 const last=a.at(-1),yr=last.month.slice(0,4),mo=Number(last.month.slice(5));
 const note=mo<12?yr+'년은 '+mo+'월까지 발표 · 11~12월처럼 미발표 월은 빈칸으로 표시':
   '2024년부터 월별 공식 통계를 같은 1~12월 기준으로 비교';
 svg.append(svgNode('text',{x:500,y:548,'text-anchor':'middle','font-size':12,fill:'#73869a'},note));
 if(!selectedYears.size)svg.append(svgNode('text',{x:500,y:341,'text-anchor':'middle','font-size':17,fill:'#61758a'},'비교할 연도를 선택하세요.'));
}

let cachedRows=[];
function renderPrice(){
 if(!cachedRows.length)return;
 const type=select.value,label={steer:'거세우',female:'암소',male:'수소'}[type];
 priceCard.querySelector('small').textContent='한우 '+label+' 경락단가 (원/kg)';
 const last=cachedRows.at(-1),prev=cachedRows.at(-2),p=last.auction_price_by_sex?.[type],prior=prev?.auction_price_by_sex?.[type];
 priceCard.querySelector('strong').textContent=Number.isFinite(p)?p.toLocaleString('ko-KR')+'원/kg':'—';
 priceCard.querySelector('em').textContent=Number.isFinite(p)&&Number.isFinite(prior)?
   ((p-prior>=0?'+':'')+(p-prior).toLocaleString('ko-KR')+'원/kg · 전월 대비'):'원본에 발표된 가격이 없습니다';
 draw(cachedRows);
}
select.addEventListener('change',renderPrice);
const tableDetails=el('details','mk-note'),tableSummary=el('summary','','월별 3개 지표 전체 숫자 보기');
tableDetails.append(tableSummary);
const tableWrap=el('div','mk-table-wrap');tableDetails.append(tableWrap);
card.insertBefore(tableDetails,card.querySelector('.mk-semen'));
function renderTable(rows){
 tableWrap.replaceChildren();
 const t=el('table'),header=el('tr');
 for(const name of ['월','사육두수 (두)','판정두수 (두)','거세 경락단가 (원/kg)','암 경락단가 (원/kg)'])
   header.append(el('th','',name));
 t.append(header);
 for(const r of rows.slice().reverse()){
   const tr=el('tr');
   const p=r.auction_price_by_sex||{};
   for(const v of [r.month,r.inventory_head,r.graded_head,p.steer,p.female]){
     tr.append(el('td','',Number.isFinite(v)?v.toLocaleString('ko-KR'):v??'미발표'));
   }t.append(tr);
 }tableWrap.append(t);
}
fetch('market_supply_data.json?check='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(obj=>{
 if(!Array.isArray(obj.records)||!obj.records.length)throw Error('저장된 공식 월별 데이터 없음');
 const rows=obj.records.filter(v=>Number.isInteger(v.inventory_head)&&Number.isInteger(v.graded_head))
   .sort((a,b)=>a.month.localeCompare(b.month));
 if(!rows.length)throw Error('유효한 공식 월별 데이터 없음');
 cachedRows=rows;
 makeYearLegend(rows);
 const last=rows.at(-1),prev=rows.length>1?rows.at(-2):null;
 updated.textContent='기간 '+rows[0].month+' ~ '+last.month+' · 갱신 '+(obj.last_success_kst||'미확인');
 stock.querySelector('strong').textContent=nf(last.inventory_head)+'두';
 flow.querySelector('strong').textContent=nf(last.graded_head)+'두';
 const delta=k=>prev?(last[k]-prev[k]>=0?'+':'')+nf(last[k]-prev[k])+'두 · 전월 대비':'공식 자료 1개월';
 stock.querySelector('em').textContent=delta('inventory_head');
 flow.querySelector('em').textContent=delta('graded_head');
 renderPrice();renderTable(rows);
}).catch(e=>{
 updated.textContent='공식 수집 확인 필요';svg.replaceChildren();
 svg.append(svgNode('text',{x:490,y:200,'text-anchor':'middle',fill:'#9b3c31'},'월별 공식 자료를 불러오지 못했습니다'));
 scroll.append(el('p','mk-error','자료 연결 오류: '+e.message+' · 추정값은 표시하지 않습니다.'));
});
})();