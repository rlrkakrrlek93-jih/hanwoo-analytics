/* thankscow identity for HANWOO INSIGHT · safe to re-run */
(()=>{'use strict';
const url='https://www.youtube.com/@thankscow';
const icon='<svg viewBox="0 0 32 32" aria-hidden="true" fill="none"><path d="M8 13C6 9 7 6 10 5l5 6M24 13c2-4 1-7-2-8l-5 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M9 12c3-3 11-3 14 0 4 4 3 13-2 16-3 2-7 2-10 0-5-3-6-12-2-16Z" stroke="currentColor" stroke-width="2"/><path d="M12 19h.1M20 19h.1" stroke="currentColor" stroke-width="3.3" stroke-linecap="round"/><path d="M12 23c2 2 6 2 8 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
function signature(cls=''){const a=document.createElement('a');a.className='tc-signature '+cls;a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('aria-label','제작 브랜드 thankscow');a.innerHTML='<span class="tc-emblem" aria-hidden="true">牛</span><span class="tc-sig-copy"><small>CREATED & CURATED BY</small><strong>thankscow</strong></span>';return a}
function watermark(node){if(!node||node.querySelector(':scope > .tc-watermark'))return;node.classList.add('tc-watermark-target');const mark=document.createElement('span');mark.className='tc-watermark';mark.setAttribute('aria-hidden','true');mark.innerHTML='<span class="tc-sprout" aria-hidden="true"><svg viewBox="0 0 34 30" fill="none"><path d="M17 28V16" stroke="#536846" stroke-width="3" stroke-linecap="round"/><path d="M16 15C8 16 3 10 4 4c7-1 13 3 12 11Z" fill="#75864F"/><path d="M18 16C19 7 25 3 32 3c1 8-4 13-14 13Z" fill="#657B46"/></svg></span><span class="tc-wordmark"><span>thanks</span><span>cow</span></span>';node.append(mark)}

function embedSvgWatermark(svg){
 if(svg.querySelector(':scope > .tc-svg-watermark'))return;
 const vb=svg.viewBox?.baseVal;
 if(!vb||vb.width<250||vb.height<100)return;
 const ns='http://www.w3.org/2000/svg';
 const group=document.createElementNS(ns,'g');
 group.setAttribute('class','tc-svg-watermark');
 group.setAttribute('aria-hidden','true');
 group.setAttribute('pointer-events','none');
 const large=vb.width>=650;
 const x=vb.x+vb.width*(large?.72:.57);
 const y=vb.y+vb.height*(large?.57:.64);
 const size=Math.min(large?43:24,Math.max(17,vb.width*.043));
 const label=document.createElementNS(ns,'text');
 label.setAttribute('x',String(x));label.setAttribute('y',String(y));
 label.setAttribute('font-size',String(size));
 label.setAttribute('font-family','Trebuchet MS, Arial Rounded MT Bold, system-ui, sans-serif');
 label.setAttribute('font-weight','900');label.setAttribute('text-anchor','middle');
 label.setAttribute('letter-spacing','-1');
 const a=document.createElementNS(ns,'tspan');a.setAttribute('fill','#50654b');a.textContent='thanks';
 const b=document.createElementNS(ns,'tspan');b.setAttribute('fill','#ad7859');b.textContent='cow';
 label.append(a,b);
 group.append(label);
 const sprout=document.createElementNS(ns,'path');
 const sx=x+size*.04,sy=y-size*1.12;
 sprout.setAttribute('d',`M ${sx} ${sy+size*.52} v -${size*.34} M ${sx} ${sy+size*.22} q -${size*.46} -${size*.39} -${size*.64} -${size*.06} q ${size*.15} ${size*.34} ${size*.64} ${size*.25} M ${sx} ${sy+size*.21} q ${size*.37} -${size*.44} ${size*.65} -${size*.21} q -${size*.17} ${size*.35} -${size*.65} ${size*.29}`);
 sprout.setAttribute('stroke','#71895b');sprout.setAttribute('fill','#71895b');
 sprout.setAttribute('stroke-width',String(size*.055));sprout.setAttribute('stroke-linejoin','round');
 group.append(sprout);
 svg.append(group);
}


// Decorative countryside artwork, inspired by thankscow's warm farm illustration.
function heroArtwork(){
 const hero=document.querySelector('.hero');
 if(!hero||hero.querySelector('.tc-pasture-art'))return;
 const wrap=document.createElement('div');
 wrap.className='tc-pasture-art';
 wrap.setAttribute('aria-hidden','true');
 wrap.innerHTML=`<svg viewBox="0 0 900 390" preserveAspectRatio="xMidYMax meet" xmlns="http://www.w3.org/2000/svg" role="presentation">
 <defs>
 <linearGradient id="tcSky" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#fff7ed"/><stop offset="1" stop-color="#f9e9d9"/></linearGradient>
 <linearGradient id="tcHill" x1="0" x2="1"><stop stop-color="#dda897"/><stop offset="1" stop-color="#b96759"/></linearGradient>
 </defs>
 <path d="M0 200Q140 170 270 219T580 204T900 189V390H0Z" fill="#f1d6c4" opacity=".68"/>
 <circle cx="764" cy="67" r="44" fill="#c65e4e" opacity=".74"/>
 <g fill="#f9ded2" opacity=".9"><path d="M110 98c-5-15 11-28 27-25 4-17 32-23 44-5 13-3 27 5 28 18 21-2 30 12 23 19H110Z"/><path d="M588 126c-8-12 5-26 19-23 6-16 31-16 39-4 20-5 30 9 29 22 22-1 26 12 20 17H588Z"/></g>
 <path d="M0 283C135 221 196 258 312 276S507 225 628 250S794 204 900 256V390H0Z" fill="url(#tcHill)" opacity=".58"/>
 <path d="M0 332C142 288 261 345 396 308S675 293 900 319V390H0Z" fill="#b6a581" opacity=".64"/>
 <path d="M0 362C190 332 280 359 442 341S734 332 900 358V390H0Z" fill="#739078" opacity=".54"/>
 <g stroke="#fdf3e5" stroke-width="6" stroke-linecap="round" opacity=".87"><path d="M0 311Q275 345 560 310T900 320" fill="none"/><path d="M0 338Q275 372 560 338T900 346" fill="none"/><path d="M61 307v57M153 313v52M247 322v49M346 322v49M448 320v50M548 311v50M650 307v52M754 308v54M853 314v51"/></g>
 <g transform="translate(634 161)" stroke="#905e50" stroke-width="3" stroke-linejoin="round"><path d="M-5 61L52 18l64 41v87H-5Z" fill="#f7e9d8"/><path d="M-16 62l68-55 74 55-9 8-65-48-60 48Z" fill="#a45342"/><rect x="68" y="85" width="28" height="61" rx="2" fill="#c49b7d"/><path d="M11 87h31v31H11Z" fill="#e0b79b"/><path d="M26 87v31M11 102h31" stroke="#fff0db" stroke-width="2"/><rect x="137" y="-31" width="22" height="157" rx="8" fill="#dec6b0"/><path d="M133-17q15-19 30 0" fill="#d2a69a"/></g>
 <g transform="translate(526 265)" stroke="#4b3a32" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
 <path d="M-32 32Q-52-5-17-27Q14-50 64-18Q89 6 73 49Z" fill="#fff8e9"/>
 <path d="M-18-22Q14-42 28-15Q9 7 35 27Q11 48-20 30Z" fill="#68574d"/>
 <path d="M-27-16q-36-26-39 0q-5 21 28 25M56-19q30-33 42-8q3 19-22 32" fill="#554038"/>
 <ellipse cx="23" cy="33" rx="36" ry="25" fill="#efc6ad"/>
 <ellipse cx="12" cy="33" rx="6" ry="8" fill="#aa7e6f"/><ellipse cx="36" cy="33" rx="6" ry="8" fill="#aa7e6f"/>
 <circle cx="-10" cy="-1" r="4" fill="#352a27"/><circle cx="52" cy="-3" r="4" fill="#352a27"/>
 <path d="M-18 51v14M63 48v16" stroke-width="10"/>
 </g>
 <g transform="translate(767 286)" stroke="#62483a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
 <path d="M-56 14q-8-61 54-66q70-1 72 64v34H-53Z" fill="#bb7953"/>
 <path d="M-42-23q-30-26-45-8q-6 17 31 29M48-25q32-25 47-9q11 17-27 35" fill="#b47b54"/>
 <ellipse cx="7" cy="17" rx="40" ry="27" fill="#e8b393"/>
 <ellipse cx="-6" cy="17" rx="6" ry="7" fill="#a56b57"/><ellipse cx="23" cy="17" rx="6" ry="7" fill="#a56b57"/>
 <circle cx="-22" cy="-11" r="4" fill="#463329"/><circle cx="41" cy="-11" r="4" fill="#463329"/>
 </g>
 <g fill="#718365" opacity=".87"><path d="M430 332q-23-25-23-52q25 1 27 39q8-46 38-53q9 30-31 67Z"/><path d="M875 349q-23-34-14-59q22 10 21 37q8-48 30-49v61Z"/></g>
 </svg>`;
 hero.append(wrap);
}

function paint(){
 heroArtwork();
 const header=document.querySelector('.top,.app-header');
 if(header&&!header.querySelector('.tc-topbrand')){const sig=signature('tc-topbrand');const mobile=header.classList.contains('app-header');(mobile?header.querySelector('.header-actions'):header)?.prepend(sig)}
 const hero=document.querySelector('.hero-row');
 if(hero&&!hero.querySelector('.tc-hero-stamp')){const p=document.createElement('div');p.className='tc-hero-stamp';p.textContent='HANWOO INSIGHT  /  by thankscow';(hero.firstElementChild||hero).append(p)}
 const main=document.querySelector('main,.app-main');
 if(main&&!main.querySelector('.tc-footer')){
  const f=document.createElement('footer');f.className='tc-footer';f.append(signature());
  const n=document.createElement('div');n.className='tc-note';n.innerHTML='<b>HANWOO INSIGHT by thankscow</b><div>© 2026 thankscow. All rights reserved.</div><div>원자료의 권리는 각 제공기관에 있으며, thankscow의 별도 가공·편집 및 시각화 구성은 해당 권리 범위에서 보호됩니다.</div>';f.append(n);main.append(f)
 }
 document.querySelectorAll('main svg.chart, main .chart-surface svg, main .mk-chartscroll svg, main .ss-scroll svg').forEach(embedSvgWatermark);
 document.querySelectorAll('.chartbox,.chart-surface,.market-chart,.chart-container,.semen-chart').forEach(node=>{node.querySelectorAll(':scope > .tc-watermark').forEach(w=>w.remove())});
 document.querySelectorAll('main canvas').forEach(el=>{const host=el.parentElement;watermark(host)});
 document.querySelectorAll('.chartbox').forEach(box=>{if(box.querySelector('.tc-source'))return;const source=document.createElement('div');source.className='tc-source';source.innerHTML='공개 통계 기반 <b>· 시각화 thankscow</b> · 세부 출처는 각 데이터 설명 참조';box.append(source)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',paint,{once:true});else paint();
let pending=false;const schedule=()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;paint()})};
const start=()=>{const root=document.querySelector('main');if(root)new MutationObserver(schedule).observe(root,{childList:true,subtree:true})};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
