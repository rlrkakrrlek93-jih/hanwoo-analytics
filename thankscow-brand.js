/* thankscow identity for HANWOO INSIGHT · safe to re-run */
(()=>{'use strict';
// Brand credit stays on-site until the owner specifies an official brand URL.
const icon='<svg viewBox="0 0 32 32" aria-hidden="true" fill="none"><path d="M8 13C6 9 7 6 10 5l5 6M24 13c2-4 1-7-2-8l-5 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M9 12c3-3 11-3 14 0 4 4 3 13-2 16-3 2-7 2-10 0-5-3-6-12-2-16Z" stroke="currentColor" stroke-width="2"/><path d="M12 19h.1M20 19h.1" stroke="currentColor" stroke-width="3.3" stroke-linecap="round"/><path d="M12 23c2 2 6 2 8 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
function signature(cls=''){const a=document.createElement('span');a.className='tc-signature '+cls;a.setAttribute('aria-label','제작 브랜드 thankscow');a.innerHTML='<span class="tc-emblem" aria-hidden="true">牛</span><span class="tc-sig-copy"><small>CREATED & CURATED BY</small><strong>thankscow</strong></span>';return a}
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
 const hero=document.querySelector('.hero')||document.querySelector('#home');
 if(!hero||hero.querySelector('.tc-pasture-art'))return;
 const mobile=hero.id==='home';
 const wrap=document.createElement('div');
 wrap.className=mobile?'tc-pasture-art tc-data-center-art tc-mobile-studio':'tc-pasture-art tc-data-center-art';
 wrap.setAttribute('aria-hidden','true');
 wrap.innerHTML=`<svg viewBox="0 0 760 320" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" role="presentation">
  <defs>
   <linearGradient id="tcScreen" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fffefd"/><stop offset="1" stop-color="#edf7f1"/></linearGradient>
   <linearGradient id="tcLab" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#f7f0e7"/><stop offset="1" stop-color="#efe4d8"/></linearGradient>
  </defs>
  <!-- playful analytics workspace, no agricultural landscape -->
  <ellipse cx="390" cy="289" rx="331" ry="18" fill="#d8d4c8" opacity=".31"/>
  <path d="M128 70Q132 34 181 34H582Q631 34 636 81V268H128Z" fill="url(#tcLab)" opacity=".72"/>
  <path d="M128 104H636" stroke="#e9dbcd" stroke-width="2" stroke-dasharray="5 9"/>
  <g transform="translate(180 34)">
   <rect width="333" height="217" rx="22" fill="#fffdf9" stroke="#d7cabd" stroke-width="4"/>
   <rect x="15" y="13" width="303" height="190" rx="13" fill="url(#tcScreen)" />
   <circle cx="34" cy="30" r="5" fill="#d58b7b"/><circle cx="49" cy="30" r="5" fill="#e4c185"/><circle cx="64" cy="30" r="5" fill="#91b49e"/>
   <text x="82" y="35" font-size="12" font-weight="800" font-family="sans-serif" fill="#6c7f74">HANWOO DATA CENTER</text>
   <rect x="32" y="52" width="119" height="55" rx="10" fill="#e4f0e7"/>
   <text x="44" y="70" font-size="10" fill="#607f71" font-family="sans-serif">DATA INSIGHT</text>
   <text x="43" y="94" font-size="24" font-weight="900" fill="#345e52" font-family="sans-serif">01</text>
   <rect x="165" y="52" width="135" height="55" rx="10" fill="#f9e9df"/>
   <text x="176" y="70" font-size="10" fill="#a26e5c" font-family="sans-serif">STATISTICS</text>
   <text x="175" y="94" font-size="24" font-weight="900" fill="#a96150" font-family="sans-serif">2026</text>
   <path d="M36 172H296M36 149H296M36 126H296" stroke="#d5e2dc" stroke-width="1.5" stroke-dasharray="4 6"/>
   <path d="M40 168L79 154L115 158L154 136L191 143L227 126L290 118" stroke="#478e7b" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
   <path d="M40 176L79 175L115 170L154 169L191 156L227 161L290 144" stroke="#c7886a" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
   <g fill="#fff" stroke="#478e7b" stroke-width="3"><circle cx="79" cy="154" r="4"/><circle cx="154" cy="136" r="4"/><circle cx="227" cy="126" r="4"/><circle cx="290" cy="118" r="4"/></g>
   <path d="M133 218h68l8 28h-84Z" fill="#cabeb1"/><rect x="102" y="244" width="132" height="10" rx="5" fill="#bfaea1"/>
  </g>
  <!-- small friendly cow researcher on the right -->
  <g transform="translate(505 140)" stroke="#57453b" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
   <path d="M8 85C5 40 28 19 83 23C136 25 151 59 141 110L125 133H31Z" fill="#f9f2e7"/>
   <path d="M18 53Q-13 22-23 46Q-27 65 18 75M130 52Q163 20 176 43Q183 61 136 74" fill="#c6b1a3"/>
   <path d="M36 32Q62 15 89 26Q89 48 72 67Q48 69 31 59Z" fill="#64574d"/>
   <ellipse cx="79" cy="102" rx="49" ry="35" fill="#e8bca8"/>
   <ellipse cx="61" cy="105" rx="7" ry="10" fill="#a77869" stroke="none"/><ellipse cx="94" cy="105" rx="7" ry="10" fill="#a77869" stroke="none"/>
   <circle cx="41" cy="73" r="5" fill="#483a33" stroke="none"/><circle cx="111" cy="73" r="5" fill="#483a33" stroke="none"/>
   <path d="M68 121q12 8 25-1" fill="none"/>
   <path d="M23 137Q53 115 70 148L45 177H15Z" fill="#b47e68"/>
   <path d="M119 137Q105 118 92 146L103 177H148Z" fill="#b47e68"/>
   <rect x="-7" y="141" width="104" height="69" rx="9" fill="#dce9e1" stroke="#789484"/>
   <path d="M45 170l-8 12h16Z" fill="#76a98e" stroke="none"/>
  </g>
  <!-- floating analytics motifs -->
  <g transform="translate(81 91) rotate(-8)">
   <rect width="96" height="79" rx="16" fill="#fffdf9" stroke="#e2d5c8" stroke-width="3"/>
   <rect x="15" y="44" width="15" height="21" rx="4" fill="#e6ad91"/>
   <rect x="37" y="31" width="15" height="34" rx="4" fill="#96b7a5"/>
   <rect x="59" y="19" width="15" height="46" rx="4" fill="#527d6d"/>
   <path d="M13 14h60" stroke="#eadfd4" stroke-width="4" stroke-linecap="round"/>
  </g>
  <g transform="translate(573 57) rotate(11)">
   <rect width="96" height="67" rx="15" fill="#fffdf9" stroke="#e5dacf" stroke-width="3"/>
   <circle cx="29" cy="34" r="18" fill="#f2d5c1"/>
   <path d="M29 16A18 18 0 0 1 47 34H29Z" fill="#c88769"/>
   <path d="M29 34v18A18 18 0 0 1 12 40Z" fill="#8eae9b"/>
   <path d="M57 23h24M57 33h18M57 43h21" stroke="#b7bfb4" stroke-width="4" stroke-linecap="round"/>
  </g>
  <g fill="#dbb48d" opacity=".9"><path d="M86 211l4 10 11 1-8 7 2 12-9-6-10 6 3-12-8-7 11-1Z"/><circle cx="681" cy="206" r="6"/><circle cx="699" cy="188" r="3"/></g>
 </svg>`;
 if(mobile){
  const eyebrow=hero.querySelector('.home-eyebrow');
  const title=hero.querySelector('.hero-title');
  const desc=hero.querySelector('.hero-description');
  const content=hero.querySelector('#homeContent');
  const card=document.createElement('div');card.className='tc-mobile-hero-unified';
  const copy=document.createElement('div');copy.className='tc-mobile-hero-copy';
  [eyebrow,title,desc].filter(Boolean).forEach(node=>copy.append(node));
  card.append(copy,wrap);
  const svg=wrap.querySelector('svg');if(svg){svg.setAttribute('viewBox','150 12 510 295');svg.setAttribute('preserveAspectRatio','xMidYMid meet')}
  if(content)hero.insertBefore(card,content);else hero.prepend(card);
 }else hero.append(wrap);
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
