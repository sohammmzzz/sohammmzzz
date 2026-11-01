"""Builds the animated banner and button for the GitHub profile README.

The mood borrows from sohamdas.vercel.app (deep water, soft light, the
Bricolage Grotesque type) without copying the site itself.

Run:  python3 build/build.py path/to/BricolageGrotesque[opsz,wdth,wght].ttf
"""
import base64
import io
import random
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

# ---- palette (from the site's CSS tokens) ---------------------------------
CREAM = "#ece6d8"
MUTED = "#aab3b1"
FAINT = "#6f7d80"
MINT = "#93cfc1"
INK = "#0f1d1a"
W = 1200

# water colour by depth: surface teal -> seabed ink
STOPS = [(0, (37, 79, 92)), (40, (30, 62, 77)), (110, (24, 46, 60)), (180, (21, 33, 45)), (240, (16, 20, 28))]


def water(d):
    for (d0, c0), (d1, c1) in zip(STOPS, STOPS[1:]):
        if d0 <= d <= d1:
            t = (d - d0) / (d1 - d0)
            return "#%02x%02x%02x" % tuple(round(a + (b - a) * t) for a, b in zip(c0, c1))
    return "#%02x%02x%02x" % STOPS[-1][1]


# ---- fonts -----------------------------------------------------------------
CHARS = "".join(chr(c) for c in range(32, 127)) + "₹·–—→↗°’‘“”×…"


def font_face(src, family, axes):
    f = TTFont(src)
    f = instantiateVariableFont(f, axes)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    opts.notdef_outline = True
    s = Subsetter(opts)
    s.populate(text=CHARS)
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


FONT_CSS = ""


def build_fonts(src):
    global FONT_CSS
    FONT_CSS = "".join([
        font_face(src, "BD", {"opsz": 96, "wght": 300, "wdth": 88}),   # display
        font_face(src, "BT", {"opsz": 14, "wght": 400, "wdth": 100}),  # text
        font_face(src, "BM", {"opsz": 14, "wght": 500, "wdth": 100}),  # medium
    ])


STACK = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif"
BASE_CSS = f"""
.d{{font-family:BD,{STACK};fill:{CREAM};letter-spacing:-0.035em}}
.t{{font-family:BT,{STACK};fill:{MUTED}}}
.m{{font-family:BM,{STACK}}}
.cap{{font-family:BT,{STACK};fill:{FAINT};letter-spacing:.22em;font-size:13px}}
.mint{{fill:{MINT}}}
.cream{{fill:{CREAM}}}
.rise{{animation:rise 1.1s cubic-bezier(.2,.7,.2,1) backwards}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- shared pieces ---------------------------------------------------------
def water_bg(uid, h, d0, d1, rays=True):
    out = [f"""<defs>
<linearGradient id="w{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{water(d0)}"/><stop offset="1" stop-color="{water(d1)}"/></linearGradient>
<linearGradient id="ray{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bfe6ea" stop-opacity=".16"/><stop offset="1" stop-color="#bfe6ea" stop-opacity="0"/></linearGradient>
<clipPath id="c{uid}"><rect width="{W}" height="{h}" rx="28"/></clipPath>
</defs>
<g clip-path="url(#c{uid})">
<rect width="{W}" height="{h}" fill="url(#w{uid})"/>"""]
    if rays:
        rnd = random.Random(uid)
        strength = max(0.0, 1 - d0 / 140)
        for i in range(6):
            x = 120 + i * 190 + rnd.randint(-40, 40)
            wdt = rnd.randint(60, 130)
            dur = rnd.uniform(7, 12)
            out.append(
                f'<polygon points="{x},-10 {x + wdt},-10 {x + wdt - 160},{h} {x - 220},{h}" fill="url(#ray{uid})" opacity="{0.5 * strength:.2f}">'
                f'<animate attributeName="opacity" values="{0.2 * strength:.2f};{0.9 * strength:.2f};{0.2 * strength:.2f}" dur="{dur:.1f}s" begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/></polygon>')
    out.append(bubbles(uid, h))
    return "\n".join(out)


def bubbles(uid, h, n=16):
    rnd = random.Random(f"b{uid}")
    out = []
    for _ in range(n):
        x = rnd.randint(40, W - 40)
        r = rnd.choice([1.5, 2, 2.5, 3, 4, 5])
        dur = rnd.uniform(9, 22)
        drift = rnd.randint(-30, 30)
        out.append(
            f'<circle cx="{x}" cy="{h + 10}" r="{r}" fill="none" stroke="#cfeef0" stroke-opacity=".35" stroke-width="1">'
            f'<animate attributeName="cy" from="{h + 10}" to="-10" dur="{dur:.1f}s" begin="-{rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cx" values="{x};{x + drift};{x}" dur="{dur / 2:.1f}s" repeatCount="indefinite"/></circle>')
    return "\n".join(out)


def wave(y, uid, amp=6, opacity=.35):
    seg = 120
    d = f"M -{seg * 2} {y} " + " ".join(
        f"q {seg / 4} {-amp if i % 2 == 0 else amp} {seg / 2} 0" for i in range(int((W + seg * 4) / (seg / 2))))
    return (f'<g><path d="{d}" fill="none" stroke="#cfe9ea" stroke-opacity="{opacity}" stroke-width="1.2">'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{seg} 0" dur="6s" repeatCount="indefinite"/></path>'
            f'<path d="{d}" fill="none" stroke="#cfe9ea" stroke-opacity="{opacity * 0.6}" stroke-width="1" transform="translate(0 6)">'
            f'<animateTransform attributeName="transform" type="translate" from="{seg} 6" to="0 6" dur="9s" repeatCount="indefinite"/></path></g>')


def svg(h, body, title):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<style>{FONT_CSS}{BASE_CSS}</style>
{body}
</svg>"""


def write(name, content):
    (OUT / name).write_text(content)
    print(f"{name:22s} {len(content.encode()) / 1024:6.1f} KB")


def delay(i, base=0.15, step=0.12):
    return f'style="animation-delay:{base + i * step:.2f}s"'


# ---- panels ----------------------------------------------------------------
def ripples(cx, cy):
    """Soft rings spreading out, like a voice moving through water."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="5" fill="{MINT}" opacity=".9"><animate attributeName="opacity" values=".9;.5;.9" dur="3s" repeatCount="indefinite"/></circle>']
    for i in range(4):
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="6" ry="2" fill="none" stroke="{MINT}" stroke-width="1.2">'
                   f'<animate attributeName="rx" values="6;230" dur="8s" begin="-{i * 2}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="ry" values="2;70" dur="8s" begin="-{i * 2}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="stroke-opacity" values=".55;0" dur="8s" begin="-{i * 2}s" repeatCount="indefinite"/></ellipse>')
    return "".join(out)


def caustics(uid, h):
    """Faint moving light, as if sun is coming through the surface."""
    return f"""<defs><filter id="ca{uid}" x="0" y="0" width="100%" height="100%">
<feTurbulence type="fractalNoise" baseFrequency=".004 .012" numOctaves="2" seed="3">
<animate attributeName="baseFrequency" values=".004 .012;.005 .010;.004 .012" dur="18s" repeatCount="indefinite"/></feTurbulence>
<feColorMatrix values="0 0 0 0 .75  0 0 0 0 .92  0 0 0 0 .92  1.4 0 0 0 -.62"/></filter>
<linearGradient id="fade{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset=".7" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="m{uid}"><rect width="{W}" height="{h}" fill="url(#fade{uid})"/></mask></defs>
<rect width="{W}" height="{h}" filter="url(#ca{uid})" mask="url(#m{uid})" opacity=".35"/>"""


def hero():
    h = 360
    b = [water_bg("hero", h, 30, 200, rays=False)]
    b.append(caustics("hero", h))
    b.append(ripples(930, 205))
    x = 80
    b.append(f'<g class="rise" {delay(0)}><text x="{x}" y="112" class="cap" style="fill:#ece6d8;fill-opacity:.55">LEAD AI ENGINEER · NAGPUR, INDIA</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text x="{x - 4}" y="204" class="d" font-size="96">Soham Das</text></g>')
    b.append(f'<g class="rise" {delay(2)}><text x="{x}" y="252" class="t" font-size="22" fill="{CREAM}" fill-opacity=".8">I make machines that listen, see, and answer back.</text></g>')
    b.append(wave(h - 34, "hero", amp=4, opacity=.22))
    b.append("</g>")
    write("banner.svg", svg(h, "\n".join(b), "Soham Das, Lead AI Engineer. I make machines that listen, see, and answer back."))


def button(fname, label, filled, width=None):
    size, hh, pad = 16, 46, 26
    w = width or round(len(label) * size * 0.56 + pad * 2)
    if filled:
        body = (f'<rect x="1" y="1" width="{w - 2}" height="{hh - 2}" rx="{hh / 2 - 1}" fill="{MINT}"/>'
                f'<text x="{w / 2}" y="{hh / 2 + 6}" text-anchor="middle" class="m" font-size="{size}" fill="{INK}">{esc(label)}</text>')
    else:
        body = (f'<rect x="1" y="1" width="{w - 2}" height="{hh - 2}" rx="{hh / 2 - 1}" fill="{water(200)}" stroke="{MINT}" stroke-opacity=".45"/>'
                f'<text x="{w / 2}" y="{hh / 2 + 6}" text-anchor="middle" class="t" font-size="{size}" fill="{CREAM}">{esc(label)}</text>')
    (OUT / fname).write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{hh}" viewBox="0 0 {w} {hh}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title><style>{FONT_CSS.split('@font-face')[0]}@font-face{FONT_CSS.split('@font-face')[2 if not filled else 3]}{BASE_CSS}</style>{body}</svg>""")


def main():
    build_fonts(sys.argv[1])
    hero()
    button("btn-portfolio.svg", "Dive into the portfolio ↗", True)
    

if __name__ == "__main__":
    main()
