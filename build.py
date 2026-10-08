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
CHAT_ENDPOINT = os.environ.get("CHAT_ENDPOINT", "").strip()  # set after deploying worker/ (see worker/README.md)
FORM_ID = os.environ.get("FORMSPREE_ID", "maeqodlq")  # NeuralBytea contact form (Formspree)

D = yaml.safe_load((ROOT / "data/portfolio_data.yaml").read_text())
SITE, CONTACT, APPS = D["site"], D["contact"], D["projects"]
CHAT_ENDPOINT = CHAT_ENDPOINT or str(SITE.get("chat_endpoint") or "").strip()
# Direct mode (GitHub Pages only, no proxy): the Groq key comes from a CI secret and is NEVER committed.
# It is only camouflaged (reversed + base64 + chunked) so naive scrapers do not spot "gsk_"; anyone with DevTools can still read it.
CHAT_KEY = "" if CHAT_ENDPOINT else os.environ.get("CHAT_KEY", "").strip()
CHAT_ON = bool(CHAT_ENDPOINT or CHAT_KEY)


def _scramble(key):
    import base64
    b = base64.b64encode(key[::-1].encode()).decode()
    n = -(-len(b) // 4)
    return [b[i:i + n] for i in range(0, len(b), n)]
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
    chat_cfg = ""
    if CHAT_ENDPOINT:
        chat_cfg = f'<script>window.NB_CHAT={json.dumps({"endpoint": CHAT_ENDPOINT, "site": SITE_URL})}</script>\n'
    elif CHAT_KEY:
        chat_cfg = f'<script>window.NB_CHAT={json.dumps({"mode": "direct", "k": _scramble(CHAT_KEY), "site": SITE_URL, "model": "openai/gpt-oss-20b"})}</script>\n'
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#ffffff">
<meta property="og:type" content="website"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE_URL}/{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}favicon.ico" sizes="any"><link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Sora:wght@500;600;700;800&family=JetBrains+Mono:wght@400&display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
<script defer src="{root}assets/site.js"></script>
{chat_cfg}<script defer src="{root}assets/chat.js"></script>
{extra}
</head>"""


def nav(root, active):
    def a(key, href, label):
        return f'<a href="{root}{href}"{" class=on" if key == active else ""}>{label}</a>'
    return f"""<header class="nav"><div class="wrap nav-in">
<a class="brand" href="{root}"><img src="{root}images/mark-512.png" width="30" height="30" alt="">{NAME}</a>
<nav id="menu">{a("home", "", "Home")}{a("apps", "apps/", "Apps")}{a("about", "about/", "About")}{a("faq", "faq/", "FAQ")}{a("contact", "contact/", "Contact")}
<a href="{STORE}" target="_blank" rel="noopener">Odoo Store ↗</a></nav>
<a class="btn btn-sm btn-primary nav-cta" href="{root}contact/">Start a project</a>
<button class="burger" aria-label="Menu" aria-controls="menu"><i></i><i></i></button>
</div></header>"""


def footer(root):
    fam = "".join(f'<a href="{root}apps/?line={FAM_CLASS[f[0]]}">{f[0]}</a>' for f in FAMILIES)
    return f"""<footer class="foot"><div class="wrap foot-grid">
<div><a class="brand" href="{root}"><img src="{root}images/mark-512.png" width="30" height="30" alt="">{NAME}</a>
<p class="muted">Odoo apps and custom development. {len(APPS)} apps on the Odoo Apps Store.</p>
<a href="mailto:{CONTACT['email']}">{CONTACT['email']}</a><span class="muted">{CONTACT['location']}</span></div>
<div><h4>Product lines</h4>{fam}</div>
<div><h4>Company</h4><a href="{root}apps/">All apps</a><a href="{root}about/">About</a><a href="{root}faq/">FAQ</a><a href="{root}contact/">Contact</a><a href="{STORE}" target="_blank" rel="noopener">Odoo Apps Store ↗</a></div>
<div><h4>Legal</h4><a href="{root}privacy/">Privacy Policy</a><a href="{root}terms/">Terms of Use</a><a href="{root}sitemap/">Sitemap</a></div>
</div><div class="wrap foot-bar"><span>© 2026 {NAME}. All rights reserved.</span><span>Odoo is a trademark of Odoo S.A.</span></div></footer>"""


def page(title, desc, path, active, body, extra="", og="images/og-cover.png"):
    root = "../" * len(path.strip("/").split("/")) if path.endswith("/") else ""
    return head(title, desc, path, root, og, extra) + f'<body>\n<div class="aurora"></div>\n{nav(root, active)}\n<main>{body.replace("{{root}}", root)}</main>\n{footer(root)}\n</body></html>'


def cover(app, root, cls="shot", lazy=True):
    if app.get("image"):
        img = app["image"].replace("assets/", "")
        return f'<div class="{cls}"><img src="{root}{img}" alt="{e(app["title"])} for Odoo"{" loading=lazy" if lazy else ""} width="1000" height="500"></div>'
    f = family(app)
    return f'<div class="{cls} cover cv-{FAM_CLASS[f]}"><small>Odoo {latest(app)[0].split(".")[0]}</small><b>{e(app["title"])}</b><span>{e(f)}</span></div>'


def updated(app):
    return latest(app)[1].get("updated") or "2026-01-01"


def price_value(app):
    return float(latest(app)[1].get("price") or 0)


# "Top picks" order: featured apps first (in data order), then the rest by last update.
RANK = {a["id"]: i for i, a in enumerate(sorted(APPS, key=lambda x: (not x.get("featured"), APPS.index(x))))}


def app_card(app, root, reveal=True, lazy=True):
    q = (app["title"] + " " + app["short_desc"] + " " + " ".join(app["tags"])).lower()
    return f"""<a class="card app{' reveal' if reveal else ''}" href="{root}apps/{slug(app)}/" data-line="{FAM_CLASS[family(app)]}" data-ver="{' '.join(s.split('.')[0] for s, _ in vers(app))}" data-price="{price_value(app):g}" data-updated="{updated(app)}" data-rank="{RANK[app['id']]}" data-name="{e(app['title'].lower())}" data-q="{e(q)}">
{cover(app, root, lazy=lazy)}
<div class="app-body"><div class="app-top"><span class="chip fam-{FAM_CLASS[family(app)]}">{e(family(app))}</span><span class="price">{price_label(latest(app)[1])}</span></div>
<h3>{e(app['title'])}</h3><p>{e(app['short_desc'])}</p>
<div class="app-foot"><span class="more">View details <i>→</i></span><span class="vbs" title="Odoo versions">{ver_chips(app)}</span></div></div></a>"""


# --------------------------------------------------------------------------- pages
FAQS = [
    ("Which Odoo versions do you support?", "Our apps are built for Odoo 17, 18 and 19. Each app page shows which versions exist, with a store link, version number and price for each. Odoo 19 has the full range."),
    ("Community or Enterprise?", "Most apps work on both. Employee Loan Pro, Attendance Leave Gantt and Payroll Dashboard Pro need Enterprise features such as Payroll or Contracts. The edition is listed on every app page."),
    ("How do I install an app?", "Get it from the Odoo Apps Store like any other app. Each app page has a button that opens the right store listing for your Odoo version."),
    ("How are the apps licensed and priced?", "Paid apps use the OPL-1 licence and a one-time price per app, with no subscription. The N-Genius payment provider is free."),
    ("Can you build something custom?", "Yes. We build custom Odoo modules, portals, payment and API integrations, dashboards and migrations, at a fixed price or hourly."),
    ("How do I get support?", "Use the contact form or the app's page on the Odoo Apps Store. We reply by email."),
    ("Does the AI Chat Assistant send my data to an AI provider?", "You connect your own AI model with your own API key (for example ChatGPT, Claude, Gemini, Groq or a local Ollama). Your questions and the records the assistant looks up are sent to the provider you choose, and it only sees what the signed-in user is allowed to see."),
    ("Who can use Employee Self Service?", "Your internal users. Employee records, time off, attendance, expenses and payslips are internal data, so the pages require an internal user and turn external users away."),
    ("Where are you based?", f"{CONTACT['location']}, working remotely with customers worldwide."),
]
VALUE = [
    (f"{len(APPS)}", "Apps on the Odoo Apps Store", "Install the way you install any Odoo app. Every listing links to its store page."),
    ("17 · 18 · 19", "Three Odoo versions", "Pick your series on each app page. Odoo 19 has the full range."),
    ("Both", "Community and Enterprise", "Most apps run on both. The few that need Enterprise features say so."),
    ("One-time", "Simple pricing", "Pay once per app, with no subscription. One app is free."),
]
STEPS = [
    ("Tell us what you need", "Send a short note: the problem, your Odoo version and edition."),
    ("We scope it", "You get a clear approach and a fixed price or an hourly estimate."),
    ("We build and test", "Odoo modules written to Odoo standards and tested before delivery."),
    ("Deliver and support", "Installed on your system, with questions answered by email."),
]


def car(items, cls=""):
    """A scroll-snap carousel; `items` are already-rendered HTML cards."""
    return (f'<div class="carousel {cls} reveal" data-carousel><div class="car-track">' + "".join(f'<div class="car-item">{i}</div>' for i in items)
            + '</div><button class="car-btn prev" aria-label="Previous">‹</button><button class="car-btn next" aria-label="Next">›</button><div class="car-dots"></div></div>')


def home():
    root = ""
    featured = sorted((a for a in APPS if a.get("featured")), key=lambda a: RANK[a["id"]])
    hero_shots = [a for a in APPS if a.get("image")][:3]
    stack = "".join(f'<div class="float f{i+1}"><img src="images/{a["image"].split("images/")[1]}" alt="{e(a["title"])}" width="1000" height="500"></div>' for i, a in enumerate(hero_shots))
    stats = "".join(f'<div class="stat reveal"><b>{e(s["value"])}</b><span>{e(s["label"])}</span></div>' for s in D["stats"])

    def n_apps(n):
        c = sum(1 for a in APPS if family(a) == n)
        return f'{c} app{"" if c == 1 else "s"}'
    fams = [f'<a class="card fam" href="apps/?line={c}"><div class="ico">{ico}</div><h3>{n}</h3><p>{d}</p><span class="more">{n_apps(n)} <i>→</i></span></a>' for n, ico, c, d in FAMILIES]
    tech = "".join(f"<span>{t}</span>" for t in ["Odoo 17", "Odoo 18", "Odoo 19", "Python", "OWL", "JavaScript", "PostgreSQL", "QWeb", "Portals", "Payments", "HR & Payroll", "Accounting", "Purchase", "Sales"])
    why = "".join(f'<div class="glass reveal"><div class="num">{n}</div><h3>{t}</h3><p>{p}</p></div>' for n, t, p in VALUE)
    body = f"""
<section class="hero wrap">
 <div class="hero-copy">
  <span class="pill"><i class="dot"></i>{len(APPS)} apps live on the Odoo Apps Store</span>
  <h1>Odoo apps that <em>empower</em> your team and customers.</h1>
  <p class="lead">{NAME} builds production-ready Odoo apps for versions 17, 18 and 19: portals, payments, HR and payroll, dashboards and an AI assistant. Install from the store, or let us build it for you.</p>
  <div class="btn-row"><a class="btn btn-primary" href="apps/">Browse the apps</a><a class="btn btn-ghost" href="contact/">Talk to us →</a></div>
  <ul class="trust"><li>Odoo 17 · 18 · 19</li><li>Community &amp; Enterprise</li><li>OPL-1 licensed</li><li>Store-published</li></ul>
 </div>
 <div class="hero-art" aria-hidden="true"><div class="glow"></div>{stack}</div>
</section>
<section class="wrap stats">{stats}</section>
<section class="wrap"><div class="marquee" aria-hidden="true"><div class="track">{tech}{tech}</div></div></section>
<section class="wrap sec"><div class="sec-head reveal"><span class="eyebrow">Top picks</span><h2>Where most customers start</h2><p>Our most-used portals, payments and AI tools.</p><a class="see" href="apps/">All {len(APPS)} apps →</a></div>
 {car([app_card(a, root, reveal=False, lazy=False) for a in featured])}</section>
<section class="wrap sec"><div class="sec-head reveal"><span class="eyebrow">Product lines</span><h2>Browse by product line</h2><p>Six families, each app doing one job well.</p></div>
 {car(fams)}</section>
<section class="band"><div class="wrap"><div class="sec-head reveal light"><span class="eyebrow">Why NeuralBytea</span><h2>Built to install and forget</h2></div>
 <div class="grid why-grid">{why}</div></div></section>
<section class="wrap"><div class="cta reveal"><h2>Need an Odoo app <span class="grad">built or customised?</span></h2>
 <p>Send a short note about what you need and we will reply with how we would approach it.</p>
 <div class="btn-row center"><a class="btn btn-primary" href="contact/">Contact us</a><a class="btn btn-ghost" href="{STORE}" target="_blank" rel="noopener">Odoo Apps Store ↗</a></div></div></section>"""
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": NAME, "url": SITE_URL + "/", "email": CONTACT["email"],
          "logo": SITE_URL + "/images/mark-512.png", "description": SITE["description"]}
    return page(f"{NAME} | Odoo 17, 18 & 19 Apps and Custom Odoo Development", SITE["description"], "", "home", body,
                f'<script type="application/ld+json">{json.dumps(ld)}</script>')


def apps_page():
    root = "../"
    opt = lambda items: "".join(f'<option value="{v}">{t}</option>' for v, t in items)
    vers_o = opt([("all", "All versions")] + [(s.split(".")[0], f"Odoo {s.split('.')[0]} ({sum(1 for a in APPS if s in dict(vers(a)))})") for s in SERIES])
    line_o = opt([("all", "All lines")] + [(c, f"{n} ({sum(1 for a in APPS if family(a) == n)})") for n, _, c, _ in FAMILIES])
    price_o = opt([("all", "Any price"), ("free", "Free"), ("lt25", "Under $25"), ("25-50", "$25 to $50"), ("50-100", "$50 to $100"), ("gt100", "Over $100")])
    upd_o = opt([("all", "Any date"), ("7", "Past 7 days"), ("30", "Past 30 days"), ("90", "Past 90 days")])
    sort_o = opt([("top", "Top picks"), ("latest", "Latest updated"), ("price-asc", "Price: low to high"), ("price-desc", "Price: high to low"), ("name", "Name A to Z")])
    body = f"""<section class="wrap cat-head"><div><div class="crumb"><a href="{root}">Home</a> / Apps</div><h1>All Odoo apps</h1></div>
<p class="muted">{len(APPS)} apps · Odoo 17, 18 and 19 · every app is on the Odoo Apps Store</p></section>
<section class="wrap">
<form class="filters sticky" role="search" onsubmit="return false"><input id="q" type="search" placeholder="Search apps…" aria-label="Search apps">
<select id="f-ver" aria-label="Odoo version">{vers_o}</select><select id="f-line" aria-label="Product line">{line_o}</select>
<select id="f-price" aria-label="Price">{price_o}</select><select id="f-upd" aria-label="Last updated">{upd_o}</select>
<select id="f-sort" aria-label="Sort by">{sort_o}</select><button type="button" class="reset" id="f-reset">Reset</button></form>
<div class="resultbar"><span id="count"></span><span id="sortnote">Top picks come first</span></div></section>
<section class="wrap"><div class="grid app-grid" id="app-grid">{''.join(app_card(a, root, reveal=False) for a in APPS)}</div>
<p id="none" class="muted center" hidden>No apps match these filters. <a href="#" id="clear" style="color:var(--a)">Clear filters</a></p>
<nav class="pager" id="pager" aria-label="Pagination"></nav></section>"""
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
    shots = app.get("screenshots", [])
    gallery = ('<h2 class="h3">Screenshots</h2><div class="gallery">' + "".join(
        f'<figure><a href="{root}{s["src"]}" target="_blank" rel="noopener"><img src="{root}{s["src"]}" alt="{e(app["title"])}: {e(s["caption"])}" loading="lazy" width="1440" height="900"></a>'
        f'<figcaption>{e(s["caption"])}</figcaption></figure>' for s in shots) + "</div>") if shots else ""
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
  <h2 class="h3">Key features</h2><ul class="feat">{feats}</ul>{gallery}
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
    body = f"""<section class="wrap"><div class="split">
 <aside class="split-l"><div class="crumb">Contact</div><h1>Let's talk</h1>
  <p class="lead">Questions about an app, or need something built? Tell us what you need and we will reply by email.</p>
  <dl class="cinfo"><dt>Email</dt><dd><a href="mailto:{CONTACT['email']}">{CONTACT['email']}</a></dd><dt>Location</dt><dd>{CONTACT['location']}, working remotely worldwide</dd>
   <dt>Engagement</dt><dd>Fixed price or hourly</dd><dt>Apps</dt><dd><a href="{STORE}" target="_blank" rel="noopener">Odoo Apps Store ↗</a></dd></dl>
  <h3>What happens next</h3><ol class="nsteps"><li><b>You send a note</b>What you need and your Odoo version.</li><li><b>We reply by email</b>With how we would approach it.</li><li><b>We agree scope and price</b>Fixed price or hourly, your choice.</li></ol>
 </aside>
 <form class="split-r form" action="https://formspree.io/f/{FORM_ID}" method="POST">
  <h2>Send a message</h2><p class="muted">Helpful to include: your Odoo version and edition, the app you are asking about, and what you want to achieve.</p>
  <label>Your name<input name="name" required placeholder="Jane Doe"></label>
  <label>Email<input type="email" name="_replyto" required placeholder="you@company.com"></label>
  <label>Subject<input name="subject" id="subject" required placeholder="e.g. Question about Vendor Portal Pro"></label>
  <label class="grow">Message<textarea name="message" required placeholder="What do you need?"></textarea></label>
  <input name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" class="hp">
  <button class="btn btn-primary" type="submit">Send message →</button><p class="status" id="status" role="status"></p></form>
</div></section>"""
    return page(f"Contact | {NAME}", f"Contact {NAME} about an Odoo app or custom Odoo development.", "contact/", "contact", body)


def about_page():
    root = "../"
    facts = "".join(f"<li><b>{a}</b><span>{b}</span></li>" for a, b in [(f"{len(APPS)} apps", "on the Odoo Apps Store"), ("Odoo 17 · 18 · 19", "Odoo 19 has the full range"), ("Community + Enterprise", "most apps run on both"), (CONTACT["location"], "working remotely worldwide")])
    lines = "".join(f'<a class="card fam" href="{root}apps/?line={c}"><div class="ico">{ico}</div><h3>{n}</h3><p>{d}</p></a>' for n, ico, c, d in FAMILIES)
    steps = "".join(f'<div class="glass"><h3>{t}</h3><p>{p}</p></div>' for t, p in STEPS)
    why = "".join(f'<div class="card why"><div class="num">{n}</div><h3>{t}</h3><p>{p}</p></div>' for n, t, p in VALUE)
    hire = "".join(f'<div class="card hire"><small>{e(h["k"])}</small><b>{e(h["v"])}</b><p>{e(h["n"])}</p></div>' for h in D["hire"])
    tech = "".join(f'<span class="tag">{t}</span>' for t in ["Odoo 17", "Odoo 18", "Odoo 19", "Python", "Odoo ORM", "OWL", "JavaScript", "QWeb", "PostgreSQL", "Portals", "Payments", "HR & Payroll", "Accounting", "Purchase", "Sales", "Timesheets"])
    body = f"""<section class="wrap about-intro"><div><span class="eyebrow">About {NAME}</span>
 <h1 class="statement">We build Odoo apps that install cleanly and do one job well.</h1>
 <p class="lead">{SITE["description"]}</p><div class="btn-row"><a class="btn btn-primary" href="{root}apps/">Browse the apps</a><a class="btn btn-ghost" href="{root}contact/">Work with us</a></div></div>
 <ul class="facts">{facts}</ul></section>
<section class="wrap sec"><div class="sec-head"><span class="eyebrow">What we build</span><h2>Six product lines</h2></div><div class="grid fam-grid">{lines}</div></section>
<section class="band"><div class="wrap"><div class="sec-head light"><span class="eyebrow">How custom work goes</span><h2>From a note to a working module</h2></div><div class="steps">{steps}</div></div></section>
<section class="wrap sec"><div class="sec-head"><span class="eyebrow">Why NeuralBytea</span><h2>The facts behind the apps</h2></div><div class="grid why-grid">{why}</div></section>
<section class="wrap sec"><div class="sec-head"><span class="eyebrow">Services</span><h2>Apps, custom work and support</h2></div><div class="grid hire-grid">{hire}</div></section>
<section class="wrap sec"><div class="sec-head"><span class="eyebrow">Technology</span><h2>What we work with</h2></div><div class="tags">{tech}</div></section>
<section class="wrap"><div class="cta"><h2>Have an Odoo project in mind?</h2><p>Send a short note and we will reply with how we would approach it.</p>
 <div class="btn-row center"><a class="btn btn-primary" href="{root}contact/">Contact us</a></div></div></section>"""
    return page(f"About {NAME} | Odoo apps and custom development", f"About {NAME}: Odoo apps for versions 17, 18 and 19 and custom Odoo development from {CONTACT['location']}.", "about/", "about", body)


def faq_page():
    root = "../"
    items = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQS)
    body = f"""<section class="wrap faq-head"><span class="eyebrow">FAQ</span><h1>Frequently asked questions</h1>
 <p class="lead">Quick answers about versions, editions, licensing and support.</p>
 <input id="faq-q" type="search" placeholder="Search the questions…" aria-label="Search the questions"></section>
<section class="wrap faq-one" id="faq-list">{items}<p id="faq-none" class="muted center" hidden>No question matches. <a href="{root}contact/" style="color:var(--a)">Ask us directly</a>.</p></section>
<section class="wrap"><div class="ask card"><div><h3>Still have a question?</h3><p class="muted">Send us a note and we will reply by email.</p></div><a class="btn btn-primary" href="{root}contact/">Contact us →</a></div></section>"""
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}
    return page(f"FAQ | {NAME}", "Answers about Odoo versions, Community and Enterprise, licensing, installation, custom development and support.", "faq/", "faq", body,
                f'<script type="application/ld+json">{json.dumps(faq_ld)}</script>')


def legal_page(path, title, desc, sections):
    root = "../"
    toc = "".join(f'<a href="#s{i}">{h}</a>' for i, (h, _) in enumerate(sections))
    secs = "".join(f'<section id="s{i}"><h2>{h}</h2>{b}</section>' for i, (h, b) in enumerate(sections))
    body = f"""<section class="wrap doc-head"><div class="crumb"><a href="{root}">Home</a> / {title}</div><h1>{title}</h1><p class="muted">Last updated: 8 October 2026</p></section>
<section class="wrap doc"><nav class="toc" aria-label="On this page"><b>On this page</b>{toc}</nav><article>{secs}</article></section>"""
    return page(f"{title} | {NAME}", desc, path, "", body)


def privacy_page():
    c = CONTACT["email"]
    S = [
     ("Who we are", f"<p>{NAME} publishes Odoo apps and offers custom Odoo development. We are based in {CONTACT['location']} and work remotely. You can reach us at <a href='mailto:{c}'>{c}</a>. This policy explains what personal data this website handles.</p>"),
     ("What we collect", "<p>Only what you choose to send us, plus a little technical data any website receives:</p><ul><li><b>Contact form:</b> your name, email address, subject and message.</li>" + ("<li><b>Chat assistant:</b> the questions you type into the chat window.</li>" if CHAT_ON else "") + "<li><b>Technical data:</b> your IP address and browser details, which our hosting provider receives when you load a page.</li></ul><p>We do not run analytics or advertising trackers, and this site does not set cookies. " + ("The chat window keeps your current conversation in your browser tab only (session storage) and it is cleared when you close the tab." if CHAT_ON else "") + "</p>"),
     ("How we use it", "<p>We use your contact details and message only to reply to you and to handle your request or project. We do not sell your data and we do not use it for marketing you did not ask for.</p>"),
     ("Who processes it", "<ul><li><b>Formspree</b> receives the contact form and forwards it to our email inbox.</li><li><b>GitHub Pages</b> hosts this website and may keep standard server logs.</li><li><b>Google Fonts</b> serves the fonts, so your browser requests them from Google.</li>" + (("<li><b>Cloudflare</b> runs the chat service that receives your chat questions, and <b>Groq</b> generates the answer. Do not type passwords or private data into the chat. We do not store chat conversations.</li>" if CHAT_ENDPOINT else "<li><b>Groq</b> receives your chat questions directly from your browser to generate the answer. Do not type passwords or private data into the chat. We do not store chat conversations.</li>") if CHAT_ON else "") + "</ul><p>Links to the Odoo Apps Store and other sites take you away from this website. Their own privacy policies apply there.</p>"),
     ("How long we keep it", "<p>We keep emails for as long as needed to answer you, deliver any work we agree, and keep ordinary business records. You can ask us to delete them sooner.</p>"),
     ("Your rights", f"<p>You can ask us what data we hold about you, ask us to correct or delete it, or object to how we use it. Email <a href='mailto:{c}'>{c}</a> and we will reply.</p>"),
     ("Children", "<p>This website is not aimed at children and we do not knowingly collect their data.</p>"),
     ("Changes", "<p>If we change this policy we will update the date at the top of this page.</p>")]
    return legal_page("privacy/", "Privacy Policy", f"How {NAME} handles personal data on this website: contact form, hosting and fonts.", S)


def terms_page():
    c = CONTACT["email"]
    S = [
     ("Using this website", f"<p>This website describes the Odoo apps and services of {NAME}. By using it you agree to these terms. If you do not agree, please do not use the site.</p>"),
     ("Apps and licences", "<p>Our apps are sold and downloaded through the Odoo Apps Store. Paid apps are licensed under the Odoo Proprietary License v1 (OPL-1) and the N-Genius payment provider under LGPL-3, as shown on each app page. The Odoo Apps Store terms apply to purchases.</p>"),
     ("Information on this site", "<p>We work to keep app details, versions and prices accurate, but the Odoo Apps Store listing is the source of truth for the current price, version and licence of an app.</p>"),
     ("Custom work", "<p>Custom development is agreed separately in writing, including scope, price and delivery. Nothing on this website is a binding offer.</p>"),
     ("Intellectual property", f"<p>The {NAME} name, logo, text and screenshots are ours. Odoo is a trademark of Odoo S.A. and other product names belong to their owners.</p>"),
     ("No warranty and liability", "<p>This website is provided as it is. To the extent the law allows, we are not liable for losses from using the website or relying on its content.</p>"),
     ("Governing law", "<p>These terms are governed by the laws of Pakistan.</p>"),
     ("Contact", f"<p>Questions about these terms: <a href='mailto:{c}'>{c}</a>.</p>")]
    return legal_page("terms/", "Terms of Use", f"Terms for using the {NAME} website and how our Odoo apps are licensed and sold.", S)


def sitemap_page():
    root = "../"
    col = lambda title, links: f'<div class="card sm"><h3>{title}</h3>' + "".join(f'<a href="{h}">{t}</a>' for t, h in links) + "</div>"
    pages = col("Pages", [("Home", root), ("All apps", root + "apps/"), ("About", root + "about/"), ("FAQ", root + "faq/"), ("Contact", root + "contact/")])
    lines = col("Product lines", [(n, f"{root}apps/?line={c}") for n, _, c, _ in FAMILIES])
    legal = col("Legal", [("Privacy Policy", root + "privacy/"), ("Terms of Use", root + "terms/"), ("XML sitemap", root + "sitemap.xml")])
    apps = col(f"All {len(APPS)} apps", [(a["title"], f"{root}apps/{slug(a)}/") for a in sorted(APPS, key=lambda x: x["title"])])
    body = f"""<section class="wrap doc-head"><div class="crumb"><a href="{root}">Home</a> / Sitemap</div><h1>Sitemap</h1><p class="muted">Every page on this website.</p></section>
<section class="wrap"><div class="sm-grid"><div>{pages}{lines}{legal}</div><div>{apps}</div></div></section>"""
    return page(f"Sitemap | {NAME}", f"All pages and apps on the {NAME} website.", "sitemap/", "", body)


def write_knowledge():
    """worker/src/knowledge.js: everything the chat assistant may say, generated from the same data as the site."""
    apps = []
    for a in APPS:
        v = vers(a)
        m = meta(a)
        apps.append({
            "id": a["id"], "title": a["title"], "line": family(a), "edition": m["edition"], "licence": m["licence"],
            "versions": [{"odoo": s.split(".")[0], "price": price_label(i), "module_version": i["version"].split(".", 2)[2], "store": i["url"]} for s, i in v],
            "summary": a["short_desc"], "about": a["full_desc"], "features": a.get("highlights", []), "works_with": a.get("modules", []),
            "page": f"{SITE_URL}/apps/{slug(a)}/"})
    facts = [
        "Apps are built for Odoo 17, 18 and 19; Odoo 19 has the full range, Odoo 17 has only Employee Loan Pro, Attendance Leave Gantt and Sales & Payment Dashboard.",
        "Most apps run on Community and Enterprise; Employee Loan Pro, Attendance Leave Gantt and Payroll Dashboard Pro need Enterprise features (Payroll or Contracts).",
        "Install from the Odoo Apps Store like any app. Paid apps: one-time price per app, OPL-1 licence, no subscription. N-Genius payment provider is free (LGPL-3).",
        "Custom development: custom Odoo modules, portals, payment and API integrations, dashboards and migrations, fixed price or hourly.",
        "Support: contact form or the app's store page; replies by email.",
        "Employee Self Service needs internal users. The AI Chat Assistant uses the customer's own AI provider and API key and respects each user's access rights."]
    company = {
        "name": NAME, "site": SITE_URL, "email": CONTACT["email"], "location": CONTACT["location"], "store": STORE,
        "contact_page": SITE_URL + "/contact/", "facts": facts}
    out = ROOT / "worker/src/knowledge.js"
    out.write_text("// GENERATED by build.py from data/portfolio_data.yaml and data/versions.yaml. Do not edit.\n"
                   f"export const APPS = {json.dumps(apps, ensure_ascii=False, indent=1)};\n"
                   f"export const COMPANY = {json.dumps(company, ensure_ascii=False, indent=1)};\n", encoding="utf-8")


def not_found():
    # Absolute root-relative assets so it works at any depth on a domain root.
    body = '<section class="wrap page-hero center"><h1>404</h1><p class="lead">That page does not exist.</p><a class="btn btn-primary" href="/">Back to home</a></section>'
    out = page(f"Page not found | {NAME}", "Page not found", "404.html", "", body).replace("index,follow,max-image-preview:large", "noindex,follow")
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
    for f in ("style.css", "site.js", "chat.js"):
        shutil.copy(ROOT / "src" / f, OUT / "assets" / f)
    if CHAT_KEY:
        (OUT / "assets/chat").mkdir(parents=True, exist_ok=True)
        for f in ("prompt.js", "knowledge.js"):
            shutil.copy(ROOT / "worker/src" / f, OUT / "assets/chat" / f)
    write("index.html", home())
    write("apps/index.html", apps_page())
    for i, a in enumerate(APPS):
        write(f"apps/{slug(a)}/index.html", app_page(i, a))
    write("contact/index.html", contact_page())
    write("about/index.html", about_page())
    write("faq/index.html", faq_page())
    write("privacy/index.html", privacy_page())
    write("terms/index.html", terms_page())
    write("sitemap/index.html", sitemap_page())
    write("404.html", not_found())
    write_knowledge()
    urls = ["", "apps/", "about/", "faq/", "contact/", "privacy/", "terms/", "sitemap/"] + [f"apps/{slug(a)}/" for a in APPS]
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
