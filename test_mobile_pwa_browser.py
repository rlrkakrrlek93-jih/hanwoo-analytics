#!/usr/bin/env python3
"""Mobile PWA regression with Chromium. No published statistics are modified."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import struct
import zlib

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):pass

def verify_png(path, expected):
    data=(ROOT/path).read_bytes()
    assert data[:8]==bytes([137,80,78,71,13,10,26,10]),(path,"bad PNG magic")
    pos=8;idat=b""
    while pos<len(data):
        n=struct.unpack(">I",data[pos:pos+4])[0]
        name=data[pos+4:pos+8]
        chunk=data[pos+8:pos+8+n]
        expected_crc=struct.unpack(">I",data[pos+8+n:pos+12+n])[0]
        assert zlib.crc32(name+chunk)&0xFFFFFFFF==expected_crc,(path,"bad CRC")
        if name==b"IHDR":
            w,h,depth,color=struct.unpack(">IIBB",chunk[:10])
            assert (w,h,depth,color)==(expected,expected,2,3)
        if name==b"IDAT":idat+=chunk
        pos+=n+12
        if name==b"IEND":break
    decoded=zlib.decompress(idat)
    assert len(decoded)==expected*(1+(expected+3)//4),(path,"invalid rows")

def check_app(page, mobile):
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto(f"http://127.0.0.1:{PORT}/index.html",wait_until="domcontentloaded",timeout=40000)
    page.locator("#marketScope .mk-card").first.wait_for(timeout=18000)
    page.locator("#semenSalesScope .ss-table tbody tr").first.wait_for(timeout=18000)
    assert page.locator("#semenSalesScope .ss-table tbody tr").count()==12
    assert page.locator("#marketScope svg path[data-year]").count()==9
    assert page.locator("link[rel=manifest]").get_attribute("href")=="./manifest.webmanifest"
    if mobile:
        assert page.locator(".mobile-bottom-nav").is_visible(), "mobile bottom nav should be visible"
        assert page.locator(".mobile-bottom-nav a").count()==4
        assert page.locator(".mobile-install-button").is_visible(), "install guide button should be visible"
        assert page.locator("#semenSalesScope .ss-table").evaluate("el=>el.scrollWidth>el.clientWidth"), "data table must be scrollable on phone"
        bounds=page.evaluate("({page:document.documentElement.scrollWidth,view:window.innerWidth})")
        assert bounds["page"]<=bounds["view"]+2, ("whole-page horizontal overflow",bounds)
        page.locator(".mobile-bottom-nav a[href='#semenSalesScope']").click()
        assert page.evaluate("location.hash")=="#semenSalesScope"
        page.locator(".mobile-install-button").click()
        assert page.locator(".mobile-install-guide").is_visible()
        page.locator(".mobile-install-guide button").click()
        assert not page.locator(".mobile-install-guide").is_visible()
    else:
        assert not page.locator(".mobile-bottom-nav").is_visible()
    assert not errors,errors[:4]

def main():
    global PORT
    manifest=json.loads((ROOT/"manifest.webmanifest").read_text(encoding="utf8"))
    assert manifest["display"]=="standalone"
    assert manifest["scope"]=="./"
    assert manifest["start_url"].startswith("./")
    sizes={x["sizes"] for x in manifest["icons"]}
    assert {"192x192","512x512"}<=sizes
    for path,size in [("pwa/icon-192.png",192),("pwa/icon-512.png",512),("pwa/apple-touch-icon.png",180)]:
        verify_png(path,size)
    for name in ["index.html","dashboard_template.html"]:
        html=(ROOT/name).read_text(encoding="utf8")
        assert 'href="./mobile.css"' in html
        assert 'src="mobile-app.js"' in html
        assert 'rel="manifest"' in html
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
    PORT=server.server_port
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            try:
                for width,height in [(390,844),(768,1024)]:
                    ctx=browser.new_context(viewport={"width":width,"height":height},is_mobile=True,
                        has_touch=True,device_scale_factor=2,locale="ko-KR",service_workers="allow")
                    page=ctx.new_page()
                    check_app(page,mobile=True)
                    if width==390:
                        output=ROOT/"test_artifacts";output.mkdir(exist_ok=True)
                        page.locator("#marketScope").screenshot(path=str(output/"hanwoo_mobile_market.png"))
                        page.locator("#semenSalesScope").screenshot(path=str(output/"hanwoo_mobile_semen.png"))
                        # Ensure app install resources are cached and can serve a full app offline.
                        page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller !== null",
                            timeout=26000)
                        ctx.set_offline(True)
                        page.reload(wait_until="domcontentloaded",timeout=24000)
                        assert page.locator(".mobile-offline-banner").is_visible()
                        assert page.locator("#marketScope").count()==1
                        ctx.set_offline(False)
                    ctx.close()
                desktop=browser.new_context(viewport={"width":1280,"height":900},locale="ko-KR")
                check_app(desktop.new_page(),mobile=False)
                desktop.close()
            finally:
                browser.close()
    finally:
        server.shutdown();server.server_close()
    print("PASS: PWA icons and manifest, 390px/768px mobile layout, desktop, installer, navigation, offline fallback")

if __name__=="__main__":main()
