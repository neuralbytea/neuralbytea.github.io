"""Render the N-Genius banner, icon and overview diagram (NeuralBytea branding, no third-party logos).
Inputs: /tmp/shots/ng/*.png (real screenshots). Output: /tmp/shots/ng/out/*."""
import base64, io, os, time
from pathlib import Path
from PIL import Image
from cdp import Browser

ROOT = Path(__file__).resolve().parent.parent
OUT = Path("/tmp/shots/ng/out"); OUT.mkdir(parents=True, exist_ok=True)
MARK = (ROOT / "src/static/images/nb-mark.svg").read_text()
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel=stylesheet>'
b = Browser(width=1760, height=880)


def render(html, w, h, name, transparent=False):
    (ROOT / "tools/art/_ng.html").write_text(html)
    b.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
    b.send("Emulation.setDefaultBackgroundColorOverride", color={"r": 0, "g": 0, "b": 0, "a": 0} if transparent else {"r": 255, "g": 255, "b": 255, "a": 1})
    b.go("file://" + str(ROOT / "tools/art/_ng.html"), 1.6)
    time.sleep(.8)
    r = b.send("Page.captureScreenshot", format="png", clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 1})
    im = Image.open(io.BytesIO(base64.b64decode(r["data"])))
    im.save(OUT / name); return im


def data_uri(path, crop=None):
    im = Image.open(path).convert("RGB")
    if crop: im = im.crop(crop)
    buf = io.BytesIO(); im.save(buf, "PNG"); return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------- banner 1760x880
dlg = data_uri("/tmp/shots/ng/01_pay.png", (396, 29, 1044, 392))
banner = f'''<!doctype html><meta charset=utf-8>{FONTS}<style>
*{{box-sizing:border-box;margin:0}}body{{width:1760px;height:880px;position:relative;overflow:hidden;font-family:Inter,sans-serif;color:#fff;
background:radial-gradient(60% 80% at 100% 0,rgba(45,212,191,.38),transparent 60%),radial-gradient(55% 70% at 0 100%,rgba(99,102,241,.45),transparent 60%),#0a1230}}
body:before{{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:64px 64px;mask-image:linear-gradient(110deg,#000,transparent 80%)}}
.badge{{position:absolute;left:100px;top:96px;padding:14px 30px;border-radius:99px;background:linear-gradient(120deg,#14b8a6,#6366f1);font:700 34px Sora;letter-spacing:.06em}}
h1{{position:absolute;left:100px;top:210px;font:800 138px/1 Sora;letter-spacing:-.04em;width:900px}}h1 em{{font-style:normal;background:linear-gradient(100deg,#5eead4,#a5b4fc);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{position:absolute;left:100px;top:504px;width:820px;font:500 44px/1.35 Inter;color:#cfd8f5}}
.chips{{position:absolute;left:100px;top:640px;display:flex;gap:16px}}.chips span{{padding:12px 24px;border-radius:99px;background:rgba(255,255,255,.09);border:2px solid rgba(255,255,255,.2);font:600 28px Inter}}
.win{{position:absolute;left:1000px;top:130px;width:660px;height:auto;border-radius:26px;overflow:hidden;background:#fff;box-shadow:0 50px 100px -30px rgba(0,0,0,.75),0 0 0 3px rgba(165,180,252,.55)}}.win img{{width:100%;display:block}}
.tag{{position:absolute;left:960px;top:590px;padding:20px 34px;border-radius:20px;background:#fff;color:#0f1d4a;font:700 30px Sora;box-shadow:0 24px 50px -16px rgba(0,0,0,.6);display:flex;gap:16px;align-items:center}}.tag:before{{content:"";width:16px;height:16px;border-radius:50%;background:#14b8a6}}
.brand{{position:absolute;left:100px;bottom:46px;display:flex;align-items:center;gap:26px}}.brand .m{{width:150px}}.brand b{{font:700 44px Sora;letter-spacing:-.02em}}.brand b i{{font-style:normal;color:#a5b4fc}}.brand span{{display:block;font:600 22px Inter;letter-spacing:.28em;text-transform:uppercase;color:#8e9bd0;margin-top:8px}}
.foot{{position:absolute;right:100px;bottom:64px;font:500 26px Inter;color:#8e9bd0}}</style>
<div class=badge>ODOO 19</div><h1>N-Genius<br><em>Payments</em></h1>
<div class=sub>Hosted card checkout, webhooks and full refunds on every Odoo invoice.</div>
<div class=chips><span>UAE &amp; Saudi regions</span><span>3-D Secure</span><span>Free · LGPL-3</span></div>
<div class=win><img src="{dlg}"></div><div class=tag>Card payment, secured by N-Genius</div>
<div class=brand><div class=m>{MARK.replace("<svg ", '<svg width="150" ', 1)}</div><div><b>Neural<i>bytea</i></b><span>Payment providers</span></div></div>
<div class=foot>Community &amp; Enterprise · Odoo.sh &amp; On-Premise</div>'''
render(banner, 1760, 880, "banner.png")

# ---------------- icon 512x512 (rounded tile, transparent corners)
icon = '''<!doctype html><meta charset=utf-8><style>*{margin:0}body{width:512px;height:512px;background:transparent}</style>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="t" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#14b8a6"/><stop offset=".55" stop-color="#3b6cf6"/><stop offset="1" stop-color="#7c4dff"/></linearGradient>
<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#06103a" flood-opacity=".35"/></filter></defs>
<rect width="512" height="512" rx="116" fill="url(#t)"/><path d="M0 116a116 116 0 0 1 116-116h280a116 116 0 0 1 116 116v150H0z" fill="url(#s)"/>
<g filter="url(#sh)"><rect x="82" y="150" width="348" height="230" rx="34" fill="#fff"/><rect x="82" y="196" width="348" height="52" fill="#1f2b6b"/>
<rect x="116" y="290" width="104" height="22" rx="11" fill="#c7d0ef"/><rect x="116" y="326" width="150" height="16" rx="8" fill="#dde3f6"/>
<rect x="340" y="288" width="58" height="44" rx="10" fill="#14b8a6"/><rect x="340" y="288" width="58" height="12" rx="6" fill="#0d9488"/></g>
<g filter="url(#sh)"><path d="M372 236 L458 268 V338 C458 386 424 414 372 436 C320 414 286 386 286 338 V268 Z" fill="#1f2b6b" stroke="#fff" stroke-width="12" stroke-linejoin="round"/></g>
<path d="M336 338l28 28 52-60" stroke="#fff" stroke-width="24" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'''
render(icon, 512, 512, "icon.png", transparent=True)

# ---------------- overview diagram 1200x760
ov = f'''<!doctype html><meta charset=utf-8>{FONTS}<style>
*{{box-sizing:border-box;margin:0}}body{{width:1200px;height:820px;position:relative;font-family:Inter,sans-serif;color:#0f1d4a;overflow:hidden;
background:radial-gradient(70% 90% at 100% 0,#dbe6ff,transparent 60%),radial-gradient(60% 80% at 0 100%,#d9f7f1,transparent 60%),#f7f9ff}}
h2{{position:absolute;left:70px;top:56px;font:800 54px/1.1 Sora;letter-spacing:-.03em}}h2 em{{font-style:normal;background:linear-gradient(100deg,#0d9488,#4f46e5);-webkit-background-clip:text;background-clip:text;color:transparent}}
.p{{position:absolute;left:70px;top:176px;width:640px;font:500 24px/1.45 Inter;color:#4b587f}}
.box{{position:absolute;border-radius:24px;background:#fff;border:2px solid #d6def5;box-shadow:0 24px 50px -28px rgba(47,91,255,.5);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
.box b{{font:700 30px Sora}}.box span{{font:500 20px Inter;color:#66739b;margin-top:6px}}
.arrow{{position:absolute;height:6px;border-radius:3px;background:linear-gradient(90deg,#14b8a6,#6366f1)}}.arrow:after{{content:"";position:absolute;right:-4px;top:-9px;border-left:22px solid #6366f1;border-top:12px solid transparent;border-bottom:12px solid transparent}}
.step{{position:absolute;top:610px;width:250px;padding:20px 22px;border-radius:20px;background:#fff;border:2px solid #d6def5}}.step b{{display:block;font:700 22px Sora}}.step span{{font:500 17px/1.4 Inter;color:#66739b}}
.n{{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#14b8a6,#6366f1);color:#fff;font:700 18px Sora;margin-bottom:10px}}
.note{{position:absolute;left:70px;bottom:18px;font:500 16px Inter;color:#7c89ad}}</style>
<h2>How <em>N-Genius Payments</em><br>works in Odoo 19</h2>
<div class=p>Customers pay on the N-Genius hosted page. Odoo then re-reads the order from N-Genius, so the redirect alone never changes a payment.</div>
<div class=box style="left:70px;top:350px;width:250px;height:170px"><b>Odoo 19</b><span>Invoice · Pay Now</span></div>
<div class=arrow style="left:334px;top:432px;width:110px"></div>
<div class=box style="left:456px;top:320px;width:290px;height:230px;border-color:#7c8cf8"><div style="width:150px">{MARK.replace("<svg ", '<svg width="150" ', 1)}</div><b style="margin-top:6px;font-size:26px">N-Genius Payment Provider</b><span>by NeuralBytea</span></div>
<div class=arrow style="left:760px;top:432px;width:110px"></div>
<div class=box style="left:884px;top:350px;width:250px;height:170px"><b>N-Genius Online</b><span>Hosted checkout</span></div>
<div class=step style="left:70px"><div class=n>1</div><b>Hosted checkout</b><span>Card data stays on the N-Genius page.</span></div>
<div class=step style="left:340px"><div class=n>2</div><b>Webhooks</b><span>Paid, failed and refunded events.</span></div>
<div class=step style="left:610px"><div class=n>3</div><b>Sandbox and live</b><span>UAE and Saudi regions.</span></div>
<div class=step style="left:880px"><div class=n>4</div><b>Full refunds</b><span>Sent from Odoo in one click.</span></div>
<div class=note>N-Genius is a product of Network International. NeuralBytea is an independent developer and is not affiliated with Network International.</div>'''
render(ov, 1200, 820, "overview.png")
b.close(); print("written:", sorted(os.listdir(OUT)))
