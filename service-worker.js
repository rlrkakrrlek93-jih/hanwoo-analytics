/* HANWOO INSIGHT PWA — online always fetches current official data first. */
const CACHE='hanwoo-insight-mobile-20261125-calfhist1';
const ROOT=new URL('./',self.registration.scope).href;
const REQUIRED=[
 './','./index.html','./app.html','./app.css','./app.js','./data-health-widget.js','./manifest.webmanifest','./mobile.css','./mobile-app.js',
 './market-indicators.js','./semen_sales_chart.js','./quality-check.js',
 './pwa/icon-192.png','./pwa/icon-512.png','./pwa/apple-touch-icon.png',
 './data.json','./grade_data.json','./age_data.json',
 './market_supply_data.json','./semen_sales_data.json','./beef_national_data.json','./beef_grade_data.json',
 './calf_price_data.json','./calf-prices.js','./calf-prices.css','./calf-chart.js','./calf-chart.css',
 './quality_report.json'
];
self.addEventListener('install',event=>{
 event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(REQUIRED)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
 event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('hanwoo-insight-mobile-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
 const req=event.request;
 if(req.method!=='GET')return;
 const url=new URL(req.url);
 if(url.origin!==self.location.origin||!url.pathname.startsWith(new URL(ROOT).pathname))return;
 const key=new Request(url.origin+url.pathname,{method:'GET'});
 event.respondWith((async()=>{
   const cache=await caches.open(CACHE);
   try{
     const response=await fetch(req,{cache:'no-store'});
     if(response.ok)event.waitUntil(cache.put(key,response.clone()));
     return response;
   }catch(err){
     const saved=await cache.match(key);
     if(saved)return saved;
     if(req.mode==='navigate'){
       const index=await cache.match(new Request(new URL('index.html',ROOT)));
       if(index)return index;
     }
     return new Response('오프라인에서 사용할 수 없는 자료입니다.',{status:503,headers:{'Content-Type':'text/plain; charset=utf-8'}});
   }
 })());
});