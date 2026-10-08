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

## Chat assistant (two ways to run it)
1. **GitHub Pages only (direct mode):** add a repository secret named `GROQ_API_KEY` (Settings > Secrets and variables > Actions), then re-run the "Deploy site" workflow.
   The key is injected at build time, never committed. It is camouflaged in the page but a visitor with DevTools can still read it, so use a dedicated free-tier key.
2. **Cloudflare Worker proxy (recommended, key stays server-side):** see `worker/README.md`. If `site.chat_endpoint` is set it takes priority over direct mode.
Without either, the chat bubble is simply not shown.
