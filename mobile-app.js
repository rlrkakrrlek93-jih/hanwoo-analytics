/* HANWOO INSIGHT mobile PWA UI. Presentation-only, never modifies official data. */
(()=>{'use strict';
const root=document.documentElement;
const mobile=()=>window.matchMedia('(max-width: 820px)').matches;
const hero=document.querySelector('.hero');
if(hero&&!hero.id)hero.id='app-overview';
const tabTargets=[
  ['#app-overview','⌂','홈'],
  ['#marketScope','▥','시장'],
  ['#semenSalesScope','♧','정액'],
  ['#details','≡','상세']
];
const bar=document.createElement('nav');
bar.className='mobile-bottom-nav';
bar.setAttribute('aria-label','모바일 주요 메뉴');
for(const [href,symbol,label] of tabTargets){
 const a=document.createElement('a');
 a.href=href;a.setAttribute('data-app-tab',label);
 const icon=document.createElement('span');icon.className='mobile-tab-icon';icon.textContent=symbol;icon.setAttribute('aria-hidden','true');
 const text=document.createElement('span');text.textContent=label;
 a.append(icon,text);
 a.addEventListener('click',()=>highlight(href));
 bar.append(a);
}
document.body.append(bar);
function highlight(href){for(const a of bar.querySelectorAll('a')){if(a.getAttribute('href')===href)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')}}
highlight(location.hash||'#app-overview');
window.addEventListener('hashchange',()=>highlight(location.hash||'#app-overview'));
const status=document.createElement('aside');status.className='mobile-offline-banner';status.hidden=true;status.role='status';
status.textContent='오프라인 · 저장된 자료일 수 있습니다. 최신값은 인터넷 연결 후 새로고침하세요.';
document.body.prepend(status);
const updateStatus=()=>{status.hidden=navigator.onLine;root.dataset.network=navigator.onLine?'online':'offline'};
window.addEventListener('online',updateStatus);window.addEventListener('offline',updateStatus);updateStatus();
for(const selector of ['#marketScope .mk-chartscroll','#semenSalesScope .ss-scroll','#semenSalesScope .ss-table']){
 const target=document.querySelector(selector);
 if(!target)continue;
 const hint=document.createElement('p');hint.className='mobile-swipe-hint';hint.textContent='↔ 좌우로 밀어 전체 그래프·표 보기';
 target.insertAdjacentElement('beforebegin',hint);
}
const header=document.querySelector('.top');
const install=document.createElement('button');install.type='button';install.className='mobile-install-button';install.textContent='＋ 앱 설치';
install.setAttribute('aria-label','홈 화면에 한우 인사이트 앱 설치하기');
if(header)header.append(install);
let pendingPrompt=null;
const standalone=()=>window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
const refreshInstall=()=>{install.hidden=standalone()};
window.addEventListener('appinstalled',()=>{pendingPrompt=null;install.hidden=true});
window.addEventListener('beforeinstallprompt',evt=>{evt.preventDefault();pendingPrompt=evt;refreshInstall()});
refreshInstall();
const guide=document.createElement('div');guide.className='mobile-install-guide';guide.hidden=true;
guide.setAttribute('role','dialog');guide.setAttribute('aria-modal','true');guide.setAttribute('aria-label','홈 화면에 앱 설치 안내');
const card=document.createElement('div');card.className='guide-card';
const title=document.createElement('h2');title.textContent='한우 인사이트 앱 설치';
const instructions=document.createElement('p');
const close=document.createElement('button');close.type='button';close.textContent='확인';close.addEventListener('click',()=>{guide.hidden=true;install.focus()});
card.append(title,instructions,close);guide.append(card);document.body.append(guide);
guide.addEventListener('click',evt=>{if(evt.target===guide)guide.hidden=true});
document.addEventListener('keydown',evt=>{if(evt.key==='Escape')guide.hidden=true});
install.addEventListener('click',async()=>{
 if(standalone())return;
 if(pendingPrompt){
   const evt=pendingPrompt;pendingPrompt=null;
   try{await evt.prompt();const result=await evt.userChoice;if(result.outcome==='accepted')install.hidden=true;}catch(e){showGuide()}
 }else showGuide();
});
function showGuide(){
 const apple=/iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
 instructions.textContent=apple
  ? 'Safari에서 이 홈페이지를 열고 공유(□↑) → 홈 화면에 추가 → 추가를 누르세요. 설치 후 아이콘을 누르면 앱처럼 열립니다.'
  : 'Chrome 또는 삼성 인터넷에서 브라우저 메뉴(⋮) → 앱 설치 또는 홈 화면에 추가를 누르세요. 설치 후 한우 인사이트 아이콘으로 바로 실행할 수 있습니다.';
 guide.hidden=false;close.focus();
}
if('serviceWorker' in navigator){
 window.addEventListener('load',()=>{navigator.serviceWorker.register('./service-worker.js',{scope:'./'}).catch(err=>{console.warn('Offline support unavailable:',err?.message||err)})});
}
})();