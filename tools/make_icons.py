"""Render PNG icons + social image from the vector logo (needs headless Chrome via cdp.py and Pillow)."""
import base64, io, re, time
from pathlib import Path
from PIL import Image
from cdp import Browser

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "src/static"
mark = (STATIC / "images/nb-mark.svg").read_text()
icon = (ROOT / "tools/art/app-icon.svg").read_text()
b = Browser(width=1200, height=630)


def render(html, w, h, transparent=False):
    (ROOT / "tools/art/_r.html").write_text(html)
    b.send("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
    if transparent:
        b.send("Emulation.setDefaultBackgroundColorOverride", color={"r": 0, "g": 0, "b": 0, "a": 0})
    b.go("file://" + str(ROOT / "tools/art/_r.html"), .6)
    time.sleep(.3)
    r = b.send("Page.captureScreenshot", format="png", clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 1})
    return Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGBA")


def square(size):
    return render(f'<body style="margin:0;background:transparent">{icon.replace("<svg ", f"<svg width={size} height={size} ", 1)}</body>', size, size, True)


# favicon.ico (16/32/48), apple-touch-icon (180), 512 mark with solid dark background
sq = {s: square(s) for s in (16, 32, 48, 180, 512)}
sq[48].save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[sq[32], sq[16]])
sq[180].convert("RGB").save(STATIC / "apple-touch-icon.png")
sq[512].convert("RGB").save(STATIC / "images/mark-512.png")

# social share card 1200x630
card = f'''<body style="margin:0;width:1200px;height:630px;position:relative;overflow:hidden;font-family:Sora,Inter,sans-serif;color:#fff;
background:radial-gradient(60% 90% at 88% 0,rgba(47,91,255,.55),transparent 62%),radial-gradient(50% 70% at 0 100%,rgba(154,92,255,.35),transparent 60%),#070b16">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@500;600&display=swap" rel=stylesheet>
<div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(120deg,#000,transparent 75%)"></div>
<div style="position:absolute;left:70px;top:96px;width:520px">{mark.replace("<svg ", "<svg width=520 ", 1)}</div>
<div style="position:absolute;left:690px;top:150px;width:440px">
 <div style="font:800 64px/1 Sora;letter-spacing:-.04em">Neural<span style="background:linear-gradient(100deg,#2f9bff,#9a5cff);-webkit-background-clip:text;color:transparent">bytea</span></div>
 <div style="margin-top:14px;font:600 15px Inter;letter-spacing:.34em;text-transform:uppercase;color:#9fb0d8">Solutions that empower</div>
 <div style="margin-top:34px;font:500 27px/1.4 Inter;color:#d6def5">Odoo apps for versions 17, 18 and 19, and custom Odoo development.</div>
 <div style="margin-top:30px;display:inline-block;padding:12px 24px;border-radius:99px;background:linear-gradient(120deg,#2f5bff,#12b5f0);font:600 20px Inter">neuralbytea.github.io</div></div></body>'''
render(card, 1200, 630).convert("RGB").save(STATIC / "images/og-cover.png")
b.close()
print("icons written:", [p.name for p in (STATIC / "favicon.ico", STATIC / "apple-touch-icon.png", STATIC / "images/mark-512.png", STATIC / "images/og-cover.png")])
