#!/usr/bin/env python3
"""NeuralByte static site generator.

    python3 build.py                       # builds ./site for https://neuralbytea.github.io
    SITE_URL=https://neuralbyte.com python3 build.py   # custom domain (also writes CNAME)

All content comes from data/portfolio_data.yaml. Every page is pre-rendered to
plain HTML (no client-side data loading), all links are relative, so the site
works from a domain root, a sub-path, or a local file server.
"""
import html, json, os, re, shutil, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE_URL = os.environ.get("SITE_URL", "https://neuralbytea.github.io").rstrip("/")
FORM_ID = os.environ.get("FORMSPREE_ID", "mzdwrpyp")  # TODO: replace with a NeuralByte-owned form

D = yaml.safe_load((ROOT / "data/portfolio_data.yaml").read_text())
SITE, CONTACT, APPS = D["site"], D["contact"], D["projects"]
VERS = yaml.safe_load((ROOT / "data/versions.yaml").read_text())  # from scan_versions.py
SERIES = ["19.0", "18.0", "17.0"]  # newest first
NAME = SITE["name"]
STORE = SITE["store"]
e = lambda v: html.escape(str(v if v is not None else ""), quote=True)

FAMILIES = [
    ("Portals", "🌐", "portals", "Vendor, customer, employee and field-sales portals. Self-service without extra user seats."),
    ("Payments", "💳", "payments", "Mastercard MPGS Hosted Checkout with 3-D Secure and automatic invoice reconciliation."),
    ("HR & Payroll", "👥", "hr", "Employee loans with payroll deduction, attendance and leave Gantt, self-service HR."),
    ("Dashboards", "📊", "dash", "Owl dashboards for sales, invoices, payments and payroll with Excel and PDF export."),
    ("AI Assistant", "🤖", "ai", "An AI chat bubble inside Odoo: bring your own ChatGPT, Claude or Gemini key and chat with your data."),
    ("Backend UI", "🧩", "ui", "AI list search, split view, chatter workspace, home menu and sidebar navigation."),
]
FAM_CLASS = {f[0]: f[2] for f in FAMILIES}


def family(app):
    return app["tags"][0] if app["tags"][0] in FAM_CLASS else "Backend UI"


def meta(app):
    parts = [p.strip() for p in app["role"].split("·")]
    return {"edition": parts[0], "price": parts[1] if len(parts) > 1 else "", "licence": parts[2] if len(parts) > 2 else ""}


def vers(app):
    """Published series for this app, newest first: [(series, info)]."""
    v = VERS.get(app["id"], {})
    return [(s, v[s]) for s in SERIES if s in v]


def price_label(info):
    p = float(info.get("price") or 0)
    return "Free" if not p else "$%s" % (("%g" % p) if p == int(p) else "%.2f" % p)


def latest(app):
    v = vers(app)
    return v[0] if v else (app["odoo_version"].split()[-1], {"price": None, "url": app["store_url"], "version": ""})


def ver_chips(app):
    return "".join(f'<i class="vb">{s.split(".")[0]}</i>' for s, _ in reversed(vers(app)))


def slug(app):
    return app["id"]


# --------------------------------------------------------------------------- layout
def head(title, desc, path, root, og_image="images/og-cover.png", extra=""):
    url = f"{SITE_URL}/{path}"
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#070b16">
<meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}favicon.ico" sizes="any"><link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Sora:wght@500;600;700;800&family=JetBrains+Mono:wght@400&display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
<script defer src="{root}assets/site.js"></script>
{extra}
</head>"""


def nav(root, active):
    def a(key, href, label):
        return f'<a href="{root}{href}"{" class=on" if key == active else ""}>{label}</a>'
    return f"""<header class="nav"><div class="wrap nav-in">
<a class="brand" href="{root}"><img src="{root}images/mark-512.png" width="30" height="30" alt="">{NAME}</a>
<nav id="menu">{a("home", "", "Home")}{a("apps", "apps/", "Apps")}<a href="{root}#services">Services</a>{a("contact", "contact/", "Contact")}
<a href="{STORE}" target="_blank" rel="noopener">Odoo Store ↗</a></nav>
<a class="btn btn-sm btn-primary nav-cta" href="{root}contact/">Start a project</a>
<button class="burger" aria-label="Menu" aria-controls="menu"><i></i><i></i></button>
</div></header>"""


def footer(root):
    fam = "".join(f'<a href="{root}apps/?line={FAM_CLASS[f[0]]}">{f[0]}</a>' for f in FAMILIES)
    return f"""<footer class="foot"><div class="wrap foot-grid">
<div><a class="brand" href="{root}"><img src="{root}images/mark-512.png" width="30" height="30" alt="">{NAME}</a>
<p class="muted">Odoo apps and custom development. {len(APPS)} apps on the Odoo Apps Store.</p></div>
<div><h4>Product lines</h4>{fam}</div>
<div><h4>Company</h4><a href="{root}apps/">All apps</a><a href="{root}contact/">Contact</a><a href="{STORE}" target="_blank" rel="noopener">Odoo Apps Store ↗</a></div>
<div><h4>Get in touch</h4><a href="mailto:{CONTACT['email']}">{CONTACT['email']}</a><span class="muted">{CONTACT['location']}</span><span class="muted">Working remotely worldwide</span></div>
</div><div class="wrap foot-bar"><span>© {2026} {NAME}. All rights reserved.</span><span>Odoo is a trademark of Odoo S.A.</span></div></footer>"""


def page(title, desc, path, active, body, extra="", og="images/og-cover.png"):
    root = "../" * len(path.strip("/").split("/")) if path.endswith("/") else ""
    return head(title, desc, path, root, og, extra) + f'<body>\n<div class="aurora"></div>\n{nav(root, active)}\n<main>{body.replace("{{root}}", root)}</main>\n{footer(root)}\n</body></html>'


def cover(app, root, cls="shot"):
    if app.get("image"):
        img = app["image"].replace("assets/", "")
        return f'<div class="{cls}"><img src="{root}{img}" alt="{e(app["title"])} for Odoo" loading="lazy" width="1000" height="500"></div>'
    f = family(app)
    return f'<div class="{cls} cover cv-{FAM_CLASS[f]}"><small>Odoo {latest(app)[0].split(".")[0]}</small><b>{e(app["title"])}</b><span>{e(f)}</span></div>'


def app_card(app, root):
    m = meta(app)
    return f"""<a class="card app reveal" href="{root}apps/{slug(app)}/" data-line="{FAM_CLASS[family(app)]}" data-ver="{' '.join(s.split('.')[0] for s, _ in vers(app))}" data-q="{e((app['title'] + ' ' + app['short_desc'] + ' ' + ' '.join(app['tags'])).lower())}">
{cover(app, root)}
<div class="app-body"><div class="app-top"><span class="chip fam-{FAM_CLASS[family(app)]}">{e(family(app))}</span><span class="price">{price_label(latest(app)[1])}</span></div>
<h3>{e(app['title'])}</h3><p>{e(app['short_desc'])}</p>
<div class="app-foot"><span class="more">View details <i>→</i></span><span class="vbs" title="Odoo versions">{ver_chips(app)}</span></div></div></a>"""


# --------------------------------------------------------------------------- pages
def home():
    root = ""
    featured = [a for a in APPS if a.get("featured")][:6]
    hero_shots = [a for a in APPS if a.get("image")][:3]
    stack = "".join(f'<div class="float f{i+1}"><img src="images/{a["image"].split("images/")[1]}" alt="{e(a["title"])}" width="1000" height="500"></div>' for i, a in enumerate(hero_shots))
    stats = "".join(f'<div class="stat reveal"><b>{e(s["value"])}</b><span>{e(s["label"])}</span></div>' for s in D["stats"])
    fams = "".join(
        f'<a class="card fam reveal" href="apps/?line={c}"><div class="ico">{ico}</div><h3>{n}</h3><p>{d}</p>'
        f'<span class="more">{sum(1 for a in APPS if family(a) == n)} app{"" if sum(1 for a in APPS if family(a) == n) == 1 else "s"} <i>→</i></span></a>'
        for n, ico, c, d in FAMILIES) + ('<a class="card fam reveal" href="contact/"><div class="ico">🛠</div><h3>Custom development</h3>'
        '<p>Need something else? We build custom Odoo modules, portals and integrations.</p><span class="more">Talk to us <i>→</i></span></a>')
    hire = "".join(f'<div class="card hire reveal"><small>{e(h["k"])}</small><b>{e(h["v"])}</b><p>{e(h["n"])}</p></div>' for h in D["hire"])
    tech = "".join(f"<span>{t}</span>" for t in ["Odoo 17", "Odoo 18", "Odoo 19", "Python", "OWL", "JavaScript", "PostgreSQL", "QWeb", "Portals", "Payments", "HR & Payroll", "Accounting", "Purchase", "Sales"])
    body = f"""
<section class="hero wrap">
 <div class="hero-copy">
  <span class="pill"><i class="dot"></i>{len(APPS)} apps live on the Odoo Apps Store</span>
  <h1>Odoo apps that <em>empower</em> your team and customers.</h1>
  <p class="lead">{NAME} builds production-ready Odoo apps for versions 17, 18 and 19: vendor, customer and employee portals, payment providers, HR and payroll tools, dashboards, an AI assistant and backend UI upgrades. Install from the store, or let us build it for you.</p>
  <div class="btn-row"><a class="btn btn-primary" href="apps/">Browse the apps</a><a class="btn btn-ghost" href="contact/">Talk to us →</a></div>
  <ul class="trust"><li>Odoo 17 · 18 · 19</li><li>Community &amp; Enterprise</li><li>OPL-1 licensed</li><li>Store-published</li></ul>
 </div>
 <div class="hero-art" aria-hidden="true"><div class="glow"></div>{stack}</div>
</section>
<section class="wrap stats">{stats}</section>
<div class="marquee" aria-hidden="true"><div class="track">{tech}{tech}</div></div>
<section class="wrap sec"><div class="sec-head reveal"><span class="eyebrow">Product lines</span><h2>Six families of Odoo apps</h2><p>Each app does one job and works out of the box after install.</p></div>
 <div class="grid fam-grid">{fams}</div></section>
<section class="wrap sec"><div class="sec-head reveal"><span class="eyebrow">Featured</span><h2>Where most customers start</h2><p>Portals, payments and payroll tools.</p><a class="see" href="apps/">All {len(APPS)} apps →</a></div>
 <div class="grid app-grid">{''.join(app_card(a, root) for a in featured)}</div></section>
<section class="wrap sec" id="services"><div class="sec-head reveal"><span class="eyebrow">Services</span><h2>Apps, custom work and support</h2></div>
 <div class="grid hire-grid">{hire}</div></section>
<section class="wrap"><div class="cta reveal"><h2>Need an Odoo app <span class="grad">built or customised?</span></h2>
 <p>Send a short note about what you need and we will reply with how we would approach it.</p>
 <div class="btn-row center"><a class="btn btn-primary" href="contact/">Contact us</a><a class="btn btn-ghost" href="{STORE}" target="_blank" rel="noopener">Odoo Apps Store ↗</a></div></div></section>"""
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": NAME, "url": SITE_URL + "/", "email": CONTACT["email"],
          "logo": SITE_URL + "/images/mark-512.png", "description": SITE["description"]}
    return page(f"{NAME} | Odoo 17, 18 & 19 Apps and Custom Odoo Development", SITE["description"], "", "home", body,
                f'<script type="application/ld+json">{json.dumps(ld)}</script>')


def apps_page():
    root = "../"
    chips = '<button class="fchip on" data-line="all">All <b>%d</b></button>' % len(APPS) + "".join(
        f'<button class="fchip" data-line="{c}">{n} <b>{sum(1 for a in APPS if family(a) == n)}</b></button>' for n, _, c, _ in FAMILIES)
    vchips = '<button class="fchip vchip on" data-ver="all">All</button>' + "".join(
        f'<button class="fchip vchip" data-ver="{s.split(".")[0]}">{s.split(".")[0]} <b>{sum(1 for a in APPS if s in dict(vers(a)))}</b></button>' for s in SERIES)
    body = f"""<section class="wrap page-hero"><div class="crumb"><a href="{root}">Home</a> / Apps</div>
<h1>Odoo apps</h1><p class="lead">Every app is published on the Odoo Apps Store. Pick your Odoo version, filter by product line, or search by feature.</p>
<div class="toolbar"><div class="chips vchips"><span class="lbl">Odoo</span>{vchips}</div></div>
<div class="toolbar"><div class="chips">{chips}</div><input id="q" type="search" placeholder="Search apps…" aria-label="Search apps"></div></section>
<section class="wrap"><div class="grid app-grid" id="app-grid">{''.join(app_card(a, root) for a in APPS)}</div>
<p id="none" class="muted center" hidden>No apps match your search.</p></section>"""
    return page(f"Odoo 17, 18 & 19 Apps by {NAME} | Portals, Payments, HR, AI",
                f"Browse {len(APPS)} Odoo apps for versions 17, 18 and 19 by {NAME}: portals, payments, HR and payroll, dashboards, AI assistant and backend UI.",
                "apps/", "apps", body)


def app_page(i, app):
    root = "../../"
    m = meta(app)
    related = [a for a in APPS if a is not app and family(a) == family(app)][:3] or [a for a in APPS if a is not app][:3]
    prev_a, next_a = APPS[i - 1], APPS[(i + 1) % len(APPS)]
    mods = "".join(f"<span class='tag'>{e(x)}</span>" for x in app.get("modules", []))
    tech = "".join(f"<span class='tag'>{e(x)}</span>" for x in app.get("tech_stack", []))
    feats = "".join(f"<li>{e(x)}</li>" for x in app.get("highlights", []))
    lat_s, lat = latest(app)
    price_num = str(float(lat.get("price") or 0))
    vlist = "".join(
        f'<a class="vrow{" new" if i == 0 else ""}" href="{info["url"]}" target="_blank" rel="noopener"><b>Odoo {s.split(".")[0]}</b>'
        f'<span>v{info["version"].split(".", 2)[2]} · {price_label(info)}</span><i>Get ↗</i></a>' for i, (s, info) in enumerate(vers(app)))
    body = f"""<section class="wrap page-hero slim"><div class="crumb"><a href="{root}">Home</a> / <a href="{root}apps/">Apps</a> / {e(app['title'])}</div></section>
<section class="wrap detail">
 <div class="detail-main">
  {cover(app, root, "shot big")}
  <div class="chips-row"><span class="chip fam-{FAM_CLASS[family(app)]}">{e(family(app))}</span>{''.join(f'<span class="tag">{e(t)}</span>' for t in app['tags'][1:])}</div>
  <h1>{e(app['title'])}</h1><p class="lead">{e(app['short_desc'])}.</p>
  <h2 class="h3">About this app</h2><p class="body">{e(app['full_desc'])}</p>
  <h2 class="h3">Key features</h2><ul class="feat">{feats}</ul>
 </div>
 <aside class="detail-side"><div class="card buy">
  <div class="buy-price"><b>{price_label(latest(app)[1])}</b><span>{"one-time" if float(latest(app)[1].get("price") or 0) else "open licence"}</span></div>
  <h4>Get it for your Odoo version</h4>
  <div class="vlist">{vlist}</div>
  <a class="btn btn-ghost block" href="{root}contact/?subject={e(app['title'])}">Ask a question</a>
  <dl><dt>Odoo versions</dt><dd>{" · ".join(s.split(".")[0] for s, _ in reversed(vers(app)))}</dd><dt>Edition</dt><dd>{e(m['edition'])}</dd><dt>Licence</dt><dd>{e(m['licence'])}</dd><dt>Publisher</dt><dd>{NAME}</dd></dl>
  <h4>Works with</h4><div class="tags">{mods}</div><h4>Tech stack</h4><div class="tags">{tech}</div></div></aside>
</section>
<section class="wrap sec"><div class="sec-head"><h2>Related apps</h2></div><div class="grid app-grid">{''.join(app_card(a, root) for a in related)}</div>
<div class="pn"><a href="{root}apps/{slug(prev_a)}/">← {e(prev_a['title'])}</a><a href="{root}apps/{slug(next_a)}/">{e(next_a['title'])} →</a></div></section>"""
    ld = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": app["title"], "applicationCategory": "BusinessApplication",
          "operatingSystem": "Odoo " + ", ".join(s.split(".")[0] for s, _ in vers(app)), "description": app["short_desc"], "url": f"{SITE_URL}/apps/{slug(app)}/",
          "offers": {"@type": "Offer", "price": price_num, "priceCurrency": "USD", "url": lat["url"]},
          "publisher": {"@type": "Organization", "name": NAME}}
    img = app["image"].replace("assets/", "") if app.get("image") else "images/og-cover.png"
    return page(f"{app['title']} for Odoo {' / '.join(s.split('.')[0] for s, _ in reversed(vers(app)))} | {NAME}", app["short_desc"] + ". " + app["full_desc"][:110], f"apps/{slug(app)}/", "apps", body,
                f'<script type="application/ld+json">{json.dumps(ld)}</script>', img)


def contact_page():
    body = f"""<section class="wrap page-hero"><div class="crumb"><a href="../">Home</a> / Contact</div><h1>Let's talk</h1>
<p class="lead">Questions about an app, or need something built? Tell us what you need and we will reply by email.</p></section>
<section class="wrap contact">
 <div class="card info"><h3>Email</h3><a href="mailto:{CONTACT['email']}">{CONTACT['email']}</a><h3>Location</h3><p>{CONTACT['location']} · remote worldwide</p>
  <h3>Odoo Apps Store</h3><a href="{STORE}" target="_blank" rel="noopener">View all apps ↗</a><h3>Engagement</h3><p>Fixed price or hourly.</p></div>
 <form class="card form" action="https://formspree.io/f/{FORM_ID}" method="POST">
  <label>Your name<input name="name" required placeholder="Jane Doe"></label>
  <label>Email<input type="email" name="_replyto" required placeholder="you@company.com"></label>
  <label>Subject<input name="subject" id="subject" required placeholder="e.g. Question about Vendor Portal Pro"></label>
  <label>Message<textarea name="message" required rows="6" placeholder="What do you need?"></textarea></label>
  <input name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" class="hp">
  <button class="btn btn-primary" type="submit">Send message →</button><p class="status" id="status" role="status"></p></form>
</section>"""
    return page(f"Contact | {NAME}", f"Contact {NAME} about an Odoo app or custom Odoo development.", "contact/", "contact", body)


def not_found():
    # Absolute root-relative assets so it works at any depth on a domain root.
    body = '<section class="wrap page-hero center"><h1>404</h1><p class="lead">That page does not exist.</p><a class="btn btn-primary" href="/">Back to home</a></section>'
    out = page(f"Page not found | {NAME}", "Page not found", "404.html", "", body)
    return out.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/').replace('src="images/', 'src="/images/').replace('href="./', 'href="/')


# --------------------------------------------------------------------------- build
def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "src/static", OUT)
    (OUT / "assets").mkdir()
    for f in ("style.css", "site.js"):
        shutil.copy(ROOT / "src" / f, OUT / "assets" / f)
    write("index.html", home())
    write("apps/index.html", apps_page())
    for i, a in enumerate(APPS):
        write(f"apps/{slug(a)}/index.html", app_page(i, a))
    write("contact/index.html", contact_page())
    write("404.html", not_found())
    urls = ["", "apps/", "contact/"] + [f"apps/{slug(a)}/" for a in APPS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE_URL}/{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    write(".nojekyll", "")
    host = SITE_URL.split("//")[1]
    if not host.endswith(".github.io"):
        write("CNAME", host + "\n")
    print(f"built {len(urls) + 1} pages -> {OUT}  (SITE_URL={SITE_URL})")


if __name__ == "__main__":
    main()
