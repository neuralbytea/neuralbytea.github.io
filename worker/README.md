# NeuralBytea chat assistant (Cloudflare Worker)

A small proxy between the website's chat widget and Groq. **The Groq API key lives only here, as a secret.**
It is never in the website's HTML/JS, never in git.

What it does: only accepts requests from https://neuralbytea.github.io, limits message size and history,
rate-limits per visitor, answers only from `src/knowledge.js` (generated from the site data on every build),
and caches identical first questions.

## Deploy (about 5 minutes, free Cloudflare account)
```bash
cd worker
npx wrangler login                      # opens the browser once
npx wrangler secret put GROQ_API_KEY    # paste the Groq key when asked (stored encrypted on Cloudflare)
npx wrangler deploy                     # prints https://neuralbytea-chat.<your-subdomain>.workers.dev
```
Then give the site that URL: in `data/portfolio_data.yaml` set `site.chat_endpoint: "<the URL>"`
(or set the GitHub repo variable `CHAT_ENDPOINT`), commit and push. The chat bubble appears on every page.

## Keep it healthy
- Re-run `npx wrangler deploy` after the app list changes (`python3 ../build.py` regenerates `src/knowledge.js`).
- Add a Cloudflare rate-limiting rule for the Worker URL (Security > WAF) for a hard per-IP cap.
- Groq free tier: 8,000 tokens/min and 1,000 requests/day per model. Each chat costs about 1,300 tokens, so roughly 5 chats a minute.
  When the limit is hit the widget tells the visitor to retry or use the contact form. A paid Groq tier removes the limit.
- To change the model: `MODEL` in `wrangler.toml` (`openai/gpt-oss-20b` default, `openai/gpt-oss-120b` is stronger but slower).

## Test locally
```bash
GROQ_API_KEY=... node test/e2e.mjs                 # 17 checks against the real Groq API (takes ~3 min, paced for the free tier)
GROQ_API_KEY=... node test/dev-server.mjs          # Worker on http://localhost:8787
CHAT_ENDPOINT=http://localhost:8787 python3 ../build.py   # build the site with the widget pointed at it
```
Never build with a local endpoint and commit the result: `site/` is git-ignored and CI builds from `data/portfolio_data.yaml`.
