# NeuralByte site

Content lives in `data/portfolio_data.yaml`. `python3 build.py` pre-renders every page into `site/`
(home, apps, one page per app, contact, 404, sitemap, robots). No runtime data loading, all links relative.

    pip install pyyaml
    python3 build.py && cd site && python3 -m http.server 8000

Custom domain: `SITE_URL=https://yourdomain.com python3 build.py` (writes CNAME). In CI set a repo variable `SITE_URL`.
Deploy: repo Settings > Pages > Source = GitHub Actions (workflow in .github/workflows/deploy.yml).
Add an app: append to `projects:` in the YAML, drop a 1000x500 banner in `src/static/images/apps/`, rebuild.


## Pages
Home, Apps (filters, sort, pagination), per-app pages, About, FAQ, Contact, Privacy Policy, Terms of Use, Sitemap, 404.
`scan_versions.py` refreshes versions, prices and update dates; `tools/` holds the screenshot driver and banner/icon generator.
