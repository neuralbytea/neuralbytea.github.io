"""Tiny headless-Chrome driver over the DevTools protocol (needs websocket-client).

    from cdp import Browser
    b = Browser(); b.login("http://localhost:8081", "admin", "pw")
    b.shot("http://localhost:8081/my", "/tmp/out.png", full=True)
"""
import base64, json, os, shutil, subprocess, tempfile, time, urllib.request
import websocket

CHROME = shutil.which("google-chrome") or "google-chrome"


class Browser:
    def __init__(self, port=9333, width=1440, height=900, scale=1):
        self.dir = tempfile.mkdtemp(prefix="cdp_")
        self.proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={self.dir}",
                                      "--remote-allow-origins=*", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                ws = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(.5)
        self.ws, self.n = websocket.create_connection(ws, max_size=None), 0
        self.send("Page.enable")
        self.send("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=scale, mobile=False)

    def send(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(m["error"])
                return m.get("result", {})

    def js(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        return r.get("result", {}).get("value")

    def go(self, url, wait=1.5):
        self.send("Page.navigate", url=url)
        for _ in range(80):
            if self.js("document.readyState") == "complete":
                break
            time.sleep(.25)
        time.sleep(wait)

    def login(self, base, user, pw):
        self.send("Network.clearBrowserCookies")
        self.go(f"{base}/web/login", .5)
        self.js(f"document.querySelector('input[name=login]').value={json.dumps(user)};document.querySelector('input[name=password]').value={json.dumps(pw)};document.querySelector('form.oe_login_form').submit()")
        time.sleep(3)

    def shot(self, url, path, full=False, wait=1.5, js=None, clip=None):
        if url:
            self.go(url, wait)
        if js:
            self.js(js)
            time.sleep(wait)
        kw = {"format": "png"}
        if clip:
            kw["clip"] = {**clip, "scale": 1}
        elif full:
            m = self.send("Page.getLayoutMetrics")["cssContentSize"]
            kw.update(captureBeyondViewport=True, clip={"x": 0, "y": 0, "width": m["width"], "height": m["height"], "scale": 1})
        open(path, "wb").write(base64.b64decode(self.send("Page.captureScreenshot", **kw)["data"]))
        return path

    def close(self):
        try:
            self.ws.close()
        finally:
            self.proc.terminate()
            shutil.rmtree(self.dir, ignore_errors=True)
