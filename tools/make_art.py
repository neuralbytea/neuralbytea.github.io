"""Render store banners (1200x600) and icons (256x256) for NeuralBytea modules.
Banners embed REAL screenshots taken from the running module (see /tmp/shots/final)."""
import os, sys, time
from cdp import Browser

SHOTS = os.environ.get("SHOTS", "/tmp/shots/final")
OUT = os.environ.get("ART_OUT", "/tmp/shots/art")
MARK = os.path.abspath("../src/static/images/mark-512.png")
os.makedirs(OUT, exist_ok=True)

BASE = """<!doctype html><meta charset=utf-8>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Sora:wght@600;700;800&display=swap" rel=stylesheet>
<style>
*{box-sizing:border-box;margin:0}
body{width:1200px;height:600px;overflow:hidden;position:relative;font-family:Inter,sans-serif;color:#fff;
background:radial-gradient(60% 80% at 100% 0,%(glow1)s,transparent 60%),radial-gradient(50% 60% at 0 100%,%(glow2)s,transparent 60%),%(bg)s}
body:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:40px 40px}
.brand{position:absolute;left:60px;top:58px;display:flex;align-items:center;gap:14px;font:600 14px Inter;letter-spacing:.2em;color:#cfd0ee}
.brand i{width:44px;height:44px;border-radius:12px;background:%(accent)s;display:grid;place-items:center;box-shadow:0 8px 24px -6px %(accent)s}
.brand img{width:26px;height:26px;border-radius:6px}
h1{position:absolute;left:60px;top:128px;width:600px;font:700 66px/1.04 Sora;letter-spacing:-.03em}
h1 em{font-style:normal;background:%(grad)s;-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{position:absolute;left:60px;top:300px;width:540px;font:400 20px/1.5 Inter;color:#b9b8d9}
.sub b{color:#fff;font-weight:600}
.pills{position:absolute;left:60px;top:392px;width:600px;display:flex;flex-wrap:wrap;gap:10px}
.pills span{display:flex;align-items:center;gap:9px;padding:9px 16px;border-radius:99px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);font:500 15px Inter;color:#eceaff}
.pills span:before{content:"";width:8px;height:8px;border-radius:50%%;background:var(--c)}
.win{position:absolute;left:668px;top:62px;width:492px;height:416px;border-radius:16px;background:#fff;overflow:hidden;box-shadow:0 30px 70px -20px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.15)}
.bar{height:34px;background:#f1f1f6;display:flex;align-items:center;gap:7px;padding:0 14px;font:500 11px 'Inter';color:#777;border-bottom:1px solid #e3e3ec}
.bar i{width:11px;height:11px;border-radius:50%%}.bar b{margin-left:10px;font-weight:500;letter-spacing:.02em}
.view{position:absolute;top:34px;left:0;right:0;bottom:0;overflow:hidden}
.view img{position:absolute;width:%(iw)spx;left:%(ix)spx;top:%(iy)spx}
.card{position:absolute;right:48px;top:420px;width:190px;padding:14px 18px;border-radius:14px;background:%(cardbg)s;box-shadow:0 20px 40px -12px rgba(0,0,0,.6);border:1px solid rgba(255,255,255,.25)}
.card small{display:block;font:600 11px Inter;letter-spacing:.1em;text-transform:uppercase;opacity:.85}
.card b{display:block;font:700 30px/1.15 Sora;margin-top:2px}.card span{font:400 12px Inter;opacity:.85}
.tag{position:absolute;left:660px;top:508px;padding:11px 20px;border-radius:12px;background:#fff;color:#1b1840;font:600 15px Inter;box-shadow:0 14px 30px -10px rgba(0,0,0,.6);display:flex;gap:10px;align-items:center}
.tag:before{content:"";width:9px;height:9px;border-radius:50%%;background:%(accent)s}
.foot{position:absolute;left:60px;bottom:34px;font:500 13px Inter;letter-spacing:.04em;color:#8e8cb5}
</style>
<body>
<div class=brand><i><img src="file://%(mark)s"></i>NEURALBYTEA</div>
<h1>%(title)s</h1>
<div class=sub>%(sub)s</div>
<div class=pills>%(pills)s</div>
<div class=win><div class=bar><i style=background:#ff5f57></i><i style=background:#febc2e></i><i style=background:#28c840></i><b>%(url)s</b></div>
<div class=view><img src="file://%(shot)s"></div></div>
<div class=card><small>%(ck)s</small><b>%(cv)s</b><span>%(cs)s</span></div>
<div class=tag>%(tag)s</div>
<div class=foot>%(foot)s</div>
</body>"""

BANNERS = {
 "ess": dict(
    bg="#0a1224", glow1="rgba(20,184,166,.38)", glow2="rgba(99,102,241,.30)", accent="linear-gradient(135deg,#14b8a6,#6366f1)",
    grad="linear-gradient(100deg,#5eead4,#a5b4fc)", cardbg="linear-gradient(135deg,#10b981,#0d9488)", mark=MARK,
    title="Employee<br><em>Self Service</em>",
    sub="One workspace on <b>/my</b> where your team handles their own HR admin, instead of emailing HR.",
    pills="".join(f'<span style="--c:{c}">{t}</span>' for t, c in [("Profile & documents", "#5eead4"), ("Time off & approvals", "#34d399"), ("Attendance timeline", "#60a5fa"), ("Overtime & comp-off", "#fbbf24"), ("Expenses", "#f472b6"), ("Payslips (Enterprise)", "#a5b4fc")]),
    shot=f"{SHOTS}/ess-attendance.png", iw=1000, ix=-38, iy=-74, url="yourcompany.com/my/attendances",
    ck="Paid time off", cv="22.0 days", cs="left of 24.0 allocated", tag="Request, check in, claim: all self-service",
    foot="Odoo 19 · Community & Enterprise · OPL-1"),
 "sb": dict(
    bg="#0d0f29", glow1="rgba(129,140,248,.40)", glow2="rgba(245,158,11,.22)", accent="linear-gradient(135deg,#6366f1,#f59e0b)",
    grad="linear-gradient(100deg,#a5b4fc,#fcd34d)", cardbg="linear-gradient(135deg,#4f46e5,#7c3aed)", mark=MARK,
    title="Services<br>Billing <em>Pro</em>",
    sub="Turn timesheets into profit. <b>Rate cards</b> price every hour and show the <b>margin</b> on every line.",
    pills="".join(f'<span style="--c:{c}">{t}</span>' for t, c in [("Multi-tier rate cards", "#a5b4fc"), ("Billing + cost rate", "#fcd34d"), ("Margin on every line", "#34d399"), ("Portal timer", "#60a5fa"), ("Margin dashboard", "#f472b6"), ("Sales-order billing", "#fb923c")]),
    shot=f"{SHOTS}/sb-team-overview.png", iw=1000, ix=-8, iy=-70, url="Services Billing / Team overview",
    ck="Margin (rate card)", cv="53.7%", cs="on 475 billable hours", tag="Cost rate and margin never reach portal users",
    foot="Odoo 19 · Community & Enterprise · OPL-1"),
}

ICON = """<!doctype html><meta charset=utf-8><style>*{margin:0}body{width:256px;height:256px;background:transparent}
svg{display:block}</style>%s"""
ICONS = {
 "ess": """<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#14b8a6"/><stop offset="1" stop-color="#6366f1"/></linearGradient>
<linearGradient id="h" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.22"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient></defs>
<rect width="256" height="256" rx="58" fill="url(#g)"/><path d="M0 58a58 58 0 0 1 58-58h140a58 58 0 0 1 58 58v70H0z" fill="url(#h)"/>
<circle cx="92" cy="94" r="30" fill="#ffffff"/><path d="M36 196c0-32 25-52 56-52s56 20 56 52v4H36z" fill="#ffffff"/>
<rect x="146" y="102" width="74" height="80" rx="14" fill="#ffffff"/><path d="M146 116a14 14 0 0 1 14-14h46a14 14 0 0 1 14 14v10h-74z" fill="#0f766e"/>
<rect x="161" y="92" width="7" height="18" rx="3.5" fill="#ffffff"/><rect x="198" y="92" width="7" height="18" rx="3.5" fill="#ffffff"/>
<circle cx="183" cy="156" r="18" fill="#10b981"/><path d="M174 156l7 7 12-14" stroke="#ffffff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>""",
 "sb": """<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4f46e5"/><stop offset="1" stop-color="#7c3aed"/></linearGradient>
<linearGradient id="h" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.22"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
<linearGradient id="c" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fcd34d"/><stop offset="1" stop-color="#f59e0b"/></linearGradient></defs>
<rect width="256" height="256" rx="58" fill="url(#g)"/><path d="M0 58a58 58 0 0 1 58-58h140a58 58 0 0 1 58 58v70H0z" fill="url(#h)"/>
<rect x="104" y="30" width="30" height="16" rx="6" fill="#ffffff"/><rect x="113" y="42" width="12" height="14" fill="#ffffff"/>
<circle cx="118" cy="130" r="72" fill="#ffffff"/><circle cx="118" cy="130" r="57" fill="#eef0ff"/>
<path d="M118 130V92" stroke="#4f46e5" stroke-width="9" stroke-linecap="round"/><path d="M118 130l25 15" stroke="#4f46e5" stroke-width="9" stroke-linecap="round"/><circle cx="118" cy="130" r="8" fill="#4f46e5"/>
<rect x="66" y="158" width="11" height="20" rx="3" fill="#a5b4fc"/><rect x="83" y="148" width="11" height="30" rx="3" fill="#818cf8"/>
<circle cx="190" cy="188" r="42" fill="url(#c)" stroke="#ffffff" stroke-width="8"/>
<text x="190" y="207" text-anchor="middle" font-family="Sora,Arial,sans-serif" font-weight="800" font-size="52" fill="#ffffff">$</text></svg>""",
}


def render(tpl, vals):
    for k, v in vals.items():
        tpl = tpl.replace(f"%({k})s", str(v))
    return tpl.replace("%%", "%")


def main():
    b = Browser(width=1200, height=600)
    for k, v in BANNERS.items():
        open(f"art/{k}_banner.html", "w").write(render(BASE, v))
        b.go("file://" + os.path.abspath(f"art/{k}_banner.html"), 2.5)
        b.js("document.fonts.ready.then(()=>true)")
        time.sleep(1)
        b.shot(None, f"{OUT}/{k}_banner.png", clip={"x": 0, "y": 0, "width": 1200, "height": 600})
    b.send("Emulation.setDeviceMetricsOverride", width=256, height=256, deviceScaleFactor=1, mobile=False)
    b.send("Emulation.setDefaultBackgroundColorOverride", color={"r": 0, "g": 0, "b": 0, "a": 0})
    for k, svg in ICONS.items():
        open(f"art/{k}_icon.html", "w").write(ICON % svg)
        b.go("file://" + os.path.abspath(f"art/{k}_icon.html"), 1.5)
        b.shot(None, f"{OUT}/{k}_icon.png", clip={"x": 0, "y": 0, "width": 256, "height": 256})
    b.close()
    print("ok", os.listdir(OUT))


main()
