"""Trace the NB monogram (src/static/images/mark-512.png) into a clean, animated SVG.

    python3 trace_logo.py     # needs: pip install potracer numpy pillow
Writes src/static/images/nb-mark.svg (animated, transparent) and tools/art/nb-letters.svg (static, letters only, for icons).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import potrace

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src/static/images/mark-512.png"
UP = 2  # trace at 2x for smoother curves

im = Image.open(SRC).convert("RGB")
a = np.array(im).astype(float)
# brightness separates the letters (all bright blues/violets, max channel > 200) from the near-black background (max channel ~15)
v = a.max(axis=2)
alpha = np.clip((v - 15) / (200 - 15), 0, 1)
big = np.array(Image.fromarray((alpha * 255).astype(np.uint8)).resize((im.width * UP, im.height * UP), Image.BICUBIC)).astype(float) / 255
mask = big > 0.5  # True = letter
ys, xs = np.where(mask)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()

# potrace traces the DARK pixels of an 8-bit image: letters drawn black on white
plist = potrace.Bitmap(Image.fromarray(np.where(mask, 0, 255).astype(np.uint8))).trace(turdsize=20, alphamax=1.0, opticurve=True, opttolerance=0.4)


def path_d(curve):
    s = curve.start_point
    d = [f"M{s.x:.1f},{s.y:.1f}"]
    for seg in curve.segments:
        if seg.is_corner:
            d.append(f"L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}")
        else:
            d.append(f"C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}")
    return "".join(d) + "Z"


def bbox(curve):
    pts = [curve.start_point] + [p for seg in curve.segments for p in ((seg.c, seg.end_point) if seg.is_corner else (seg.c1, seg.c2, seg.end_point))]
    return min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts)


letters, particles = [], []
N_LEFT = 118 * UP  # everything entirely left of the N's left edge is a loose pixel
for c in plist:
    bx0, bx1, by0, by1 = bbox(c)
    (particles if bx1 < N_LEFT else letters).append((path_d(c), (bx0 + bx1) / 2, (by0 + by1) / 2))
L = "".join(d for d, _, _ in letters)
print(f"letters: {len(letters)} curves, particles: {len(particles)}")

PAD = 46
vx, vy, vw, vh = x0 - PAD, y0 - PAD, (x1 - x0) + 2 * PAD, (y1 - y0) + 2 * PAD
GRAD = ('<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{a}" y1="{b}" x2="{c}" y2="{d}">'
        '<stop offset="0" stop-color="#14c0ff"/><stop offset=".42" stop-color="#2f6bff"/><stop offset=".74" stop-color="#4a45ee"/><stop offset="1" stop-color="#9a5cff"/></linearGradient>'
        ).format(a=x0 + 40, b=y0, c=x1 - 40, d=y1)

px = "".join(f'<path class="px" style="animation-delay:{(i * 0.37) % 2.4:.2f}s" fill="url(#g)" d="{d}"/>' for i, (d, _, _) in enumerate(particles))
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {vw} {vh}" role="img" aria-label="NeuralBytea">
<defs>{GRAD}
<linearGradient id="sheen" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".62"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-20%" y="-30%" width="140%" height="160%"><feGaussianBlur stdDeviation="16"/></filter>
<clipPath id="cl"><path d="{L}"/></clipPath></defs>
<style>.px{{animation:tw 2.6s ease-in-out infinite}}@keyframes tw{{0%,100%{{opacity:.28}}50%{{opacity:1}}}}@media (prefers-reduced-motion:reduce){{.px{{animation:none}}#sw{{display:none}}}}</style>
<path d="{L}" fill="url(#g)" opacity=".5" filter="url(#glow)"/>
<path d="{L}" fill="url(#g)"/>
<g clip-path="url(#cl)"><rect id="sw" y="{vy}" width="{int(vw*.22)}" height="{vh}" fill="url(#sheen)" transform="skewX(-18)">
<animate attributeName="x" values="{vx-int(vw*.4)};{vx-int(vw*.4)};{vx+vw};{vx+vw}" keyTimes="0;.5;.78;1" dur="7s" repeatCount="indefinite"/></rect></g>
{px}
</svg>'''
out = ROOT / "src/static/images/nb-mark.svg"
out.write_text(svg)
print("wrote", out, f"({out.stat().st_size/1024:.1f} KB), viewBox {vx} {vy} {vw} {vh}  aspect {vw/vh:.2f}")

# static letters-only SVG for square icons (favicon, app icon)
lx0 = min(bbox(c)[0] for c in plist if bbox(c)[1] >= N_LEFT)
ls = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{lx0-10} {vy+PAD-10} {x1-lx0+20} {y1-y0+20}"><defs>{GRAD}</defs><path d="{L}" fill="url(#g)"/></svg>'''
(ROOT / "tools/art").mkdir(exist_ok=True)
(ROOT / "tools/art/nb-letters.svg").write_text(ls)
print("letters-only svg:", lx0, "->", x1, "aspect", (x1 - lx0 + 20) / (y1 - y0 + 20))
