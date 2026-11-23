/* Read-only public status panel; source checks are not official publication dates. */
(()=>{
 'use strict';
 const mobile=!!document.querySelector('.app-shell');
 const host=mobile?document.querySelector('#home'):document.querySelector('.footer');
 if(!host)return;
 const panel=document.createElement('section');
 panel.id='hanwooAutoUpdateStatus';
 panel.setAttribute('aria-label','한우 통계 자동 갱신 점검 현황');
 panel.style.cssText='margin:18px 0 5px;padding:14px;border:1px solid #e5e8e1;background:#fff;border-radius:15px;color:#40564b;font-size:11px;line-height:1.7';
 panel.hidden=true;
 host.append(panel);
 const stamp=document.createElement('div');
 stamp.style.cssText='font-size:12px;font-weight:800;margin-bottom:9px;';
 const list=document.createElement('div');
 list.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 10px;';
 const note=document.createElement('p');
 note.style.cssText='margin:10px 0 0;color:#88978b;font-size:10px;';
 note.textContent='마지막 점검 시각은 공식 통계 발표일이 아닙니다. 새 월별 공표는 기관별로 다릅니다.';
 panel.append(stamp,list,note);
 const fields=[['market','시장·경락'],['quality','도체 품질'],['grades','육질등급'],['ages','출하월령'],['semen_krei','정액 판매량'],['beef','육우 성적']];
 fetch('./auto_update_status.json?nocache='+Date.now(),{cache:'no-store'}).then(response=>{
    if(!response.ok)throw Error('no status yet');
    return response.json();
 }).then(data=>{
    if(!data||!data.datasets)return;
    stamp.textContent='자동 데이터 점검 · '+String(data.checked_at_kst||'');
    list.replaceChildren();
    for(const [key,label] of fields){
      const item=data.datasets[key];
      if(!item)continue;
      const element=document.createElement('div');
      const issue=item.collector_outcome==='failure';
      element.textContent=(issue?'! ':'✓ ')+label+' · '+(item.latest_published_month||'미확인');
      element.title=issue?'수집 오류 확인 필요':'보유 중인 가장 최근 공식 월';
      element.style.cssText='overflow-wrap:anywhere;font-weight:650;color:'+(issue?'#a85445':'#597466');
      list.append(element);
    }
    panel.hidden=false;
 }).catch(()=>{panel.hidden=true});
})();