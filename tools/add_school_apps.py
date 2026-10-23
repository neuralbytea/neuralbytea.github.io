#!/usr/bin/env python3
"""Add the neural_school (school + course management) modules to the website data.

Reads each module's __manifest__.py and static/description (banner, screenshots, alt text) from
    <ODOO_PROJ>/odoo19/env/env_neural/addons/Neural_Byte_Modules/neural_school
and (re)writes their entries in data/portfolio_data.yaml, plus web-sized images under src/static/images/apps.
Safe to re-run: entries are replaced by id, nothing else in the YAML changes.

    python3 tools/add_school_apps.py
"""
import ast, os, re, sys
from pathlib import Path
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PROJ = Path(os.environ.get("ODOO_PROJ", Path.home() / "development/odoo_proj"))
SRC = PROJ / "odoo19/env/env_neural/addons/Neural_Byte_Modules/neural_school"
DATA = ROOT / "data/portfolio_data.yaml"
IMG = ROOT / "src/static/images/apps"

# order on the site: the suite first, then the core, then the rest by topic
ORDER = ["nb_school_management_system", "nb_school_core", "nb_school_admission", "nb_school_fees", "nb_school_portal", "nb_school_hr",
         "nb_school_timetable", "nb_school_dashboard", "nb_course_core", "nb_course_admission", "nb_course_fees"]
FEATURED = {"nb_school_management_system", "nb_course_core"}
FRIENDLY = {"base": "Contacts", "mail": "Discuss", "contacts": "Contacts", "account": "Invoicing", "hr": "Employees", "portal": "Portal",
            "spreadsheet_dashboard": "Dashboards", "base_install_request": "Install Request"}
# a school app can only be searched for by what it is, so give each one a few plain tags
TAGS = {
    "nb_school_management_system": ["Education", "School", "Suite"], "nb_school_core": ["Education", "School", "Students"],
    "nb_school_admission": ["Education", "School", "Admissions"], "nb_school_fees": ["Education", "School", "Fees"],
    "nb_school_portal": ["Education", "School", "Portals"], "nb_school_hr": ["Education", "School", "Teachers"],
    "nb_school_timetable": ["Education", "School", "Timetable"], "nb_school_dashboard": ["Education", "School", "Dashboards"],
    "nb_course_core": ["Education", "Courses", "Training"], "nb_course_admission": ["Education", "Courses", "Admissions"],
    "nb_course_fees": ["Education", "Courses", "Fees"]}


TITLES = {m: re.sub(r"\s+", " ", ast.literal_eval((SRC / m / "__manifest__.py").read_text())["name"].split("|")[0]).strip() for m in ORDER}


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def to_jpg(src, dst, size=None, q=84):
    im = Image.open(src).convert("RGB")
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=q, optimize=True)


def build(mod):
    d = SRC / mod
    mf = ast.literal_eval((d / "__manifest__.py").read_text())
    sd = d / "static/description"
    html = (sd / "index.html").read_text()
    alts = {m.group(1): clean(m.group(2)) for m in re.finditer(r'<img[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"', html)}
    desc = mf.get("description", "")
    paras = [clean(p) for p in re.split(r"\n\s*\n", desc.strip()) if clean(p) and not set(clean(p)) <= set("=-")]
    full = next((p for p in paras[1:] if not p.startswith("*") and len(p) > 80), mf.get("summary", ""))
    bullets = [f"{clean(a)}: {clean(b)}" for a, b in re.findall(r"^\s*\*\s+([^:\n]+):\s*(.+)$", desc, re.M)]
    title = clean(mf["name"].split("|")[0])
    price = float(mf.get("price") or 0)
    pstr = "Free" if not price else "$%g" % price if price == int(price) else "$%.2f" % price
    # banner + screenshots
    to_jpg(sd / "banner.png", IMG / f"{mod}.jpg", (1000, 500), 88)
    shots = []
    for f in sorted(os.listdir(sd)):
        if f.endswith(".png") and not f.startswith(("more-", "banner", "icon", "svc-")):
            to_jpg(sd / f, IMG / "shots" / mod / (f[:-4] + ".jpg"))
            cap = alts.get(f, f[:-4].replace("-", " ").capitalize())
            cap = re.sub(r"\s+in Odoo$", "", cap)
            shots.append({"src": f"images/apps/shots/{mod}/{f[:-4]}.jpg", "caption": cap})
    deps = [TITLES.get(x) or FRIENDLY.get(x, x.replace("_", " ").title()) for x in mf.get("depends", [])]
    return {
        "id": mod, "title": title, "category": "odoo", "featured": mod in FEATURED, "year": 2026, "client": "NeuralBytea",
        "role": f"Community & Enterprise · {pstr} · {mf.get('license', 'OPL-1')}", "odoo_version": "Odoo 19.0", "image": f"assets/images/apps/{mod}.jpg",
        "store_url": f"https://apps.odoo.com/apps/modules/19.0/{mod}/", "short_desc": clean(mf["summary"]), "metric": pstr,
        "metric_label": "one-time price" if price else "free with the school suite", "full_desc": full, "tags": TAGS[mod],
        "modules": deps, "tech_stack": ["Python", "Odoo ORM", "QWeb", "OWL / JavaScript"], "highlights": bullets, "screenshots": shots}


def main():
    new = {m: build(m) for m in ORDER}
    data = yaml.safe_load(DATA.read_text())
    keep = [p for p in data["projects"] if p["id"] not in new]
    # put the suite and core right after the first four apps so they show among the top picks
    at = min(4, len(keep))
    data["projects"] = keep[:at] + [new[m] for m in ORDER] + keep[at:]
    DATA.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000))
    n_shots = sum(len(v["screenshots"]) for v in new.values())
    print(f"{len(new)} apps written, {n_shots} screenshots, total apps now {len(data['projects'])}")
    for m in ORDER:
        v = new[m]
        print(f"  {m:30} {v['metric']:7} shots={len(v['screenshots'])} bullets={len(v['highlights'])}  {v['title']}")


if __name__ == "__main__":
    main()
