#!/usr/bin/env python3
"""Scan the per-version NeuralBytea repos and write data/versions.yaml.

For every module found under odoo{17,18,19,20}/env/env_neural/addons/Neural_Byte_Modules
it records the manifest version and price, and keeps a version only if the module's
Odoo Apps Store page for that series really exists (HTTP 200).

    python3 scan_versions.py                 # uses ~/development/odoo_proj
    ODOO_PROJ=/path/to/odoo_proj python3 scan_versions.py
    python3 scan_versions.py --no-store      # skip the store check (trust the manifests)
"""
import ast, datetime, os, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import yaml

PROJ = Path(os.environ.get("ODOO_PROJ", Path.home() / "development/odoo_proj"))
SERIES = ["17.0", "18.0", "19.0", "20.0"]
# technical name in the repo -> technical name on the store, where they differ
STORE_NAME = {}
# only NeuralBytea modules are ever listed: BBT (Big Binary Tech) modules sit in their own folder and use the bbt_ prefix
NOT_OURS = ("bbt_",)
# modules in the repos that must not be listed (not published)
# payment_provider_ngenius is a different author's Odoo 18 module that sits in the Odoo 18 repo; it is not a NeuralBytea app
SKIP = {"nb_employee_portal", "payment_provider_ngenius"}
OUT = Path(__file__).parent / "data/versions.yaml"


SRC_EXT = {".py", ".xml", ".js", ".scss", ".css", ".csv", ".po"}


def last_updated(module_dir):
    """Newest mtime of real source files (not store artwork, docs or caches)."""
    newest = 0
    for f in module_dir.rglob("*"):
        if f.suffix in SRC_EXT and "__pycache__" not in f.parts and "node_modules" not in f.parts and "description" not in f.parts and "docs" not in f.parts:
            newest = max(newest, f.stat().st_mtime)
    return datetime.date.fromtimestamp(newest).isoformat() if newest else None


def manifests(series):
    base = PROJ / f"odoo{series.split('.')[0]}/env/env_neural/addons/Neural_Byte_Modules"
    for m in base.rglob("__manifest__.py"):
        if "node_modules" in m.parts or "BBT" in m.parts:
            continue
        try:
            mf = ast.literal_eval(m.read_text())
            mf["_updated"] = last_updated(m.parent)
            yield m.parent.name, mf
        except (ValueError, SyntaxError, OSError) as ex:
            print(f"skip {m}: {ex}", file=sys.stderr)


def store_info(series, name):
    """(published?, version shown on the store page). The store only exposes the version through the uploaded description,
    which is still what a customer gets, so it is preferred over the repo manifest (the repo can be ahead of the upload)."""
    url = f"https://apps.odoo.com/apps/modules/{series}/{name}/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=25)
        html = r.read().decode("utf8", "ignore")
    except urllib.error.URLError:
        return False, None
    m = re.search(r"Odoo\s+%s\s*(?:&nbsp;|\s)*[|·&middot;]+(?:&nbsp;|\s)*v(%s\.\d+\.\d+\.\d+)" % (re.escape(series), re.escape(series.split(".")[0] + ".0")), html)
    return True, (m.group(1) if m else None)


def main():
    check = "--no-store" not in sys.argv
    found = {}
    for s in SERIES:
        for name, mf in manifests(s):
            sname = STORE_NAME.get(name, name)
            if sname in SKIP or name in SKIP or name.startswith(NOT_OURS):
                continue
            ver = str(mf.get("version", ""))
            # a few 17.0 copies still carry an 18.0 manifest: not a real 17.0 port
            if not ver.startswith(s.split(".")[0] + "."):
                continue
            found.setdefault(sname, {})[s] = {"version": ver, "price": mf.get("price"), "updated": mf["_updated"], "license": mf.get("license")}
    jobs = [(n, s) for n, v in found.items() for s in v]
    with ThreadPoolExecutor(8) as ex:
        info = dict(zip(jobs, ex.map(lambda j: store_info(j[1], j[0]) if check else (True, None), jobs)))
    out = {}
    for n, v in sorted(found.items()):
        live = {}
        for s, d in sorted(v.items()):
            ok, store_ver = info[(n, s)]
            if not ok:
                continue
            e = {**d, "url": f"https://apps.odoo.com/apps/modules/{s}/{n}/"}
            if store_ver and store_ver != d["version"]:      # the version badge on the store page differs from the repo manifest
                e["store_page_version"] = store_ver           # reported only; the site keeps showing the repo version
            live[s] = e
        if live:
            out[n] = live
    OUT.write_text(yaml.safe_dump(out, sort_keys=False))
    for n, v in out.items():
        print(f"{n:38}", " ".join(f"{s}:{d['version'].split('.',2)[2]}${d['price']}" + (f"(store page says {d['store_page_version'].split('.',2)[2]})" if d.get('store_page_version') else "") for s, d in v.items()))


if __name__ == "__main__":
    main()
