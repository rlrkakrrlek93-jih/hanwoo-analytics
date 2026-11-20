/* Read-only market supply chart, two independent y-axes (stock vs monthly flow). */
(()=>{'use strict';
const css="#marketScope{max-width:1440px;margin:26px auto;padding:0 32px;font-family:inherit;color:#243449}#marketScope *{box-sizing:border-box}#marketScope .mk-panel{background:white;border:1px solid #e5ebf2;border-radius:18px;padding:24px;box-shadow:0 7px 25px #0d2e4a06}#marketScope .mk-top{display:flex;justify-content:space-between;align-items:start;gap:16px;flex-wrap:wrap}#marketScope h2{margin:0 0 7px;font-size:22px}#marketScope .mk-sub{font-size:13px;line-height:1.7;color:#64778b;margin:0}#marketScope .mk-status{font-size:12px;background:#eff4f8;padding:7px 10px;border-radius:8px}#marketScope .mk-cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0}#marketScope .mk-card{padding:16px;background:#f6f9fc;border-radius:12px}#marketScope .mk-card small{display:block;font-size:12px;color:#687c91;margin-bottom:8px}#marketScope .mk-card strong{font-size:25px;letter-spacing:-.6px}#marketScope .mk-card em{font-style:normal;font-size:12px;color:#6b7f91;display:block;margin-top:6px}#marketScope .mk-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;margin:14px 0;color:#3e566c}#marketScope .mk-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px}#marketScope .mk-chartscroll{width:100%;overflow-x:auto}#marketScope svg{display:block;width:100%;min-width:650px;height:auto;font-family:inherit}#marketScope .mk-note{background:#f6f8fb;border-left:3px solid #89b7cb;border-radius:0 8px 8px 0;padding:13px 16px;font-size:12px;line-height:1.8;color:#536b81;margin-top:16px}#marketScope .mk-footer{font-size:12px;color:#708196;line-height:1.8;margin-top:14px}#marketScope a{color:#176b9c}#marketScope .mk-semen{margin-top:16px;border-top:1px solid #e9eef4;padding-top:16px}#marketScope .mk-semen strong{font-size:14px}#marketScope .mk-error{color:#9b3c31;font-size:13px;padding:15px 0}@media(max-width:680px){#marketScope{padding:0 14px}#marketScope .mk-panel{padding:16px}#marketScope h2{font-size:19px}#marketScope .mk-card strong{font-size:21px}}";
const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);
const el=(tag,cl,txt)=>{const x=document.createElement(tag);if(cl)x.className=cl;if(txt!==undefined)x.textContent=txt;return x};
const section=el('section');section.id='marketScope';const card=el('div','mk-panel');section.append(card);
const head=el('div','mk-top'),titles=el('div'),updated=el('span','mk-status','공식 자료 확인 중');
titles.append(el('h2','','한우 사육·판정 수급 흐름'),el('p','mk-sub','전국 월별 한우 전체 사육두수와 도체 판정두수를 한 그래프에서 비교합니다.'));
head.append(titles,updated);card.append(head);
const cards=el('div','mk-cards'),stock=el('div','mk-card'),flow=el('div','mk-card');
stock.append(el('small','','전국 한우 전체 사육두수 (월말)'),el('strong','','—'),el('em','','축산물이력제 기준'));
flow.append(el('small','','한우 전체 판정두수 (해당 월)'),el('strong','','—'),el('em','','암·수·거세 포함'));
cards.append(stock,flow);card.append(cards);
const legend=el('div','mk-legend');
for(const [color,label] of [['#197aa4','사육두수 (왼쪽 축 · 만 두)'],['#dc8044','판정두수 (오른쪽 축 · 천 두)']]){
 const item=el('span'),dot=el('span','mk-dot');dot.style.background=color;item.append(dot,document.createTextNode(label));legend.append(item);}
card.append(legend);
const scroll=el('div','mk-chartscroll'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
svg.setAttribute('viewBox','0 0 980 345');svg.setAttribute('role','img');svg.setAttribute('aria-label','월별 한우 사육두수와 판정두수 이중축 그래프');scroll.append(svg);card.append(scroll);
card.append(el('div','mk-note','해석 주의: 사육두수는 월말에 사육 중인 소의 재고량이고, 판정두수는 해당 월 도체 등급판정 마릿수입니다. 단위와 규모가 달라 좌측·우측 축을 따로 사용하며, 두 선의 높이를 직접 비교하면 안 됩니다.'));
const semen=el('div','mk-semen');
semen.append(el('strong','','번식 선행지표 · 한우 정액 판매량'),el('p','mk-sub','농협경제지주 한우개량사업소의 지역별·월별 정액 판매량 자료가 공공데이터로 등록되어 있지만 제공 페이지에 오류가 발생해 아직 검증된 수치를 연결하지 못했습니다. 정액 판매량은 실제 인공수정 횟수가 아닙니다.'));
const semenLink=el('a','','공식 정액 판매량 자료 안내');semenLink.href='https://www.data.go.kr/data/15147844/fileData.do';semenLink.target='_blank';semenLink.rel='noopener noreferrer';semen.append(semenLink);card.append(semen);
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
function draw(rows){
 svg.replaceChildren();const a=rows.slice().sort((x,y)=>x.month.localeCompare(y.month));if(!a.length)return;
 const n=a.length,x0=85,x1=875,y0=42,y1=275,x=i=>n===1?480:x0+i*(x1-x0)/(n-1);
 const maxI=Math.ceil(Math.max(...a.map(v=>v.inventory_head))/200000)*200000;
 const minI=Math.max(0,Math.floor(Math.min(...a.map(v=>v.inventory_head))*.93/200000)*200000);
 const maxG=Math.max(20000,Math.ceil(Math.max(...a.map(v=>v.graded_head))/20000)*20000);
 const yI=v=>y1-(v-minI)/(maxI-minI||1)*(y1-y0),yG=v=>y1-v/maxG*(y1-y0);
 for(let i=0;i<=4;i++){const y=y1-(y1-y0)*i/4;
  svg.append(svgNode('line',{x1:x0,y1:y,x2:x1,y2:y,stroke:'#e7edf3','stroke-dasharray':i===0?'0':'4 5'}));
  svg.append(svgNode('text',{x:x0-12,y:y+4,'text-anchor':'end',fill:'#4183a4','font-size':12},((minI+(maxI-minI)*i/4)/10000).toFixed(0)));
  svg.append(svgNode('text',{x:x1+12,y:y+4,'text-anchor':'start',fill:'#be7047','font-size':12},(maxG*i/4000).toFixed(0)));
 }
 svg.append(svgNode('text',{x:7,y:19,fill:'#4183a4','font-size':12},'만 두'));
 svg.append(svgNode('text',{x:916,y:19,fill:'#be7047','font-size':12},'천 두'));
 for(const [key,Y,color] of [['inventory_head',yI,'#197aa4'],['graded_head',yG,'#dc8044']]){
  const points=a.map((v,i)=>[x(i),Y(v[key])]);
  const d=points.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  svg.append(svgNode('path',{d,stroke:color,'stroke-width':3.2,'stroke-linejoin':'round','stroke-linecap':'round',fill:'none'}));
  points.forEach((p,i)=>{const c=svgNode('circle',{cx:p[0],cy:p[1],r:4.6,fill:'#fff',stroke:color,'stroke-width':2.6});
    c.append(svgNode('title',{},a[i].month+' · '+(key==='inventory_head'?'월말 사육':'월중 판정')+' '+nf(a[i][key])+'두'));svg.append(c);});
 }
 a.forEach((v,i)=>{if(n>17&&i%2)return;svg.append(svgNode('text',{x:x(i),y:302,'text-anchor':'middle',fill:'#64778b','font-size':11},v.month.slice(2).replace('-','/')));});
 svg.append(svgNode('text',{x:480,y:331,'text-anchor':'middle',fill:'#8995a2','font-size':11},'월별 공식 자료 · 좌우 축 단위 주의'));
}
fetch('market_supply_data.json?check='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(obj=>{
 if(!Array.isArray(obj.records)||!obj.records.length)throw Error('저장된 공식 월별 데이터 없음');
 const rows=obj.records.filter(v=>Number.isInteger(v.inventory_head)&&Number.isInteger(v.graded_head)).sort((a,b)=>a.month.localeCompare(b.month));
 if(!rows.length)throw Error('유효한 공식 월별 데이터 없음');
 const last=rows.at(-1),prev=rows.length>1?rows.at(-2):null;
 updated.textContent='최신 '+last.month+' · 갱신 '+(obj.last_success_kst||'미확인');
 stock.querySelector('strong').textContent=nf(last.inventory_head)+'두';
 flow.querySelector('strong').textContent=nf(last.graded_head)+'두';
 const delta=k=>prev?(last[k]-prev[k]>=0?'+':'')+nf(last[k]-prev[k])+'두 · 전월 대비':'공식 자료 1개월';
 stock.querySelector('em').textContent=delta('inventory_head');
 flow.querySelector('em').textContent=delta('graded_head');
 draw(rows);
}).catch(e=>{updated.textContent='공식 수집 확인 필요';svg.replaceChildren();svg.append(svgNode('text',{x:480,y:160,'text-anchor':'middle',fill:'#9b3c31'},'월별 공식 자료를 불러오지 못했습니다'));scroll.append(el('p','mk-error','자료 연결 오류: '+e.message+' · 추정값은 표시하지 않습니다.'));});
})();