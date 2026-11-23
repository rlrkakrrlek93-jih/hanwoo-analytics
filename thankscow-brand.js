/* thankscow identity for HANWOO INSIGHT · safe to re-run */
(()=>{'use strict';
const url='https://www.youtube.com/@thankscow';
const icon='<svg viewBox="0 0 32 32" aria-hidden="true" fill="none"><path d="M8 13C6 9 7 6 10 5l5 6M24 13c2-4 1-7-2-8l-5 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M9 12c3-3 11-3 14 0 4 4 3 13-2 16-3 2-7 2-10 0-5-3-6-12-2-16Z" stroke="currentColor" stroke-width="2"/><path d="M12 19h.1M20 19h.1" stroke="currentColor" stroke-width="3.3" stroke-linecap="round"/><path d="M12 23c2 2 6 2 8 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
function signature(cls=''){const a=document.createElement('a');a.className='tc-signature '+cls;a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('aria-label','제작 브랜드 thankscow');a.innerHTML='<span class="tc-emblem" aria-hidden="true">牛</span><span class="tc-sig-copy"><small>CREATED & CURATED BY</small><strong>thankscow</strong></span>';return a}
function watermark(node){if(!node||node.querySelector(':scope > .tc-watermark'))return;node.classList.add('tc-watermark-target');const mark=document.createElement('span');mark.className='tc-watermark';mark.setAttribute('aria-hidden','true');mark.innerHTML=icon+'<span>thankscow</span>';node.append(mark)}
function paint(){
 const header=document.querySelector('.top,.app-header');
 if(header&&!header.querySelector('.tc-topbrand')){const sig=signature('tc-topbrand');const mobile=header.classList.contains('app-header');(mobile?header.querySelector('.header-actions'):header)?.prepend(sig)}
 const hero=document.querySelector('.hero-row');
 if(hero&&!hero.querySelector('.tc-hero-stamp')){const p=document.createElement('div');p.className='tc-hero-stamp';p.textContent='HANWOO INSIGHT  /  by thankscow';(hero.firstElementChild||hero).append(p)}
 const main=document.querySelector('main,.app-main');
 if(main&&!main.querySelector('.tc-footer')){
  const f=document.createElement('footer');f.className='tc-footer';f.append(signature());
  const n=document.createElement('div');n.className='tc-note';n.innerHTML='<b>HANWOO INSIGHT by thankscow</b><div>© 2026 thankscow. All rights reserved.</div><div>원자료의 권리는 각 제공기관에 있으며, thankscow의 별도 가공·편집 및 시각화 구성은 해당 권리 범위에서 보호됩니다.</div>';f.append(n);main.append(f)
 }
 document.querySelectorAll('.chartbox,.market-chart,.chart-container,.semen-chart,.paper-card:has(canvas),.paper-card:has(svg),.panel:has(canvas),.overview-hero').forEach(watermark);
 document.querySelectorAll('.chartbox').forEach(box=>{if(box.querySelector('.tc-source'))return;const source=document.createElement('div');source.className='tc-source';source.innerHTML='공개 통계 기반 <b>· 시각화 thankscow</b> · 세부 출처는 각 데이터 설명 참조';box.append(source)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',paint,{once:true});else paint();
let pending=false;const schedule=()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;paint()})};
const start=()=>{const root=document.querySelector('main');if(root)new MutationObserver(schedule).observe(root,{childList:true,subtree:true})};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
