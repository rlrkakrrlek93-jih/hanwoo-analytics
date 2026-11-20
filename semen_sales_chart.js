/* Hanwoo semen sales: official publication values, thousand STR; not usage count. */
(()=>{'use strict';
const C={'2022':'#7c3aed','2023':'#d64b66','2024':'#2563eb','2025':'#e27b29','2026':'#0d9475'},F=['#8b5cf6','#64748b'];
const css="#semenSalesScope{max-width:1440px;margin:24px auto;padding:0 32px;color:#243449}#semenSalesScope *{box-sizing:border-box}#semenSalesScope .ss-pane{padding:24px;border:1px solid #e2e9f0;background:white;border-radius:18px;box-shadow:0 7px 25px #0d2e4a06}#semenSalesScope h2{font-size:22px;letter-spacing:-.5px;margin:0 0 10px}#semenSalesScope p{font-size:13px;line-height:1.75;color:#5c7185;margin:7px 0}#semenSalesScope .ss-badges{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}#semenSalesScope .ss-year{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border:1px solid #dce5ed;background:#f8fafc;border-radius:10px;cursor:pointer;font-size:13px;font-weight:700}#semenSalesScope .ss-year input{cursor:pointer}#semenSalesScope .ss-dot{width:10px;height:10px;border-radius:50%;display:inline-block}#semenSalesScope .ss-scroll{overflow-x:auto}#semenSalesScope svg{min-width:620px;width:100%;height:auto;display:block}#semenSalesScope .ss-meta{font-size:12px;color:#697d90;margin:10px 0}#semenSalesScope .ss-note{padding:12px 15px;background:#f4f7fa;border-left:3px solid #8da8c2;border-radius:4px;line-height:1.8;font-size:12px;color:#526579}#semenSalesScope .ss-table{overflow:auto;max-height:280px;margin-top:10px}#semenSalesScope table{width:100%;border-collapse:collapse;font-size:12px}#semenSalesScope th,#semenSalesScope td{padding:8px 12px;text-align:right;border-bottom:1px solid #e7eef4;white-space:nowrap}#semenSalesScope th:first-child,#semenSalesScope td:first-child{text-align:left}#semenSalesScope th{position:sticky;top:0;background:#f6f9fc}#semenSalesScope a{color:#176b9c}#semenSalesScope details summary{cursor:pointer;margin-top:13px;font-weight:700;font-size:13px}@media(max-width:680px){#semenSalesScope{padding:0 14px}#semenSalesScope .ss-pane{padding:16px}#semenSalesScope h2{font-size:19px}}";
const style=document.createElement('style');style.textContent=css;document.head.append(style);
const e=(tag,txt,cls)=>{const n=document.createElement(tag);if(txt!=null)n.textContent=txt;if(cls)n.className=cls;return n};
const section=e('section');section.id='semenSalesScope';const card=e('div',null,'ss-pane');section.append(card);
const head=e('h2','한우 정액 판매량 · 연도별 월간 비교');card.append(head);
card.append(e('p','2022년부터 1~12월을 같은 위치에 놓고 연도별 한우 정액 판매량(천 스트로)을 비교합니다. 실제 인공수정 사용 횟수와는 다른 지표입니다.'));
const label=e('div',null,'ss-badges');card.append(label);
const description=e('p','자료 확인 중…','ss-meta');card.append(description);
const container=e('div',null,'ss-scroll'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 970 388');svg.setAttribute('role','img');svg.setAttribute('aria-label','1월부터 12월까지 한우 정액 판매량의 연도별 비교');container.append(svg);card.append(container);
const message=e('div','단위: 천 str(천 스트로). 2022~2024년의 매월 판매량을 공식 보고서 발표값 그대로 표시합니다. 2022년 공식 연간 합계는 2,281천 str이지만 월별 반올림 값의 합은 2,286천 str로 5천 str 차이가 있습니다. 2025년 6월 이후와 2026년의 미확인 월은 0으로 간주하지 않고 빈칸 처리합니다. 판매량은 실제 인공수정 사용량과 다릅니다.','ss-note');card.append(message);
const details=e('details'),sum=e('summary','월별 공식 수치와 출처 보기');details.append(sum);
const tablediv=e('div',null,'ss-table');details.append(tablediv);card.append(details);
const link=e('a','원본 자료: 전국한우협회 월별 한우 동향 분석');
link.href='https://www.ihanwoo.org/board/sub4?Ncode=publication&code=3&tabsNum=3';link.target='_blank';link.rel='noopener noreferrer';
const foot=e('p');foot.append('원자료 제공: 농협경제지주 한우개량사업소 · ',link);card.append(foot);
const market=document.querySelector('#marketScope');
if(market&&market.parentNode)market.insertAdjacentElement('afterend',section);
else(document.querySelector('main')||document.body).append(section);
const svgEl=(tag,attrs,txt)=>{const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs||{}))el.setAttribute(k,String(v));if(txt!==undefined)el.textContent=txt;return el};
let rows=[],years=[],selected=new Set(),latestText='';
function render(){
 svg.replaceChildren();
 const max=Math.max(250,...rows.map(x=>x.sold_thousand_str))*1.12;
 const x0=85,x1=920,top=38,bottom=300,x=m=>x0+(m-1)*(x1-x0)/11,y=v=>bottom-v/max*(bottom-top);
 for(let m=1;m<=12;m++){
   const xx=x(m);svg.append(svgEl('line',{x1:xx,y1:top,x2:xx,y2:bottom,stroke:'#e9eef4','stroke-dasharray':'3 5'}));
   svg.append(svgEl('text',{x:xx,y:332,'text-anchor':'middle',fill:'#60768b','font-size':12},m+'월'));
 }
 for(let i=0;i<=5;i++){
   const value=max*i/5,yy=y(value);
   svg.append(svgEl('line',{x1:x0,y1:yy,x2:x1,y2:yy,stroke:'#e2eaf1'}));
   svg.append(svgEl('text',{x:x0-12,y:yy+4,'text-anchor':'end','font-size':12,fill:'#5b7083'},value.toFixed(0)));
 }
 svg.append(svgEl('text',{x:8,y:16,'font-size':12,fill:'#5b7083'},'천 str'));
 for(const year of years){
  if(!selected.has(year))continue;
  const col=C[year]||F[years.indexOf(year)%F.length],mine=rows.filter(r=>r.month.startsWith(year+'-'));
  const vals=new Map(mine.map(r=>[Number(r.month.slice(5)),r]));
  let d='',last=0;
  for(let m=1;m<=12;m++){
    const r=vals.get(m);if(!r)continue;
    d+=(last>0&&last===m-1?' L':' M')+x(m).toFixed(1)+' '+y(r.sold_thousand_str).toFixed(1);last=m;
  }
  if(!mine.length)continue;
  const path=svgEl('path',{d:d.trim(),stroke:col,'stroke-width':3.5,'stroke-linecap':'round','stroke-linejoin':'round',fill:'none','data-year':year});
  svg.append(path);
  for(const r of mine){
    const m=Number(r.month.slice(5));
    const dot=svgEl('circle',{cx:x(m),cy:y(r.sold_thousand_str),r:4.5,fill:'#fff',stroke:col,'stroke-width':2.4,'data-year':year,'data-month':m});
    dot.append(svgEl('title',{},year+'년 '+m+'월: '+r.sold_thousand_str.toLocaleString('ko-KR')+'천 str (보고서 공표값)'));
    svg.append(dot);
  }
 }
 svg.append(svgEl('text',{x:500,y:364,'text-anchor':'middle','font-size':12,fill:'#75879b'},'2022~2026년 공식 발표된 판매량만 표시 · 확인되지 않은 월은 공백'));
}
function table(){
 tablediv.replaceChildren();const t=e('table'),thead=e('tr');
 for(const title of ['월',...years.map(y=>y+'년 · 천 str')])thead.append(e('th',title));t.append(thead);
 for(let mo=1;mo<=12;mo++){
  const tr=e('tr');tr.append(e('td',mo+'월'));
  for(const y of years){const r=rows.find(x=>x.month===y+'-'+String(mo).padStart(2,'0'));const c=e('td',r?r.sold_thousand_str.toLocaleString('ko-KR'):'미확인');if(r){const a=e('a',c.textContent);a.href=r.source_url;a.target='_blank';a.rel='noopener noreferrer';c.replaceChildren(a);}tr.append(c)}
  t.append(tr);
 }tablediv.append(t);
}
fetch('semen_sales_data.json?t='+Date.now(),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(obj=>{
 if(!Array.isArray(obj.records))throw Error('공식 수집자료 형식 불일치');
 rows=obj.records.filter(x=>/^(202[2-9])-(0[1-9]|1[0-2])$/.test(x.month)&&Number.isInteger(x.sold_thousand_str)&&x.sold_thousand_str>0).sort((a,b)=>a.month.localeCompare(b.month));
 const known=[...new Set(rows.map(x=>x.month.slice(0,4)))];
 years=[...new Set(['2022','2023','2024','2025','2026',...known])].sort();selected=new Set(years);
 label.replaceChildren();
 for(const year of years){
   const item=e('label',null,'ss-year'),input=e('input'),circle=e('span',null,'ss-dot');
   input.type='checkbox';input.checked=true;circle.style.background=C[year]||F[years.indexOf(year)%F.length];
   input.addEventListener('change',()=>{if(input.checked)selected.add(year);else selected.delete(year);render()});
   item.append(input,circle,document.createTextNode(year+'년'+(rows.some(r=>r.month.startsWith(year))?'':' (미확인)')));label.append(item);
 }
 description.textContent='검증된 '+rows.length+'개월 · 최근 확인 월 '+(rows.at(-1)?.month||'없음')+' · 2022~2024년 전월 확보, 2025년 일부 월 확인';
 render();table();
}).catch(err=>{description.textContent='판매량 통계 수신 실패: '+err.message;svg.replaceChildren()});
})();