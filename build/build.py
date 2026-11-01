"""Builds the animated SVG panels for the GitHub profile README.

The look is lifted from sohamdas.vercel.app: a dive from the surface to the
seabed. Each panel sits a little deeper, so the water darkens as you scroll,
and the depth meter on the left edge keeps count.

Run:  python3 build/build.py path/to/BricolageGrotesque[opsz,wdth,wght].ttf
"""
import base64
import io
import math
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
LAV = "#c7c1f0"
CARD = "#141922"
CARD_LINE = "#2a3442"
W = 1200
MAX_DEPTH = 240

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


def depth_meter(h, depth, top=None, bottom=None):
    """Ruler on the left edge, with the marker at this panel's depth."""
    top = 70 if top is None else top
    bottom = h - 70 if bottom is None else bottom
    y = top + (bottom - top) * depth / MAX_DEPTH
    ticks = []
    for i in range(0, 25):
        ty = top + (bottom - top) * i / 24
        ln = 12 if i % 4 == 0 else 6
        ticks.append(f'<line x1="34" y1="{ty:.1f}" x2="{34 + ln}" y2="{ty:.1f}" stroke="{CREAM}" stroke-opacity=".28"/>')
    return f"""<g>
<line x1="34" y1="{top}" x2="34" y2="{bottom}" stroke="{CREAM}" stroke-opacity=".18"/>
{''.join(ticks)}
<circle cx="34" cy="{y:.1f}" r="9" fill="{MINT}" opacity=".25"><animate attributeName="r" values="6;12;6" dur="3s" repeatCount="indefinite"/><animate attributeName="opacity" values=".35;0;.35" dur="3s" repeatCount="indefinite"/></circle>
<circle cx="34" cy="{y:.1f}" r="5" fill="{MINT}"/>
<text x="48" y="{y + 4:.1f}" class="t" font-size="12" fill="{CREAM}">{depth} m</text>
</g>"""


def pill(x, y, label, filled=False, size=15, pad=16, h=34):
    w = round(len(label) * size * 0.56 + pad * 2)
    if filled:
        return w, (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{MINT}"/>'
                   f'<text x="{x + w / 2}" y="{y + h / 2 + size * 0.36:.1f}" text-anchor="middle" class="m" font-size="{size}" fill="{INK}">{esc(label)}</text>')
    return w, (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="#ffffff" fill-opacity=".04" stroke="{CREAM}" stroke-opacity=".16"/>'
               f'<text x="{x + w / 2}" y="{y + h / 2 + size * 0.36:.1f}" text-anchor="middle" class="t" font-size="{size}" fill="{CREAM}" fill-opacity=".85">{esc(label)}</text>')


def pills(x, y, labels, maxw, size=14, gap=8, h=30):
    out, cx, cy = [], x, y
    for lab in labels:
        w = round(len(lab) * size * 0.56 + 32)
        if cx + w > x + maxw:
            cx, cy = x, cy + h + gap
        out.append(pill(cx, cy, lab, size=size, h=h)[1])
        cx += w + gap
    return "".join(out), cy + h


def orb(uid, cx, cy, r, glow=True):
    """Leo: an iridescent pearl that wobbles and shifts hue."""
    return f"""<defs>
<radialGradient id="pb{uid}" cx=".45" cy=".22" r=".95">
  <stop offset="0" stop-color="#e7e4ff"><animate attributeName="stop-color" values="#e7e4ff;#dff6ef;#e7e4ff" dur="9s" repeatCount="indefinite"/></stop>
  <stop offset=".45" stop-color="{LAV}"><animate attributeName="stop-color" values="{LAV};#a9dccf;#b8c8f2;{LAV}" dur="9s" repeatCount="indefinite"/></stop>
  <stop offset=".8" stop-color="#8fd0bd"><animate attributeName="stop-color" values="#86c9b5;#b7aee9;#86c9b5" dur="9s" repeatCount="indefinite"/></stop>
</radialGradient>
<radialGradient id="pg{uid}"><stop offset="0" stop-color="#9fe0d2" stop-opacity=".45"/><stop offset="1" stop-color="#9fe0d2" stop-opacity="0"/></radialGradient>
<radialGradient id="ps{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<filter id="pw{uid}" x="-20%" y="-20%" width="140%" height="140%">
  <feTurbulence type="fractalNoise" baseFrequency=".007" numOctaves="1" seed="4" result="n">
    <animate attributeName="baseFrequency" values=".006;.009;.006" dur="11s" repeatCount="indefinite"/>
  </feTurbulence>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="{r * 0.09:.0f}" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="pt{uid}"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="3" seed="9"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .1 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
</defs>
{f'<circle cx="{cx}" cy="{cy}" r="{r * 1.7:.0f}" fill="url(#pg{uid})"><animate attributeName="r" values="{r * 1.55:.0f};{r * 1.85:.0f};{r * 1.55:.0f}" dur="5s" repeatCount="indefinite"/></circle>' if glow else ''}
<g>
<animateTransform attributeName="transform" type="translate" values="0 0;0 -{r * 0.06:.0f};0 0" dur="6s" repeatCount="indefinite"/>
<g filter="url(#pw{uid})">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#pb{uid})"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" filter="url(#pt{uid})"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="2"/>
</g>
<ellipse cx="{cx - r * 0.3:.0f}" cy="{cy - r * 0.45:.0f}" rx="{r * 0.16:.0f}" ry="{r * 0.07:.0f}" fill="url(#ps{uid})" transform="rotate(-25 {cx - r * 0.3:.0f} {cy - r * 0.45:.0f})"/>
<circle cx="{cx - r * 0.42:.0f}" cy="{cy - r * 0.32:.0f}" r="{max(2, r * 0.03):.1f}" fill="#fff" opacity=".9"/>
</g>"""


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
def hero():
    h = 620
    b = [water_bg("hero", h, 0, 10)]
    b.append(depth_meter(h, 0))
    b.append(orb("hero", 900, 300, 190))
    b.append(f'<text x="900" y="550" text-anchor="middle" class="t" font-size="15" fill="{CREAM}" fill-opacity=".6">Touch the water. Leo is waiting at sohamdas.vercel.app</text>')
    x = 110
    b.append(f'<g class="rise" {delay(0)}><text x="{x}" y="186" class="t" font-size="22" fill="{CREAM}" fill-opacity=".75">Hi, I’m</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text x="{x - 4}" y="300" class="d" font-size="124">Soham Das.</text></g>')
    b.append(f'<g class="rise" {delay(2)}><text x="{x}" y="368" class="d mint" font-size="44" style="letter-spacing:-0.02em">I build AI you can talk to.</text></g>')
    b.append(f'<g class="rise" {delay(3)}><text class="t" font-size="19"><tspan x="{x}" y="418">Lead AI Engineer at Solar Industries India Ltd. Agents on</tspan>'
             f'<tspan x="{x}" y="446">factory floors, vision on production lines, and voice</tspan><tspan x="{x}" y="474">that moves the screen.</tspan></text></g>')
    w1, p1 = pill(x, 506, "Talk to Leo", filled=True, size=17, h=46, pad=22)
    _, p2 = pill(x + w1 + 14, 506, "Dive in ↓", size=17, h=46, pad=22)
    b.append(f'<g class="rise" {delay(4)}>{p1}{p2}</g>')
    b.append(wave(h - 30, "hero"))
    b.append("</g>")
    write("hero.svg", svg(h, "\n".join(b), "Soham Das. I build AI you can talk to."))


def section_head(label, depth, title, sub=None):
    """A thin depth marker between sections, e.g. 'Story · 12 m'."""
    h = 150 if sub else 120
    uid = f"s{depth}"
    b = [water_bg(uid, h, depth, depth + 6, rays=depth < 60)]
    b.append(f'<g class="rise" {delay(0)}><circle cx="62" cy="49" r="5" fill="{MINT}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<text x="78" y="54" class="cap">{esc(label.upper())} · {depth} M</text>'
             f'<line x1="{78 + len(label + str(depth)) * 11 + 70}" y1="49" x2="{W - 56}" y2="49" stroke="{CREAM}" stroke-opacity=".12" stroke-dasharray="2 6"/></g>')
    b.append(f'<g class="rise" {delay(1)}><text x="56" y="{102}" class="d" font-size="46">{esc(title)}</text></g>')
    if sub:
        b.append(f'<g class="rise" {delay(2)}><text x="58" y="134" class="t" font-size="17">{esc(sub)}</text></g>')
    b.append("</g>")
    return h, b


def story():
    h0, b = section_head("Story", 12, "The dive, so far.")
    h = 470
    b = [water_bg("story", h, 12, 34)]
    b.append(f'<g class="rise" {delay(0)}><circle cx="62" cy="49" r="5" fill="{MINT}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<text x="78" y="54" class="cap">THE DIVE · STORY · 12 M</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text x="56" y="112" class="d" font-size="52">The dive, four stops in.</text></g>')
    stops = [
        ("2018 – 2022", "Studied IT in the", "hills of Sikkim.", ["B.Tech, Sikkim Manipal", "Institute of Technology.", "8.17 CGPA."]),
        ("Oct 2023", "Took AI onto the", "factory floor.", ["Lead AI Engineer at Solar", "Industries, Nagpur. Most of it", "runs offline, beside machines."]),
        ("2026", "Certified, and", "twice awarded.", ["AWS Generative AI Developer –", "Professional. Two Excellence", "Awards for shipping fast."]),
        ("Now", "Building AI you", "can talk to.", ["Like Leo, the water you’ve", "been scrolling with on", "my portfolio."]),
    ]
    y0 = 196
    colw = (W - 112) / 4
    b.append(f'<line x1="56" y1="{y0}" x2="{W - 56}" y2="{y0}" stroke="{CREAM}" stroke-opacity=".16"/>')
    b.append(f'<line x1="56" y1="{y0}" x2="{W - 56}" y2="{y0}" stroke="{MINT}" stroke-width="2" stroke-dasharray="{W}" stroke-dashoffset="{W}">'
             f'<animate attributeName="stroke-dashoffset" from="{W}" to="0" dur="2.6s" begin=".4s" fill="freeze" calcMode="spline" keySplines=".3 .1 .2 1"/></line>')
    for i, (when, t1, t2, body) in enumerate(stops):
        x = 56 + i * colw
        last = i == 3
        b.append(f'<g class="rise" {delay(i, 0.6, 0.45)}>')
        b.append(f'<circle cx="{x + 7}" cy="{y0}" r="7" fill="{MINT if last else water(20)}" stroke="{MINT}" stroke-width="2"/>')
        if last:
            b.append(f'<circle cx="{x + 7}" cy="{y0}" r="7" fill="none" stroke="{MINT}"><animate attributeName="r" values="7;18" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>')
        b.append(f'<text x="{x}" y="{y0 - 24}" class="m" font-size="15" fill="{MINT if last else CREAM}" fill-opacity="{1 if last else .7}">{esc(when)}</text>')
        b.append(f'<text class="d" font-size="30" style="letter-spacing:-0.025em"><tspan x="{x}" y="{y0 + 58}">{esc(t1)}</tspan><tspan x="{x}" y="{y0 + 92}">{esc(t2)}</tspan></text>')
        b.append(f'<text class="t" font-size="15">' + "".join(
            f'<tspan x="{x}" y="{y0 + 136 + j * 23}">{esc(s)}</tspan>' for j, s in enumerate(body)) + "</text>")
        b.append("</g>")
    b.append(depth_meter(h, 12, 60, h - 40) if False else "")
    b.append("</g>")
    write("story.svg", svg(h, "\n".join(b), "Story: B.Tech at SMIT, Lead AI Engineer at Solar Industries, AWS certified, building AI you can talk to."))


def work():
    h = 360
    b = [water_bg("work", h, 40, 60)]
    b.append(f'<g class="rise" {delay(0)}><circle cx="62" cy="49" r="5" fill="{MINT}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<text x="78" y="54" class="cap">AT SOLAR INDUSTRIES INDIA LTD · 40 M</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text x="56" y="118" class="d" font-size="60">Four systems, all in production.</text></g>')
    b.append(f'<g class="rise" {delay(2)}><text x="58" y="152" class="t" font-size="18" fill="{CREAM}" fill-opacity=".7">Lead AI Engineer · Oct 2023 – present · Most of it runs offline, beside the machines it watches.</text></g>')
    stats = [("4", "systems in production"), ("10+ h", "of reconciliation saved weekly"), ("₹5 L+", "saved by one fast delivery"), ("h → s", "ad-hoc reporting time")]
    tw = (W - 112 - 3 * 16) / 4
    for i, (big, small) in enumerate(stats):
        x = 56 + i * (tw + 16)
        b.append(f'<g class="rise" {delay(i, .5, .15)}><rect x="{x}" y="196" width="{tw:.0f}" height="124" rx="18" fill="#000" fill-opacity=".16" stroke="{CREAM}" stroke-opacity=".08"/>'
                 f'<text x="{x + 24}" y="262" class="d mint" font-size="50">{esc(big)}</text>'
                 f'<text x="{x + 24}" y="295" class="t" font-size="15">{esc(small)}</text></g>')
    b.append("</g>")
    write("work.svg", svg(h, "\n".join(b), "At Solar Industries: four AI systems in production."))


# ---- isometric line art for the Fig. cards ---------------------------------
ISO_C, ISO_S = math.cos(math.radians(30)), math.sin(math.radians(30))


def iso(x, y, z, ox, oy, k=1.0):
    return ox + (x - y) * ISO_C * k, oy + (x + y) * ISO_S * k - z * k


def iso_box(x, y, z, w, d, hgt, ox, oy, k=1.0, fill_top="#1f2531", fill_l="#171b24", fill_r="#1a1f29", stroke="#46505f", extra=""):
    P = lambda a, b_, c: "%.1f,%.1f" % iso(a, b_, c, ox, oy, k)
    top = f'{P(x, y, z + hgt)} {P(x + w, y, z + hgt)} {P(x + w, y + d, z + hgt)} {P(x, y + d, z + hgt)}'
    left = f'{P(x, y + d, z)} {P(x + w, y + d, z)} {P(x + w, y + d, z + hgt)} {P(x, y + d, z + hgt)}'
    right = f'{P(x + w, y, z)} {P(x + w, y + d, z)} {P(x + w, y + d, z + hgt)} {P(x + w, y, z + hgt)}'
    sw = 'stroke-width=".8" stroke-linejoin="round"'
    return (f'<g {extra}><polygon points="{left}" fill="{fill_l}" stroke="{stroke}" {sw}/>'
            f'<polygon points="{right}" fill="{fill_r}" stroke="{stroke}" {sw}/>'
            f'<polygon points="{top}" fill="{fill_top}" stroke="{stroke}" {sw}/></g>')


def fig_art(kind, ox, oy):
    k = 1.0
    out = [iso_box(-10, -10, 0, 300, 200, 10, ox, oy, k, fill_top="#1a1f29")]
    if kind == "rca":
        # motor (cylinder-ish stack), cabinet with drawers, graph nodes
        for i in range(5):
            out.append(iso_box(20, 20, 10 + i * 14, 60, 60, 14, ox, oy, k, fill_top="#222a36"))
        cx, cy = iso(50, 50, 90, ox, oy, k)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="22" fill="#e3a299" opacity="0"><animate attributeName="opacity" values="0;0;.55;0" dur="4s" repeatCount="indefinite"/><animate attributeName="r" values="14;14;30;14" dur="4s" repeatCount="indefinite"/></circle>')
        out.append(iso_box(190, 20, 10, 70, 60, 70, ox, oy, k))
        for i in range(3):
            a = iso(260, 30, 25 + i * 18, ox, oy, k)
            b_ = iso(260, 70, 25 + i * 18, ox, oy, k)
            out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b_[0]:.1f}" y2="{b_[1]:.1f}" stroke="#5a6576" stroke-width="1"/>')
        nodes = [(150, 120), (190, 110), (220, 140), (170, 160), (240, 170), (130, 160)]
        pts = [iso(x, y, 10, ox, oy, k) for x, y in nodes]
        for i, j in [(0, 1), (1, 2), (0, 3), (3, 4), (2, 4), (0, 5), (5, 3)]:
            out.append(f'<line x1="{pts[i][0]:.1f}" y1="{pts[i][1]:.1f}" x2="{pts[j][0]:.1f}" y2="{pts[j][1]:.1f}" stroke="{MINT}" stroke-opacity=".5" stroke-dasharray="3 3"><animate attributeName="stroke-dashoffset" from="12" to="0" dur="1.2s" repeatCount="indefinite"/></line>')
        for i, (px, py) in enumerate(pts):
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{CARD}" stroke="{MINT}"><animate attributeName="fill" values="{CARD};{MINT};{CARD}" dur="3s" begin="{i * .4:.1f}s" repeatCount="indefinite"/></circle>')
        caption = ("Point at the motor to overheat it", "76 °C · 4.3 bar · watching")
    elif kind == "qc":
        out.append(iso_box(0, 70, 10, 280, 50, 14, ox, oy, k, fill_top="#202733"))
        # gantry
        out.append(iso_box(120, 60, 24, 8, 8, 90, ox, oy, k))
        out.append(iso_box(120, 60, 114, 8, 70, 8, ox, oy, k))
        out.append(iso_box(114, 84, 96, 20, 20, 14, ox, oy, k, fill_top="#283140"))
        lx, ly = iso(124, 94, 96, ox, oy, k)
        out.append(f'<polygon points="{lx:.1f},{ly:.1f} {lx - 28:.1f},{ly + 60:.1f} {lx + 28:.1f},{ly + 60:.1f}" fill="{MINT}" opacity=".12"><animate attributeName="opacity" values=".05;.22;.05" dur="2s" repeatCount="indefinite"/></polygon>')
        for i in range(4):
            box = iso_box(0, 80, 24, 34, 30, 22, ox, oy, k, fill_top="#2a3342")
            dx, dy = ISO_C * 280 * k, ISO_S * 280 * k
            out.append(f'<g>{box}<animateTransform attributeName="transform" type="translate" from="0 0" to="{dx:.1f} {dy:.1f}" dur="8s" begin="-{i * 2}s" repeatCount="indefinite"/>'
                       f'<animate attributeName="opacity" values="0;1;1;1;0" keyTimes="0;.08;.5;.92;1" dur="8s" begin="-{i * 2}s" repeatCount="indefinite"/></g>')
        caption = ("Point at the belt to slow it", "box 0137 · label ok · counted")
    elif kind == "chat":
        bars = [40, 70, 55, 95, 80, 120]
        for i, bh in enumerate(bars):
            out.append(f'<g>{iso_box(150 + i * 22, 40, 10, 14, 14, bh, ox, oy, k, fill_top=MINT if i == 5 else "#2a3342", fill_l="#1d3a37" if i == 5 else "#171b24", fill_r="#24504a" if i == 5 else "#1a1f29")}'
                       f'<animate attributeName="opacity" values="0;1" dur=".5s" begin="{.3 + i * .25:.2f}s" fill="freeze"/></g>')
        for j, (y, wd) in enumerate([(30, 90), (95, 120), (150, 80)]):
            out.append(iso_box(10, y, 10, wd, 34, 8, ox, oy, k, fill_top="#283140" if j != 1 else "#22403c"))
        caption = ("Point at a question card", "“sales by region, Q3?” → chart")
    else:  # etl trays
        cols = [("#9b6b4a", "bronze"), ("#9aa3ad", "silver"), ("#c9a659", "gold")]
        for i, (c, _) in enumerate(cols):
            out.append(f'<g>{iso_box(60, 40, 10 + i * 46, 170, 120, 30, ox, oy, k, fill_top="#1f2531")}'
                       f'<animateTransform attributeName="transform" type="translate" values="0 0;{-14 if i == 1 else 0} {-7 if i == 1 else 0};0 0" dur="5s" repeatCount="indefinite"/></g>')
            a = iso(60, 160, 25 + i * 46, ox, oy, k)
            out.append(f'<circle cx="{a[0] + 30:.1f}" cy="{a[1] - 6:.1f}" r="5" fill="{c}"/>')
        drop = iso(145, 100, 190, ox, oy, k)
        out.append(f'<circle cx="{drop[0]:.1f}" cy="{drop[1]:.1f}" r="4" fill="{MINT}"><animate attributeName="cy" values="{drop[1] - 30:.1f};{drop[1] + 40:.1f}" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;0" dur="1.6s" repeatCount="indefinite"/></circle>')
        caption = ("Point at a tray to pull it out", "λ refresh · 06:00 · all green")
    return "\n".join(out), caption


def fig_card(n, kind, eyebrow, title, line, quote, tags, how, depth, fname, link=None):
    h = 440
    uid = f"f{n}"
    b = [water_bg(uid, h, depth, depth + 14, rays=False)]
    # art card
    cx0, cy0, cw, ch = 40, 40, 470, h - 80
    b.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="22" fill="{CARD}" stroke="{CARD_LINE}"/>')
    b.append(f'<text x="{cx0 + 22}" y="{cy0 + 34}" class="t" font-size="13" fill="{FAINT}">Fig. {n}</text>')
    b.append(f'<text x="{cx0 + cw - 22}" y="{cy0 + 34}" text-anchor="end" class="t" font-size="13" fill="{CREAM}" fill-opacity=".75">{esc(eyebrow)}</text>')
    art, (cap_l, cap_r) = fig_art(kind, cx0 + cw / 2 - 20, cy0 + 120)
    b.append(art)
    b.append(f'<text x="{cx0 + 22}" y="{cy0 + ch - 22}" class="t" font-size="13" fill="{FAINT}">{esc(cap_l)}</text>')
    b.append(f'<text x="{cx0 + cw - 22}" y="{cy0 + ch - 22}" text-anchor="end" class="t" font-size="13" fill="{CREAM}" fill-opacity=".7">{esc(cap_r)}</text>')
    # text column
    x = 560
    b.append(f'<g class="rise" {delay(0)}><text x="{x}" y="112" class="d" font-size="38" style="letter-spacing:-0.025em">{esc(title)}</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text class="t" font-size="18" fill="{CREAM}" fill-opacity=".85">' + "".join(
        f'<tspan x="{x}" y="{152 + i * 27}">{esc(s)}</tspan>' for i, s in enumerate(line)) + "</text></g>")
    qy = 152 + len(line) * 27 + 22
    b.append(f'<g class="rise" {delay(2)}><rect x="{x}" y="{qy - 4}" width="3" height="{len(quote) * 25 + 6}" rx="1.5" fill="{MINT}"/>'
             f'<text class="t" font-size="16" fill="{CREAM}" fill-opacity=".8">' + "".join(
                 f'<tspan x="{x + 18}" y="{qy + 14 + i * 25}">{esc(s)}</tspan>' for i, s in enumerate(quote)) + "</text></g>")
    ty = qy + len(quote) * 25 + 30
    tp, ty_end = pills(x, ty, tags, W - x - 50)
    b.append(f'<g class="rise" {delay(3)}>{tp}</g>')
    hy = ty_end + 34
    b.append(f'<g class="rise" {delay(4)}><circle cx="{x + 8}" cy="{hy - 5}" r="8" fill="none" stroke="{CREAM}" stroke-opacity=".3"/>'
             f'<text x="{x + 8}" y="{hy - 1}" text-anchor="middle" class="t" font-size="13" fill="{CREAM}">+</text>'
             f'<text x="{x + 26}" y="{hy}" class="t" font-size="15" fill="{CREAM}" fill-opacity=".75">{esc(how)}</text></g>')
    b.append("</g>")
    write(fname, svg(h, "\n".join(b), title))


def side_card(fname, n, title, line, tags, foot, depth, accent_kind):
    w, h = 586, 330
    uid = f"p{n}"
    b = [f"""<defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{water(depth)}"/><stop offset="1" stop-color="{water(depth + 20)}"/></linearGradient>
<clipPath id="c{uid}"><rect width="{w}" height="{h}" rx="24"/></clipPath></defs>
<g clip-path="url(#c{uid})"><rect width="{w}" height="{h}" fill="url(#g{uid})"/>"""]
    b.append(f'<text x="32" y="48" class="t" font-size="13" fill="{FAINT}">Fig. {n}</text>')
    # little animated glyph top-right
    gx, gy = w - 70, 52
    if accent_kind == "mic":
        for i in range(7):
            hh = [10, 22, 34, 18, 28, 14, 8][i]
            b.append(f'<rect x="{gx - 30 + i * 9}" y="{gy - hh / 2}" width="4" height="{hh}" rx="2" fill="{MINT}"><animate attributeName="height" values="{hh};{max(4, 40 - hh)};{hh}" dur="{.9 + i * .13:.2f}s" repeatCount="indefinite"/><animate attributeName="y" values="{gy - hh / 2};{gy - max(4, 40 - hh) / 2};{gy - hh / 2}" dur="{.9 + i * .13:.2f}s" repeatCount="indefinite"/></rect>')
    elif accent_kind == "leaf":
        for i in range(4):
            b.append(f'<rect x="{gx - 26 + i * 6}" y="{gy - 14 + i * 3}" width="56" height="10" rx="2" fill="none" stroke="{MINT}" stroke-opacity="{.3 + i * .18:.2f}" transform="rotate(-8 {gx} {gy})"><animateTransform attributeName="transform" type="rotate" values="-8 {gx} {gy};-2 {gx} {gy};-8 {gx} {gy}" dur="{4 + i}s" repeatCount="indefinite"/></rect>')
    elif accent_kind == "cards":
        for i in range(3):
            b.append(f'<rect x="{gx - 30}" y="{gy - 22 + i * 15}" width="60" height="11" rx="4" fill="{MINT}" fill-opacity="0"><animate attributeName="fill-opacity" values="0;.6;.6;0" keyTimes="0;.15;.85;1" dur="4s" begin="{i * .5}s" repeatCount="indefinite"/></rect>'
                     f'<rect x="{gx - 30}" y="{gy - 22 + i * 15}" width="60" height="11" rx="4" fill="none" stroke="{MINT}" stroke-opacity=".5"/>')
    else:  # drawer
        b.append(f'<rect x="{gx - 30}" y="{gy - 20}" width="60" height="40" rx="5" fill="none" stroke="{CREAM}" stroke-opacity=".3"/>'
                 f'<rect x="{gx - 26}" y="{gy - 4}" width="52" height="16" rx="3" fill="{CARD}" stroke="{MINT}" stroke-opacity=".6"><animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 14;0 14;0 0" keyTimes="0;.3;.45;.8;1" dur="5s" repeatCount="indefinite"/></rect>')
    b.append(f'<text x="32" y="120" class="d" font-size="40" style="letter-spacing:-0.03em">{esc(title)}</text>')
    b.append(f'<text class="t" font-size="16" fill="{CREAM}" fill-opacity=".8">' + "".join(
        f'<tspan x="32" y="{158 + i * 24}">{esc(s)}</tspan>' for i, s in enumerate(line)) + "</text>")
    tp, _ = pills(32, 158 + len(line) * 24 + 18, tags, w - 64, size=13, h=28)
    b.append(tp)
    b.append(f'<text x="32" y="{h - 30}" class="m" font-size="14" fill="{MINT}">{esc(foot)}</text>')
    b.append("</g>")
    body = "\n".join(b)
    (OUT / fname).write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title><style>{FONT_CSS}{BASE_CSS}</style>
{body}
</svg>""")
    print(f"{fname:22s} {(OUT / fname).stat().st_size / 1024:6.1f} KB")


def toolkit():
    h = 640
    b = [water_bg("tool", h, 180, 205, rays=False)]
    b.append(f'<g class="rise" {delay(0)}><circle cx="62" cy="49" r="5" fill="{MINT}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<text x="78" y="54" class="cap">WHAT I CARRY · TOOLKIT · 180 M</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text x="56" y="116" class="d" font-size="56">Tools, and the paperwork.</text></g>')
    groups = [
        ("AI and ML", ["Agentic workflows", "RAG", "LLM fine-tuning (PEFT)", "NLP", "Computer vision (YOLO)", "Time series forecasting", "Prompt engineering", "Responsible AI"]),
        ("Frameworks", ["PyTorch", "LangGraph", "LlamaIndex", "CrewAI"]),
        ("Languages", ["Python", "TypeScript", "Java", "Rust", "SQL"]),
        ("Cloud and data", ["AWS Bedrock", "SageMaker", "Lambda", "S3", "OpenSearch", "PostgreSQL", "MySQL", "Neo4j", "NebulaGraph"]),
        ("Product", ["Next.js", "Django", "FastAPI", "Flask", "Power BI"]),
    ]
    y = 160
    for i, (g, items) in enumerate(groups):
        b.append(f'<g class="rise" {delay(i, .4, .12)}><text x="56" y="{y + 20}" class="m" font-size="15" fill="{MINT}">{esc(g)}</text>')
        tp, yend = pills(220, y, items, 620, size=14, h=30)
        b.append(tp + "</g>")
        y = yend + 18
    # paperwork column
    px = 880
    b.append(f'<line x1="{px - 16}" y1="160" x2="{px - 16}" y2="{h - 50}" stroke="{CREAM}" stroke-opacity=".1"/>')
    papers = [
        ("Amazon Web Services, 2026", ["AWS Certified Generative AI", "Developer – Professional"]),
        ("Excellence Award, twice", ["Shipped a mission-critical app", "in a fast build-and-deploy", "cycle that saved ₹5 lakh+."]),
        ("Team Excellence Award", ["End-to-end delivery of the", "Manpower Management app."]),
        ("B.Tech, Information Technology", ["Sikkim Manipal Institute of", "Technology · 2018 – 2022 · 8.17"]),
    ]
    yy = 178
    for i, (head, lines) in enumerate(papers):
        b.append(f'<g class="rise" {delay(i, .7, .15)}><text x="{px + 4}" y="{yy}" class="m" font-size="15" fill="{CREAM}">{esc(head)}</text>'
                 f'<text class="t" font-size="14">' + "".join(f'<tspan x="{px + 4}" y="{yy + 24 + j * 20}">{esc(s)}</tspan>' for j, s in enumerate(lines)) + "</text></g>")
        yy += 40 + len(lines) * 20 + 14
    b.append("</g>")
    write("toolkit.svg", svg(h, "\n".join(b), "Toolkit: AI/ML, frameworks, languages, cloud and data, product. AWS certified, twice awarded."))


def seabed():
    h = 470
    b = [water_bg("sea", h, 214, 240, rays=False)]
    rnd = random.Random(7)
    # sand dunes
    b.append(f'<path d="M0 {h - 90} C 180 {h - 130}, 360 {h - 70}, 600 {h - 100} S 1000 {h - 140}, {W} {h - 95} L {W} {h} L 0 {h} Z" fill="#1b2029"/>')
    b.append(f'<path d="M0 {h - 55} C 220 {h - 80}, 420 {h - 40}, 700 {h - 62} S 1050 {h - 85}, {W} {h - 58} L {W} {h} L 0 {h} Z" fill="#20262f"/>')
    # seaweed
    for i, sx in enumerate([90, 128, 1040, 1080, 1120, 640]):
        hh = rnd.randint(70, 140)
        base = h - 60 - (20 if sx in (640,) else 0)
        b.append(f'<path d="M{sx} {base} q -14 {-hh / 3:.0f} 0 {-hh / 1.6:.0f} t 0 {-hh / 2.6:.0f}" fill="none" stroke="#3b6b62" stroke-width="5" stroke-linecap="round" opacity=".7">'
                 f'<animateTransform attributeName="transform" type="rotate" values="0 {sx} {base};{rnd.choice([-7, 7])} {sx} {base};0 {sx} {base}" dur="{rnd.uniform(4, 7):.1f}s" repeatCount="indefinite"/></path>')
    # tiny pearl resting on the sand
    b.append(orb("sea", 880, h - 150, 46))
    b.append(f'<g class="rise" {delay(0)}><circle cx="62" cy="59" r="5" fill="{MINT}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             f'<text x="78" y="64" class="cap">SEABED · 240 M · SAY HELLO</text></g>')
    b.append(f'<g class="rise" {delay(1)}><text class="d" font-size="60"><tspan x="56" y="140">Building something</tspan><tspan x="56" y="208">that listens?</tspan></text></g>')
    b.append(f'<g class="rise" {delay(2)}><text x="58" y="254" class="t" font-size="19" fill="{CREAM}" fill-opacity=".8">Tell me about it — it lands in my inbox.</text></g>')
    b.append(f'<g class="rise" {delay(3)}><text x="58" y="284" class="t" font-size="16">Or tap the orb on my portfolio and tell Leo, out loud.</text></g>')
    b.append(f'<text x="{W / 2}" y="{h - 22}" text-anchor="middle" class="t" font-size="12" fill="{FAINT}">© Soham Das · Leo runs on Gemini Live, straight from your browser.</text>')
    b.append("</g>")
    write("seabed.svg", svg(h, "\n".join(b), "Seabed, 240 m. Building something that listens? Say hello."))


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
    story()
    work()
    fig_card(1, "rca", "Fault trace", "Real-time root cause analysis",
             ["An offline agent that diagnoses machine", "faults the moment a sensor complains."],
             ["Diagnosis starts when the alarm does,", "not when someone finds the manual."],
             ["LangGraph", "Neo4j", "Ollama", "Django", "Next.js"],
             "Two-tool agent · SAP history + Neo4j fault graphs", 60, "fig1.svg")
    fig_card(2, "qc", "Counted, read, logged", "QC counting module",
             ["Two cameras, three models, and every", "box on the line accounted for."],
             ["Counting and label checks with a full", "audit trail, no clipboard required."],
             ["YOLO 26s", "SAM 3", "Gemma 4 9B", "vLLM", "PostgreSQL", "Django", "Next.js"],
             "YOLO detects · Gemma reads labels · SAM counts", 75, "fig2.svg")
    fig_card(3, "chat", "Asked, queried, charted", "ArselaT, the sales chatbot",
             ["Ask about sales in plain English,", "get the number and the chart."],
             ["Ad-hoc reporting went from", "hours to seconds."],
             ["Flask", "Next.js", "Ollama", "AWS RDS"],
             "Natural language → SQL over live RDS data", 90, "fig3.svg")
    fig_card(4, "etl", "Bronze, silver, gold", "Medallion ETL pipeline",
             ["Serverless bronze, silver and gold", "layers that refresh themselves."],
             ["Removed 10+ hours of manual", "reconciliation every week."],
             ["AWS Lambda", "EventBridge", "S3", "SNS"],
             "Scheduled refresh · SNS alerts when anything fails", 100, "fig4.svg")
    side_card("open-scrum.svg", 6, "Open-Scrum", ["A scrum master you talk to. Standups by", "voice; the board updates as you speak."],
              ["Gemini Live", "Next.js", "Django Channels", "GitHub", "Zoho"], "Open Open-Scrum ↗", 120, "mic")
    side_card("sanskrit-rag.svg", 7, "Sanskrit RAG", ["Ask questions of Sanskrit texts in", "Sanskrit, Hindi or English."],
              ["LlamaParse", "Qdrant", "Groq", "Reranking", "Streamlit"], "Live link coming soon", 125, "leaf")
    side_card("dyui.svg", 8, "DyUI", ["Lets any LangGraph agent stream live UI", "cards to a frontend, with any model or none."],
              ["Open source", "PyPI · dyui", "npm · dyui-react"], "pip install dyui ↗", 140, "cards")
    side_card("slomo.svg", 5, "Slomo", ["Still in the drawer.", "Write-up coming soon."],
              ["Work in progress"], "Live link coming soon", 145, "drawer")
    toolkit()
    seabed()
    button("btn-portfolio.svg", "Dive into the portfolio ↗", True)
    button("btn-email.svg", "sohamdas1300@gmail.com", False)
    button("btn-gitlab.svg", "GitLab ↗", False)


if __name__ == "__main__":
    main()
