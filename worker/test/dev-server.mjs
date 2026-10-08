// Local dev server: serves the Worker on http://localhost:8787 so the website widget can be tried end to end.
//   GROQ_API_KEY=... node test/dev-server.mjs      (then build the site with CHAT_ENDPOINT=http://localhost:8787)
import http from "node:http";
import { handle } from "../src/index.js";
const env = { GROQ_API_KEY: process.env.GROQ_API_KEY, ALLOW_LOCALHOST: "1" };
http.createServer(async (req, res) => {
  const chunks = []; for await (const c of req) chunks.push(c);
  const r = await handle(new Request("http://localhost:8787" + req.url, { method: req.method, headers: req.headers, body: ["GET", "HEAD", "OPTIONS"].includes(req.method) ? undefined : Buffer.concat(chunks) }), env);
  res.writeHead(r.status, Object.fromEntries(r.headers)); res.end(Buffer.from(await r.arrayBuffer()));
}).listen(8787, () => console.log("worker dev server on :8787"));
