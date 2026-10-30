#!/usr/bin/env python3
"""Refresh every module already on the website from the current manifests, banners and screenshots in the neural repos.

    python3 tools/refresh_modules.py --dry-run     # show what would change
    python3 tools/refresh_modules.py               # apply, then run scan_versions.py and build.py

Updated from the repo: title, summary, about text, price/role/metric, feature list, banner, screenshot gallery (+ captions).
Kept from the site: id, product line/tags, featured, position, "new" badge, tech stack.
Safety rules: a feature list is only replaced when the new one is at least as good (>= 4 items, or not shorter);
the page title can be overridden below; removed screenshots are deleted from the site folder.
"""
import argparse, ast, hashlib, os, re, shutil, sys
from pathlib import Path
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PROJ = Path(os.environ.get("ODOO_PROJ", Path.home() / "development/odoo_proj"))
DATA = ROOT / "data/portfolio_data.yaml"
IMG = ROOT / "src/static/images/apps"
ABOUT_REFRESH = {"nb_mcp_server"}   # about text is taken from the repo only for these (it was rewritten with the rename); other intros are not reliable to auto-extract
TITLE_OVERRIDE = {"payment_ngenius": "N-Genius Payment Provider"}  # manifest name is "Payment Provider: N-Genius"
FRIENDLY = {"base": "Contacts", "base_setup": "Settings", "mail": "Discuss", "contacts": "Contacts", "account": "Invoicing", "hr": "Employees",
            "portal": "Portal", "website_slides": "eLearning", "spreadsheet_dashboard": "Dashboards", "web": "Web"}
clean = lambda s: re.sub(r"\s+", " ", s).strip()


VERS = yaml.safe_load((ROOT / "data/versions.yaml").read_text()) if (ROOT / "data/versions.yaml").exists() else {}


def find(mod, prefer="newest"):
    """Module folder for a PUBLISHED series (versions.yaml), falling back to 19 then 18. BBT folders are never used.
    prefer="newest": newest series (banner); prefer="text": 19 first, then 20, 18 (title, summary, features: one wording for all series)."""
    pub = sorted((k.split(".")[0] for k in VERS.get(mod, {})), key=int, reverse=True)
    order = pub if prefer == "newest" else [x for x in ("19", "20", "18", "17") if x in pub]
    for v in order + [x for x in ("19", "18") if x not in order]:
        for m in (PROJ / f"odoo{v}/env/env_neural/addons/Neural_Byte_Modules").rglob(f"{mod}/__manifest__.py"):
            if "node_modules" not in m.parts and "BBT" not in m.parts:
                return m.parent
    return None


def multi(mod):
    return len(VERS.get(mod, {})) > 1


def neutral(text, mod):
    """An app that spans several Odoo series must not claim one of them: 'every Odoo 20 list view' -> 'every Odoo list view'."""
    return re.sub(r"Odoo (17|18|19|20)(\.0)?\b", "Odoo", text) if multi(mod) else text


def features(desc):
    """Feature list from the module description: 'Name: text' bullets, else every top-level bullet line."""
    named = [f"{clean(a)}: {clean(b)}" for a, b in re.findall(r"^\s*\*\s+([^:\n]+):\s*(.+)$", desc, re.M)]
    if len(named) >= 4:
        return named
    out = []
    for ln in re.findall(r"^[*-]\s+(.+)$", desc, re.M):          # top-level bullets only (no indentation)
        t = clean(re.sub(r"[*`]{1,2}", "", ln))
        if 15 <= len(t) <= 230:
            out.append(t)
    return out[:8]


def jpg(src, dst, size=None, q=84):
    im = Image.open(src).convert("RGB")
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=q, optimize=True)


def refresh(p, apply):
    mod, d = p["id"], find(p["id"], "text")
    bd = find(p["id"], "newest") or d      # banner comes from the newest published series
    if not d:
        return None, ["module not found in the repos, left as it is"]
    mf = ast.literal_eval((d / "__manifest__.py").read_text())
    sd = d / "static/description"
    html = (sd / "index.html").read_text() if (sd / "index.html").exists() else ""
    alts = {m.group(1): clean(m.group(2)) for m in re.finditer(r'<img[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"', html)}
    desc = mf.get("description", "")
    paras = [clean(x) for x in re.split(r"\n\s*\n", desc.strip()) if clean(x) and not set(clean(x)) <= set("=-")]
    intro = paras[1] if len(paras) > 1 else ""
    prose = len(intro) > 80 and not re.search(r"<[a-z/]|---|===|\s\*\s|^[*-]\s", intro)   # a real sentence paragraph, not a heading, list or HTML
    about = intro if (prose and mod in ABOUT_REFRESH) else p["full_desc"]
    price = float(mf.get("price") or 0)
    pstr = "Free" if not price else ("$%g" % price if price == int(price) else "$%.2f" % price)
    new = dict(p)
    new["_src"] = str(d.relative_to(PROJ)).split("/")[0]
    new["title"] = TITLE_OVERRIDE.get(mod) or clean(mf["name"].split("|")[0])
    new["short_desc"] = neutral(clean(mf["summary"]), mod)
    new["full_desc"] = neutral(re.sub(r"\*\*", "", about), mod)
    edition, _, lic = [x.strip() for x in (p["role"].split("·") + ["", ""])[:3]]
    new["role"] = f"{edition} · {pstr} · {mf.get('license') or lic}"     # edition stays as on the site, price and licence follow the manifest
    new["metric"] = pstr if p.get("metric", "").startswith(("$", "Free")) else p.get("metric")
    feats = features(desc)
    old_f = p.get("highlights", [])
    new["highlights"] = feats if (len(feats) >= 4 or len(feats) >= len(old_f)) and feats else old_f
    shots = []
    for f in sorted(os.listdir(sd)):
        if f.endswith(".png") and not f.startswith(("more-", "banner", "icon", "svc-")) and "logo" not in f:
            cap = re.sub(r"\s+in Odoo( \d+)?$", "", alts.get(f, f[:-4].replace("-", " ").capitalize()))
            shots.append({"src": f"images/apps/shots/{mod}/{f[:-4]}.jpg", "caption": cap, "_f": f})
    if p.get("screenshots") and shots:      # only refresh galleries that already exist on the site
        new["screenshots"] = [{k: v for k, v in s.items() if k != "_f"} for s in shots]
    ban = bd / "static/description/banner.png"
    if ban.exists():
        sha = hashlib.sha1(ban.read_bytes()).hexdigest()[:12]
        site_jpg = IMG / f"{mod}.jpg"
        was = p.get("banner_sha")
        if was != sha and (was or not site_jpg.exists() or ban.stat().st_mtime > site_jpg.stat().st_mtime):
            new["banner_sha"] = sha
            banner_changed = True
        else:
            new["banner_sha"] = sha
            banner_changed = False
    else:
        banner_changed = False
    changes = []
    if banner_changed:
        changes.append("banner/logo changed in the module")
    for k, label in (("title", "title"), ("short_desc", "summary"), ("full_desc", "about text"), ("role", "price/edition")):
        if new[k] != p.get(k):
            changes.append(f"{label}: '{str(p.get(k))[:70]}' -> '{str(new[k])[:70]}'")
    if new["highlights"] != old_f:
        changes.append(f"features: {len(old_f)} -> {len(new['highlights'])}: " + " | ".join(h[:38] for h in new["highlights"][:3]) + " ...")
    elif feats and feats != old_f:
        changes.append(f"features kept ({len(old_f)}); the new description gives only {len(feats)}")
    old_s = [s["src"] for s in p.get("screenshots", [])]
    if p.get("screenshots") and [s["src"] for s in new.get("screenshots", [])] != old_s:
        changes.append(f"screenshots: {len(old_s)} -> {len(new.get('screenshots', []))}")
    if apply:
        ban = bd / "static/description/banner.png"
        if ban.exists() and banner_changed:
            jpg(ban, IMG / f"{mod}.jpg", (1000, 500), 88)
        if p.get("screenshots") and shots:
            shutil.rmtree(IMG / "shots" / mod, ignore_errors=True)
            for s in shots:
                jpg(sd / s["_f"], IMG / "shots" / mod / (s["_f"][:-4] + ".jpg"))
    new.pop("_src", None)
    return new, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    data = yaml.safe_load(DATA.read_text())
    n = 0
    for i, p in enumerate(data["projects"]):
        new, ch = refresh(p, not a.dry_run)
        if new is None:
            print(f"- {p['id']}: {ch[0]}")
            continue
        data["projects"][i] = new
        if ch:
            n += 1
            print(f"\n## {p['id']}")
            for c in ch:
                print("   ", c)
    if not a.dry_run:
        DATA.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000))
    print(f"\n{'would change' if a.dry_run else 'changed'}: {n} of {len(data['projects'])} apps")


if __name__ == "__main__":
    main()
