#!/usr/bin/env python3
"""Add (or refresh) one or more modules on the website from the neural Odoo repos.

    python3 tools/add_module.py nb_mcp_server --line "AI Assistant" --tags "AI Assistant,MCP,Claude" --new --featured --position 4
    python3 tools/add_module.py nb_elearning_video --line "Education" --tags "Education,eLearning,Video"

It finds the module under odoo19 (falling back to odoo18) env_neural/addons/Neural_Byte_Modules, reads the manifest,
store description (feature list, screenshot captions), banner and screenshots, writes web-sized images under
src/static/images/apps and replaces the entry (by id) in data/portfolio_data.yaml. Then run scan_versions.py and build.py.
The store-version check in scan_versions.py hides a module that is not published yet, so adding it early is harmless.
"""
import argparse, ast, os, re, sys
from pathlib import Path
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PROJ = Path(os.environ.get("ODOO_PROJ", Path.home() / "development/odoo_proj"))
DATA = ROOT / "data/portfolio_data.yaml"
IMG = ROOT / "src/static/images/apps"
FRIENDLY = {"base": "Contacts", "base_setup": "Settings", "mail": "Discuss", "contacts": "Contacts", "account": "Invoicing", "hr": "Employees",
            "portal": "Portal", "website_slides": "eLearning", "spreadsheet_dashboard": "Dashboards", "web": "Web"}


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def find(mod):
    for v in ("19", "18"):
        base = PROJ / f"odoo{v}/env/env_neural/addons/Neural_Byte_Modules"
        for m in base.rglob(f"{mod}/__manifest__.py"):
            if "node_modules" not in m.parts:
                return m.parent
    sys.exit(f"{mod}: not found in the odoo19 or odoo18 neural repos")


def jpg(src, dst, size=None, q=84):
    im = Image.open(src).convert("RGB")
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=q, optimize=True)


def build(mod, a):
    d = find(mod)
    mf = ast.literal_eval((d / "__manifest__.py").read_text())
    sd = d / "static/description"
    html = (sd / "index.html").read_text() if (sd / "index.html").exists() else ""
    alts = {m.group(1): clean(m.group(2)) for m in re.finditer(r'<img[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"', html)}
    desc = mf.get("description", "")
    paras = [clean(p) for p in re.split(r"\n\s*\n", desc.strip()) if clean(p) and not set(clean(p)) <= set("=-")]
    full = next((p for p in paras[1:] if not p.startswith("*") and len(p) > 80), mf.get("summary", ""))
    bullets = [f"{clean(x)}: {clean(y)}" for x, y in re.findall(r"^\s*\*\s+([^:\n]+):\s*(.+)$", desc, re.M)]
    price = float(mf.get("price") or 0)
    pstr = "Free" if not price else ("$%g" % price if price == int(price) else "$%.2f" % price)
    jpg(sd / "banner.png", IMG / f"{mod}.jpg", (1000, 500), 88)
    shots = []
    for f in sorted(os.listdir(sd)):
        if f.endswith(".png") and not f.startswith(("more-", "banner", "icon", "svc-")):
            jpg(sd / f, IMG / "shots" / mod / (f[:-4] + ".jpg"))
            cap = re.sub(r"\s+in Odoo( \d+)?$", "", alts.get(f, f[:-4].replace("-", " ").capitalize()))
            shots.append({"src": f"images/apps/shots/{mod}/{f[:-4]}.jpg", "caption": cap})
    series = re.match(r"(\d+)\.", str(mf["version"])).group(1)
    e = {"id": mod, "title": clean(mf["name"].split("|")[0]), "category": "odoo", "featured": a.featured, "year": 2026, "client": "NeuralBytea",
         "role": f"Community & Enterprise · {pstr} · {mf.get('license', 'OPL-1')}", "odoo_version": f"Odoo {series}.0", "image": f"assets/images/apps/{mod}.jpg",
         "store_url": f"https://apps.odoo.com/apps/modules/{series}.0/{mod}/", "short_desc": clean(mf["summary"]), "metric": pstr,
         "metric_label": "one-time price" if price else "free", "full_desc": full, "tags": [t.strip() for t in a.tags.split(",")],
         "modules": [FRIENDLY.get(x, x.replace("nb_", "").replace("_", " ").title()) for x in mf.get("depends", [])],
         "tech_stack": ["Python", "Odoo ORM", "QWeb", "OWL / JavaScript"], "highlights": bullets, "screenshots": shots}
    if a.new:
        e["new"] = True
    return e, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modules", nargs="+")
    ap.add_argument("--line", required=True, help='product line, e.g. "AI Assistant" or "Education"')
    ap.add_argument("--tags", default="")
    ap.add_argument("--featured", action="store_true")
    ap.add_argument("--new", action="store_true", help='show a "New" badge')
    ap.add_argument("--position", type=int, default=None, help="index in the list (0 = first); default: end")
    a = ap.parse_args()
    a.tags = a.tags or a.line
    if a.tags.split(",")[0].strip() != a.line:
        sys.exit("the first tag must equal --line (it decides the product line)")
    data = yaml.safe_load(DATA.read_text())
    for mod in a.modules:
        entry, d = build(mod, a)
        old = next((p for p in data["projects"] if p["id"] == mod), None)
        if old:
            data["projects"].remove(old)
        pos = a.position if a.position is not None else len(data["projects"])
        data["projects"].insert(min(pos, len(data["projects"])), entry)
        print(f"{'updated' if old else 'added'} {mod} <- {d.relative_to(PROJ)}  [{entry['title']}] {entry['metric']}  {len(entry['screenshots'])} screenshots, {len(entry['highlights'])} features")
    DATA.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000))
    print("total apps:", len(data["projects"]))


if __name__ == "__main__":
    main()
