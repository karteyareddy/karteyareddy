#!/usr/bin/env python3
"""Draws the "Signal Path" profile assets from identity.json.

    python scripts/identity.py --data identity.json --out assets

Every SVG is self-contained: system fonts only, no scripts, no external
references. Motion is CSS keyframes plus a little SMIL (gradient flow, comets,
the typewriter), and the CSS part switches off under prefers-reduced-motion.
Edit identity.json and re-run; nothing in here needs touching for content.
"""
import argparse
import json
import random
from pathlib import Path
from xml.sax.saxutils import escape

SANS = "'Segoe UI',Inter,-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"

# Aurora palette: electric cyan → blue → violet → magenta, amber only as a spark.
P = {"cyan": "#00E5FF", "blue": "#4C8DFF", "violet": "#A855F7", "pink": "#FF3DA6", "amber": "#FFB224"}
C = {
    "bg": "#06080D", "panel": "#0A0D14", "chip": "#0F131C", "edge": "#1C2433", "edge2": "#2B3650",
    "text": "#EEF2FA", "muted": "#A3ADC2", "dim": "#64708A", "mid": "#7E8BA6",
    "cyan": P["cyan"], "blue": P["blue"], "violet": P["violet"], "pink": P["pink"],
}
STOPS = [(0, P["cyan"]), (.35, P["blue"]), (.7, P["violet"]), (1, P["pink"])]

BASE_CSS = (
    f".s{{font-family:{SANS}}}.m{{font-family:{MONO}}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)

# Shared motion vocabulary. Every file includes it; unused rules cost a few bytes.
FX_CSS = (
    ".up{opacity:0;animation:up .9s cubic-bezier(.2,.7,.2,1) forwards}"
    "@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}"
    ".tw{animation:tw 3s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.08}50%{opacity:.85}}"
    ".dr1,.dr2,.dr3{transform-box:fill-box;transform-origin:center}"
    ".dr1{animation:dr1 16s ease-in-out infinite alternate}@keyframes dr1{to{transform:translate(110px,50px) scale(1.2)}}"
    ".dr2{animation:dr2 21s ease-in-out infinite alternate}@keyframes dr2{to{transform:translate(-140px,40px) scale(1.1)}}"
    ".dr3{animation:dr3 18s ease-in-out infinite alternate}@keyframes dr3{to{transform:translate(70px,-70px) scale(.85)}}"
    ".scan{animation:scan 7s linear infinite}@keyframes scan{to{transform:translateX(1700px)}}"
    ".ring{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 4.4s ease-out infinite}"
    "@keyframes ring{0%{opacity:.8;transform:scale(.4)}60%,100%{opacity:0;transform:scale(1.7)}}"
    ".spin{transform-box:fill-box;transform-origin:center;animation:spin 9s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
    ".blink{animation:blink 2.4s ease-in-out infinite}@keyframes blink{50%{opacity:.2}}"
    ".breathe{animation:breathe 3.2s ease-in-out infinite}@keyframes breathe{50%{opacity:.45}}"
    ".draw{animation:draw 1.6s cubic-bezier(.2,.7,.2,1) forwards}@keyframes draw{to{stroke-dashoffset:0}}"
    ".grow{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1.2s cubic-bezier(.2,.7,.2,1) forwards}"
    "@keyframes grow{to{transform:scaleX(1)}}"
    ".caret{opacity:0;animation:caret 1s steps(2) infinite 2.6s}@keyframes caret{to{opacity:1}}"
)


# --------------------------------------------------------------------------- #
# Primitives
# --------------------------------------------------------------------------- #
def grad(gid, x1=0, x2=1200, fade=False, flow=False):
    stops = "".join(
        f'<stop offset="{o}" stop-color="{c}"{" stop-opacity=\"0\"" if fade and o == 1 else ""}/>' for o, c in STOPS)
    anim = (f'<animateTransform attributeName="gradientTransform" type="translate" '
            f'values="0 0;{(x2 - x1) * .5:.0f} 0;0 0" dur="7s" repeatCount="indefinite"/>' if flow else "")
    spread = ' spreadMethod="reflect"' if flow else ""
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0"{spread}>'
            f'{stops}{anim}</linearGradient>')


def shimmer(gid="sh", W=1200, begin="1s", dur="3.6s"):
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="260" y2="0">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/>'
            f'<animateTransform attributeName="gradientTransform" type="translate" from="-300 0" to="{W} 0" '
            f'begin="{begin}" dur="{dur}" repeatCount="indefinite"/></linearGradient>')


def svg(w, h, title, body, defs="", css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t"><title id="t">{escape(title)}</title>'
            f'<defs>{defs}</defs><style>{BASE_CSS}{FX_CSS}{css}</style>{body}</svg>\n')


def fx_defs(W, H):
    """Clip, blur and neon filters, dot grid and scan gradient shared by the panels."""
    return (f'<clipPath id="pc"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18"/></clipPath>'
            '<filter id="bl" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="55"/></filter>'
            '<filter id="ng" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="6" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '<filter id="soft" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>'
            '<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">'
            '<circle cx="1.5" cy="1.5" r="1.1" fill="#fff" opacity=".06"/></pattern>'
            '<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset=".5" stop-color="#fff" stop-opacity=".045"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')


def panel(w, h):
    return (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="{C["bg"]}" stroke="{C["edge"]}"/>'
            f'<path d="M40 .5H{min(420, w-40)}" stroke="url(#gf)" stroke-width="2"/>')


def aurora(W, H, seed=1, strength=1.0, stars=26):
    """Slow-drifting colour blobs, twinkling specks, the dot grid and a light sweep."""
    rnd = random.Random(seed)
    s = ""
    for i, (c, o) in enumerate([(P["violet"], .32), (P["cyan"], .22), (P["pink"], .2), (P["blue"], .24)]):
        cx, cy = rnd.uniform(.05, .95) * W, rnd.uniform(.05, .95) * H
        rx, ry = rnd.uniform(.16, .28) * W, rnd.uniform(.3, .6) * H
        s += (f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{c}" '
              f'opacity="{o * strength:.2f}" class="dr{i % 3 + 1}" filter="url(#bl)"/>')
    for _ in range(stars):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.choice([1, 1, 1.4, 1.8])
        s += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" class="tw" '
              f'style="animation-delay:-{rnd.uniform(0, 4):.1f}s;animation-duration:{rnd.uniform(2.4, 5):.1f}s"/>')
    s += f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="url(#dots)"/>'
    s += f'<rect x="-320" y="0" width="320" height="{H}" fill="url(#scan)" class="scan"/>'
    return f'<g clip-path="url(#pc)">{s}</g>'


def neon_text(x, y, text, size, weight=700, cls="s", extra="", fill=None, ls="-1"):
    """Headline with a soft coloured glow sitting behind it."""
    fill = fill or C["text"]
    # the glow copy skips any light "lead" span so only the main name glows
    glow = text.replace(f'fill="{C["muted"]}" class="lead"', 'fill="none"')
    return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" font-weight="{weight}" fill="url(#g)" '
            f'letter-spacing="{ls}" filter="url(#soft)" opacity=".7"{extra}>{glow}</text>'
            f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'letter-spacing="{ls}"{extra}>{text}</text>')


def tw(text, size, mono=False, bold=False):
    """Rough text width; deliberately generous so layouts keep slack across fonts."""
    if mono:
        return len(text) * size * 0.61
    k = 0.57 if bold else 0.53
    narrow = sum(text.count(ch) for ch in "il.,'|:;!()· ")
    return (len(text) - narrow * 0.55) * size * k


def wrap(text, size, width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if tw(trial, size) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def chip(x, y, label, size=20, h=40, core=False, pad=16, delay=None):
    w = tw(label, size) + pad * 2
    stroke = "url(#gc)" if core else C["edge2"]
    cls = ' class="up"' if delay is not None else ""
    st = f' style="animation-delay:{delay:.2f}s"' if delay is not None else ""
    glow = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="none" stroke="url(#gc)" '
            f'stroke-width="6" opacity=".35" filter="url(#soft)" class="breathe"/>' if core else "")
    return w, (f'<g{cls}{st}>{glow}'
               f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{C["chip"]}" '
               f'stroke="{stroke}" stroke-width="{1.6 if core else 1}"/>'
               f'<text x="{x + w/2:.1f}" y="{y + h/2 + size*0.36:.1f}" class="s" font-size="{size}" '
               f'fill="{C["text"] if core else C["muted"]}" text-anchor="middle">{escape(label)}</text></g>')


def node(x, y, r=14, delay=0.0, color=None):
    """Pipeline node: spinning dashed halo, ripple, gradient core."""
    color = color or C["cyan"]
    return (f'<circle cx="{x}" cy="{y}" r="{r + 6}" fill="none" stroke="{color}" stroke-width="1" '
            f'stroke-dasharray="3 7" opacity=".55" class="spin"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}" class="ring" style="animation-delay:{delay:.1f}s"/>'
            f'<circle cx="{x}" cy="{y}" r="7" fill="{C["bg"]}" stroke="url(#g)" stroke-width="2"/>'
            f'<circle cx="{x}" cy="{y}" r="2.8" fill="{color}" filter="url(#ng)"/>')


def comet(path, dur="5.5s", begin="0s", color="#fff", r=4):
    return (f'<circle r="{r}" fill="{color}" filter="url(#ng)">'
            f'<animateMotion dur="{dur}" begin="{begin}" repeatCount="indefinite" path="{path}"/></circle>')


def typewriter(x, y, before, after, size, clip_id="tc", begin="0.7s", dur="1.6s", W=1200):
    """`before` in plain text, `after` in flowing gradient, revealed left to right with a caret."""
    width = tw(before + " " + after, size) * 1.02 + 8
    text = (f'<g clip-path="url(#{clip_id})"><text x="{x}" y="{y}" class="s" font-size="{size}" font-weight="600" fill="{C["text"]}">'
            f'{escape(before)} <tspan fill="url(#gt)">{escape(after)}</tspan></text></g>'
            f'<rect x="{x + width - 2:.0f}" y="{y - size * .82:.0f}" width="3" height="{size * .95:.0f}" fill="{C["cyan"]}" class="caret"/>')
    clip = (f'<clipPath id="{clip_id}"><rect x="{x - 4}" y="{y - size}" width="0" height="{size * 1.4:.0f}">'
            f'<animate attributeName="width" from="0" to="{width + 8:.0f}" begin="{begin}" dur="{dur}" fill="freeze"/></rect></clipPath>')
    return text, clip


# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
def hero(d):
    W, H = 1200, 460
    p, stages = d["person"], d["pipeline"]
    trace = "M56 372 H236 L258 350 H516 L538 372 H796 L818 350 H1144"
    node_xy = [(176, 372), (420, 350), (690, 372), (970, 350)]
    nodes = ""
    for i, ((x, y), st) in enumerate(zip(node_xy, stages)):
        up = y == 350
        ly, cy = (y - 30, y - 52) if up else (y + 44, y + 66)
        col = [P["cyan"], P["blue"], P["violet"], P["pink"]][i]
        nodes += node(x, y, delay=i * 1.1, color=col)
        nodes += (f'<g class="up" style="animation-delay:{1.2 + i * .15:.2f}s">'
                  f'<text x="{x}" y="{ly}" class="m" font-size="15" letter-spacing="3" fill="{col}" '
                  f'text-anchor="middle" font-weight="700">{escape(st["verb"])}</text>'
                  f'<text x="{x}" y="{cy}" class="s" font-size="15" fill="{C["dim"]}" text-anchor="middle">{escape(st["with"])}</text></g>')
    tag, tag_clip = typewriter(56, 218, p["tagline_a"], p["tagline_b"], 32)
    body = (
        panel(W, H) + aurora(W, H, seed=7)
        + f'<g class="up"><text x="56" y="76" class="m" font-size="15" letter-spacing="3" fill="{C["dim"]}">'
          f'<tspan fill="{C["cyan"]}" font-weight="700">{escape(p["handle"].upper())}</tspan>'
          f'<tspan dx="14">/</tspan><tspan dx="14">{escape(p["eyebrow"].upper())}</tspan></text></g>'
        + f'<g class="up" style="animation-delay:.3s">'
          f'<rect x="896" y="52" width="248" height="36" rx="18" fill="{C["chip"]}" stroke="{C["edge2"]}"/>'
          f'<circle cx="918" cy="70" r="9" fill="none" stroke="{C["cyan"]}" class="ring"/>'
          f'<circle cx="918" cy="70" r="5" fill="{C["cyan"]}" class="blink" filter="url(#ng)"/>'
          f'<text x="934" y="75.5" class="m" font-size="14" fill="{C["muted"]}">{escape(p["status"])}</text></g>'
        + f'<g class="up" style="animation-delay:.2s">'
        + neon_text(54, 158, f'<tspan font-weight="300" fill="{C["muted"]}" class="lead">{escape(p["name_lead"])} </tspan>{escape(p["name_main"])}', 62)
        + '</g>'
        + tag
        + f'<g class="up" style="animation-delay:1s"><text x="56" y="258" class="s" font-size="19" fill="{C["muted"]}">{escape(p["subline"])}</text></g>'
        + f'<path d="{trace}" fill="none" stroke="{C["edge2"]}" stroke-width="2"/>'
        + f'<path d="{trace}" fill="none" stroke="url(#g)" stroke-width="2.5" stroke-linecap="round" class="pulse"/>'
        + f'<path d="{trace}" fill="none" stroke="url(#g)" stroke-width="8" stroke-linecap="round" class="pulse" opacity=".35" filter="url(#soft)"/>'
        + comet(trace) + comet(trace, dur="5.5s", begin="2.7s", color=P["cyan"], r=3)
        + f'<circle cx="56" cy="372" r="4" fill="{C["dim"]}"/>'
        + f'<path d="M1144 362 l12 10 l-12 10" fill="none" stroke="{P["pink"]}" stroke-width="2.5" filter="url(#ng)"/>'
        + nodes
    )
    defs = (fx_defs(W, H) + grad("g", 56, 1144, flow=True) + grad("gf", 40, 420, fade=True) + grad("gt", 300, 760, flow=True) + tag_clip)
    css = (".pulse{stroke-dasharray:150 1150;stroke-dashoffset:1300;animation:run 5.5s linear infinite}"
           "@keyframes run{to{stroke-dashoffset:0}}")
    title = f'{p["full_name"]} — {p["eyebrow"]}. {p["tagline_a"]} {p["tagline_b"]}'
    return svg(W, H, title, body, defs, css)


# --------------------------------------------------------------------------- #
# Section header: transparent, mid-tone, readable on light and dark GitHub
# --------------------------------------------------------------------------- #
def header(idx, title, path, W=1200):
    H = 118
    title_w = tw(title, 44, bold=True)
    x_line = 74 + title_w + 32
    R = W - 40
    line_len = max(R - x_line, 0)
    body = (
        f'<path d="M40 0 V48" stroke="url(#gv)" stroke-width="2"/>'
        f'<circle cx="40" cy="62" r="15" fill="none" stroke="{C["blue"]}" stroke-width="1" stroke-dasharray="3 6" opacity=".6" class="spin"/>'
        f'<circle cx="40" cy="62" r="9" fill="none" stroke="url(#g)" stroke-width="2.5"/>'
        f'<circle cx="40" cy="62" r="9" fill="none" stroke="{C["blue"]}" class="ring"/>'
        f'<circle cx="40" cy="62" r="3" fill="{C["cyan"]}" filter="url(#ng)"/>'
        f'<g class="up"><text x="74" y="46" class="m" font-size="16" letter-spacing="3" fill="{C["blue"]}" font-weight="700">{idx}</text></g>'
        f'<g class="up" style="animation-delay:.15s">'
        f'<text x="72" y="96" class="s" font-size="44" font-weight="700" fill="url(#g)" letter-spacing="-.5">{escape(title)}</text>'
        f'<text x="72" y="96" class="s" font-size="44" font-weight="700" fill="url(#sh)" letter-spacing="-.5">{escape(title)}</text></g>'
        + (f'<path d="M{x_line:.0f} 82 H{R}" stroke="url(#gl)" stroke-width="1.5" opacity=".7" '
           f'stroke-dasharray="{line_len:.0f}" stroke-dashoffset="{line_len:.0f}" class="draw" style="animation-delay:.3s"/>' if x_line < R - 40 else "")
        + f'<g class="up" style="animation-delay:.4s"><text x="{R}" y="46" class="m" font-size="15" fill="{C["mid"]}" text-anchor="end">{escape(path)}</text></g>'
    )
    defs = (grad("g", 30, 74 + title_w, flow=True) + grad("gl", x_line, R, fade=True) + shimmer("sh", W)
            + '<filter id="ng" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3" result="b"/>'
              '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            + f'<linearGradient id="gv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["blue"]}" stop-opacity="0"/>'
              f'<stop offset="1" stop-color="{P["blue"]}" stop-opacity=".8"/></linearGradient>')
    return svg(W, H, f"{idx} — {title}", body, defs)


# --------------------------------------------------------------------------- #
# Technology arsenal
# --------------------------------------------------------------------------- #
def arsenal(groups, W=1200):
    narrow = W < 800
    m = 40 if narrow else 56
    x0, x1, label_x = (m if narrow else 312), W - m, m
    y, body, alt, n = 60, "", [], 0
    for gi, g in enumerate(groups):
        if gi:
            body += f'<path d="M{m} {y - 20} H{W - m}" stroke="{C["edge"]}"/>'
        row_top = y
        if narrow:
            y += 44
        x = x0
        for item in g["items"]:
            label, core = (item[1:], True) if item.startswith("*") else (item, False)
            w = tw(label, 21) + 32
            if x + w > x1:
                x, y = x0, y + 54
            cw, frag = chip(x, y, label, size=21, h=42, core=core, delay=.15 + n * .045)
            body += frag
            x += cw + 12
            n += 1
        lab = (f'<g class="up" style="animation-delay:{.1 + gi * .08:.2f}s">'
               f'<text x="{label_x}" y="{row_top + 27}" class="m" font-size="{18 if narrow else 15}" letter-spacing="3" '
               f'fill="{C["cyan"]}" font-weight="700">{escape(g["label"].upper())}</text>'
               f'<text x="{x1 if narrow else label_x}" y="{row_top + (27 if narrow else 50)}" class="s" font-size="{18 if narrow else 15}" '
               f'fill="{C["dim"]}"{" text-anchor=\"end\"" if narrow else ""}>{escape(g["note"])}</text></g>')
        body += lab
        alt.append(f'{g["label"]}: ' + ", ".join(i.lstrip("*") for i in g["items"]))
        y += 42 + 42
    y += 2
    legend = (f'<g class="up" style="animation-delay:1.4s">'
              f'<rect x="{m}" y="{y - 9}" width="26" height="18" rx="9" fill="none" stroke="url(#gc)" stroke-width="1.6"/>'
              f'<text x="{m + 38}" y="{y + 5}" class="s" font-size="{18 if narrow else 15}" fill="{C["dim"]}">'
              f'{"Used in public repos below." if narrow else "Outlined in colour: used in the public repositories below."}</text></g>')
    H = y + 36
    body = panel(W, H) + aurora(W, H, seed=11, strength=.7, stars=18) + body + legend
    defs = fx_defs(W, H) + grad("gc", x0, x1, flow=True) + grad("gf", 40, min(420, W - 40), fade=True)
    return svg(W, H, "Technology arsenal. " + ". ".join(alt), body, defs)


# --------------------------------------------------------------------------- #
# Project plates, each with its own small illustration
# --------------------------------------------------------------------------- #
def art_traffic():
    xs, ys = [820, 940, 1060], [86, 166, 246]
    s = ""
    for x in xs:
        s += f'<path d="M{x} 50 V282" stroke="{C["edge2"]}" stroke-width="10" stroke-linecap="round" opacity=".55"/>'
    for y in ys:
        s += f'<path d="M784 {y} H1096" stroke="{C["edge2"]}" stroke-width="10" stroke-linecap="round" opacity=".55"/>'
    route = "M784 246 H940 V166 H1060 V86 H1096"
    s += f'<path d="{route}" fill="none" stroke="url(#ga)" stroke-width="4" stroke-linecap="round" class="wave"/>'
    s += f'<path d="{route}" fill="none" stroke="url(#ga)" stroke-width="10" stroke-linecap="round" class="wave" opacity=".3" filter="url(#soft)"/>'
    cars = [("M784 246 H1096", "5s", P["cyan"], "0s"), ("M940 50 V282", "7s", P["pink"], "1s"),
            ("M1096 86 H784", "6s", P["amber"], "2.5s"), ("M820 282 V50", "8s", P["violet"], ".5s")]
    for path, dur, col, begin in cars:
        s += (f'<rect x="-8" y="-4" width="16" height="8" rx="3" fill="{col}" filter="url(#ng)">'
              f'<animateMotion dur="{dur}" begin="{begin}" repeatCount="indefinite" rotate="auto" path="{path}"/></rect>')
    for i, (x, y) in enumerate((x, y) for y in ys for x in xs):
        s += (f'<rect x="{x-11}" y="{y-11}" width="22" height="22" rx="6" fill="{C["bg"]}" stroke="{C["edge2"]}"/>'
              f'<circle cx="{x}" cy="{y}" r="5" class="sig" style="animation-delay:-{(i*0.7)%3:.1f}s" filter="url(#ng)"/>')
    s += f'<text x="1096" y="306" class="m" font-size="13" fill="{C["dim"]}" text-anchor="end">QUBO → QAOA → green wave</text>'
    css = (".wave{stroke-dasharray:14 10;animation:flow 1.6s linear infinite}@keyframes flow{to{stroke-dashoffset:-48}}"
           f".sig{{animation:sig 3s steps(1) infinite}}@keyframes sig{{0%{{fill:{P['cyan']}}}33%{{fill:{P['amber']}}}66%{{fill:{P['pink']}}}}}")
    return s, css


def art_hand():
    # a simplified 21-point hand, MediaPipe ordering: wrist, then 4 joints per finger
    pts = [(0, 0),
           (-38, -22), (-64, -52), (-80, -82), (-92, -108),
           (-26, -92), (-32, -136), (-35, -164), (-37, -188),
           (0, -98), (0, -146), (0, -178), (0, -204),
           (24, -92), (30, -138), (33, -168), (35, -192),
           (44, -78), (56, -114), (63, -138), (68, -160)]
    ox, oy = 930, 262
    Pt = [(ox + x * 1.05, oy + y * 1.05) for x, y in pts]
    bones = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
             (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]
    s = "".join(f'<path d="M{Pt[a][0]:.0f} {Pt[a][1]:.0f} L{Pt[b][0]:.0f} {Pt[b][1]:.0f}" stroke="{C["edge2"]}" stroke-width="3"/>'
                for a, b in bones)
    s += "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{5 if i in (4, 8, 12, 16, 20) else 4}" fill="url(#ga)" class="lm" '
                 f'style="animation-delay:{i*0.08:.2f}s" filter="url(#ng)"/>' for i, (x, y) in enumerate(Pt))
    for k, i in enumerate((4, 8, 12, 16, 20)):
        x, y = Pt[i]
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="none" stroke="{P["cyan"]}" class="ring" style="animation-delay:{k*.5:.1f}s"/>'
    # scanning beam across the hand
    s += ('<clipPath id="hc"><rect x="820" y="40" width="200" height="240"/></clipPath>'
          f'<g clip-path="url(#hc)"><rect x="820" y="-40" width="200" height="34" fill="url(#beam)" class="beam"/></g>')
    # confidence gate
    s += (f'<text x="1040" y="118" class="m" font-size="13" fill="{C["dim"]}">confidence</text>'
          f'<rect x="1040" y="128" width="100" height="8" rx="4" fill="{C["edge"]}"/>'
          f'<rect x="1040" y="128" width="0" height="8" rx="4" fill="url(#ga)">'
          '<animate attributeName="width" values="0;91;91;0" keyTimes="0;.3;.85;1" dur="5s" repeatCount="indefinite"/></rect>'
          f'<path d="M1125 122 V142" stroke="{C["muted"]}" stroke-width="1.5" stroke-dasharray="2 2"/>'
          f'<text x="1040" y="160" class="m" font-size="13" fill="{C["cyan"]}">0.91 ≥ 0.85</text>'
          f'<text x="1040" y="182" class="m" font-size="13" fill="{C["dim"]}">else → human</text>')
    css = (".lm{animation:lm 3.2s ease-in-out infinite}@keyframes lm{50%{opacity:.35}}"
           ".beam{animation:beam 4s ease-in-out infinite}@keyframes beam{to{transform:translateY(330px)}}")
    defs = (f'<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["cyan"]}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{P["cyan"]}" stop-opacity=".35"/><stop offset="1" stop-color="{P["cyan"]}" stop-opacity="0"/></linearGradient>')
    return s + f'<defs>{defs}</defs>', css


def art_chat():
    dots = "".join(f'<circle cx="{912 + i*14}" cy="156" r="4" fill="{C["muted"]}" class="dot" style="animation-delay:{i*.15:.2f}s"/>' for i in range(3))
    s = (f'<rect x="790" y="62" width="230" height="46" rx="16" fill="{C["chip"]}" stroke="{C["edge2"]}"/>'
         f'<text x="810" y="91" class="s" font-size="16" fill="{C["muted"]}">Can we move it to 6 pm?</text>'
         # typing indicator, then the draft replaces it
         f'<g class="c1"><rect x="892" y="136" width="78" height="40" rx="14" fill="{C["chip"]}" stroke="{C["edge2"]}"/>{dots}</g>'
         f'<g class="c2"><rect x="880" y="128" width="262" height="76" rx="16" fill="{C["chip"]}" stroke="url(#ga)" stroke-width="1.8" stroke-dasharray="6 5" class="draft"/>'
         f'<text x="900" y="156" class="m" font-size="12" fill="{C["cyan"]}" letter-spacing="2">AI DRAFT · MEMORY ON</text>'
         f'<text x="900" y="184" class="s" font-size="16" fill="{C["text"]}">Sure — 6 pm works. See you then.</text></g>'
         f'<g class="c3"><rect x="960" y="222" width="96" height="34" rx="17" fill="url(#ga)" filter="url(#ng)" class="ap"/>'
         f'<text x="1008" y="244" class="s" font-size="15" font-weight="700" fill="{C["bg"]}" text-anchor="middle">Approve</text>'
         f'<rect x="1066" y="222" width="76" height="34" rx="17" fill="none" stroke="{C["edge2"]}"/>'
         f'<text x="1104" y="244" class="s" font-size="15" fill="{C["muted"]}" text-anchor="middle">Edit</text></g>'
         f'<text x="1142" y="290" class="m" font-size="13" fill="{C["dim"]}" text-anchor="end">nothing sends without a human</text>')
    css = (".draft{animation:dash 6s linear infinite}@keyframes dash{to{stroke-dashoffset:-110}}"
           ".c1{animation:c1 9s infinite}@keyframes c1{0%,3%{opacity:0}8%,26%{opacity:1}30%,100%{opacity:0}}"
           ".c2{animation:c2 9s infinite}@keyframes c2{0%,30%{opacity:0;transform:translateY(8px)}36%,100%{opacity:1;transform:none}}"
           ".c3{animation:c3 9s infinite}@keyframes c3{0%,44%{opacity:0}50%,100%{opacity:1}}"
           ".dot{animation:bo 1s ease-in-out infinite}@keyframes bo{50%{transform:translateY(-4px)}}"
           ".ap{animation:ap 2s ease-in-out infinite}@keyframes ap{50%{opacity:.75}}")
    return s, css


ART = {"traffic": art_traffic, "hand": art_hand, "chat": art_chat}


def plate(i, pr):
    W, H = 1200, 330
    art, css = ART[pr["art"]]()
    lines = wrap(pr["pitch"], 23, 640)[:3]
    pitch = "".join(f'<text x="56" y="{174 + k*33}" class="s" font-size="23" fill="{C["muted"]}">{escape(l)}</text>'
                    for k, l in enumerate(lines))
    x, chips = 56, ""
    for k, s in enumerate(pr["stack"]):
        w, frag = chip(x, 262, s, size=17, h=34, pad=14, delay=.6 + k * .08)
        if x + w > 740:
            break
        chips += frag
        x += w + 10
    body = (panel(W, H) + aurora(W, H, seed=20 + i, strength=.8, stars=16)
            + f'<g class="up"><text x="56" y="70" class="m" font-size="15" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">'
              f'P/{i:02d}<tspan dx="14" fill="{C["dim"]}">{escape(pr["kicker"].upper())}</tspan></text></g>'
            + f'<g class="up" style="animation-delay:.15s">' + neon_text(54, 128, escape(pr["name"]), 50, ls="-.5") + '</g>'
            + f'<g class="up" style="animation-delay:.35s">{pitch}</g>' + chips
            + f'<path d="M760 40 V290" stroke="{C["edge"]}"/>'
            + art)
    defs = fx_defs(W, H) + grad("g", 54, 700, flow=True) + grad("ga", 780, 1150, flow=True) + grad("gc", 56, 740) + grad("gf", 40, 420, fade=True)
    return svg(W, H, f'{pr["name"]} — {pr["pitch"]} Built with {", ".join(pr["stack"])}.', body, defs, css)


# --------------------------------------------------------------------------- #
# Impact strip
# --------------------------------------------------------------------------- #
def impact(items):
    W, H = 1200, 210
    cw = (W - 112) / len(items)
    body = panel(W, H) + aurora(W, H, seed=31, strength=.7, stars=14)
    for k, it in enumerate(items):
        x = 56 + k * cw
        if k:
            body += f'<path d="M{x - 20:.0f} 48 V162" stroke="{C["edge"]}"/>'
        body += (f'<g class="up" style="animation-delay:{k * .15:.2f}s">'
                 + neon_text(x, 112, escape(it["value"]), 64, fill="url(#g)")
                 + f'<rect x="{x:.0f}" y="122" width="56" height="3" rx="1.5" fill="url(#g)" class="grow" style="animation-delay:{.4 + k * .15:.2f}s"/>'
                 f'<text x="{x:.0f}" y="150" class="s" font-size="19" fill="{C["text"]}">{escape(it["label"])}</text>'
                 f'<text x="{x:.0f}" y="175" class="s" font-size="16" fill="{C["dim"]}">{escape(it["sub"])}</text></g>')
    alt = "; ".join(f'{it["value"]} {it["label"]} ({it["sub"]})' for it in items)
    return svg(W, H, alt, body, fx_defs(W, H) + grad("g", 56, 1144, flow=True) + grad("gf", 40, 420, fade=True))


# --------------------------------------------------------------------------- #
# Link pills and the closing line
# --------------------------------------------------------------------------- #
GLYPH = {
    "linkedin": '<rect x="22" y="17" width="26" height="26" rx="6" fill="none" stroke="url(#g)" stroke-width="2"/>'
                '<path d="M29 28v9M29 24v.5M34 37v-9M34 31.5c0-2 1.6-3.5 3.5-3.5s3.5 1.5 3.5 3.5V37" stroke="#EEF2FA" stroke-width="2.2" stroke-linecap="round" fill="none"/>',
    "email": '<rect x="21" y="19" width="28" height="22" rx="5" fill="none" stroke="url(#g)" stroke-width="2"/>'
             '<path d="M23 22l12 9 12-9" stroke="#EEF2FA" stroke-width="2.2" fill="none" stroke-linejoin="round"/>',
    "github": '<circle cx="35" cy="30" r="13" fill="none" stroke="url(#g)" stroke-width="2"/>'
              '<path d="M30 37v-3.5c0-1.4.5-2.3 1.2-2.8-3-.4-5-1.6-5-5 0-1.2.4-2.2 1.2-3-.1-.4-.5-1.6.1-3.1 0 0 1-.3 3.3 1.2a11 11 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.5.2 2.7.1 3.1.8.8 1.2 1.8 1.2 3 0 3.4-2 4.6-5 5 .7.5 1.2 1.4 1.2 2.8V37" stroke="#EEF2FA" stroke-width="1.8" fill="none" stroke-linejoin="round"/>',
}


def pill(kind, label):
    w = int(70 + tw(label, 20) + 26)
    body = (f'<rect x="1" y="1" width="{w-2}" height="58" rx="29" fill="{C["bg"]}" stroke="url(#rot)" stroke-width="2"/>'
            f'<rect x="1" y="1" width="{w-2}" height="58" rx="29" fill="url(#sh)"/>'
            f'<g filter="url(#ng)">{GLYPH[kind]}</g>'
            f'<text x="64" y="37" class="s" font-size="20" font-weight="600" fill="{C["text"]}">{escape(label)}</text>')
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in STOPS)
    defs = (grad("g", 20, 50)
            + f'<linearGradient id="rot">{stops}<animateTransform attributeName="gradientTransform" type="rotate" '
              'from="0 .5 .5" to="360 .5 .5" dur="4s" repeatCount="indefinite"/></linearGradient>'
            + shimmer("sh", w, begin="0s", dur="2.8s").replace('x2="260"', 'x2="120"')
            + '<filter id="ng" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
              '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return svg(w, 60, label, body, defs)


def closing(d, W=1200):
    narrow = W < 800
    if narrow:
        H = 190
        a, b = d["closing"].split(". ", 1)
        trace = "M40 0 V40 Q40 60 60 60 H70"
        nx, ny = 82, 60
        text = (f'<text x="108" y="70" class="s" font-size="32" font-weight="600" fill="url(#gt)">{escape(a)}.</text>'
                f'<text x="108" y="110" class="s" font-size="32" font-weight="600" fill="url(#gt)">{escape(b)}</text>'
                f'<text x="108" y="70" class="s" font-size="32" font-weight="600" fill="url(#sh)">{escape(a)}.</text>'
                f'<text x="108" y="110" class="s" font-size="32" font-weight="600" fill="url(#sh)">{escape(b)}</text>'
                f'<text x="108" y="146" class="m" font-size="15" letter-spacing="2" fill="{C["mid"]}">{escape(d["signoff"].upper())}</text>')
        gt = grad("gt", 108, 480, flow=True)
    else:
        H = 170
        trace = "M40 0 V60 Q40 84 64 84 H560"
        nx, ny = 572, 84
        text = (f'<text x="600" y="78" class="s" font-size="30" font-weight="600" fill="url(#gt)">{escape(d["closing"])}</text>'
                f'<text x="600" y="78" class="s" font-size="30" font-weight="600" fill="url(#sh)">{escape(d["closing"])}</text>'
                f'<text x="600" y="110" class="m" font-size="14" letter-spacing="3" fill="{C["mid"]}">{escape(d["signoff"].upper())}</text>')
        gt = grad("gt", 600, 1100, flow=True)
    orbit = f"M{nx + 18} {ny} A18 18 0 1 1 {nx - 18} {ny} A18 18 0 1 1 {nx + 18} {ny}"
    body = (f'<path d="{trace}" fill="none" stroke="url(#g)" stroke-width="2" stroke-dasharray="700" stroke-dashoffset="700" class="draw"/>'
            f'<circle cx="{nx}" cy="{ny}" r="9" fill="none" stroke="{P["violet"]}" stroke-width="2.5"/>'
            f'<circle cx="{nx}" cy="{ny}" r="3.5" fill="{P["violet"]}" class="blink" filter="url(#ng)"/>'
            f'<circle r="2.5" fill="{P["cyan"]}" filter="url(#ng)"><animateMotion dur="3s" repeatCount="indefinite" path="{orbit}"/></circle>'
            f'<g class="up" style="animation-delay:.8s">{text}</g>')
    defs = (grad("g", 40, 600) + gt + shimmer("sh", W, begin="2s")
            + '<filter id="ng" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3" result="b"/>'
              '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return svg(W, H, d["closing"], body, defs)


# --------------------------------------------------------------------------- #
# Phone-width variants (served through <picture> at max-width 700px)
# --------------------------------------------------------------------------- #
def hero_m(d):
    W = 600
    p, stages = d["person"], d["pipeline"]
    sub = wrap(p["subline"], 21, 520)
    y_sub = 330
    top = y_sub + 30 * len(sub) + 40
    gap = 86
    trace_end = top + gap * (len(stages) - 1)
    H = trace_end + 70
    nodes = ""
    for i, st in enumerate(stages):
        y = top + i * gap
        col = [P["cyan"], P["blue"], P["violet"], P["pink"]][i]
        nodes += node(56, y, delay=i * 1.1, color=col)
        nodes += (f'<g class="up" style="animation-delay:{1.2 + i * .15:.2f}s">'
                  f'<text x="92" y="{y - 4}" class="m" font-size="19" letter-spacing="3" fill="{col}" font-weight="700">{escape(st["verb"])}</text>'
                  f'<text x="92" y="{y + 22}" class="s" font-size="19" fill="{C["dim"]}">{escape(st["with"])}</text></g>')
    trace = f"M56 {top - 30} V{trace_end + 30}"
    tb1, tb2 = p["tagline_b"].split()[0], " ".join(p["tagline_b"].split()[1:])
    body = (panel(W, H) + aurora(W, H, seed=7, stars=16)
            + f'<g class="up"><text x="40" y="70" class="m" font-size="17" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">{escape(p["handle"].upper())}</text>'
            + f'<text x="40" y="98" class="m" font-size="16" letter-spacing="2" fill="{C["dim"]}">{escape(p["eyebrow"].upper())}</text></g>'
            + f'<g class="up" style="animation-delay:.15s"><text x="38" y="168" class="s" font-size="50" font-weight="300" fill="{C["muted"]}">{escape(p["name_lead"])}</text></g>'
            + f'<g class="up" style="animation-delay:.3s">' + neon_text(38, 224, escape(p["name_main"]), 54) + '</g>'
            + f'<g class="up" style="animation-delay:.6s"><text x="40" y="276" class="s" font-size="30" font-weight="600" fill="{C["text"]}">{escape(p["tagline_a"])} '
              f'<tspan fill="url(#gt)">{escape(tb1)}</tspan></text>'
            + f'<text x="40" y="312" class="s" font-size="30" font-weight="600" fill="url(#gt)">{escape(tb2)}</text></g>'
            + f'<g class="up" style="animation-delay:.9s">'
            + "".join(f'<text x="40" y="{y_sub + 24 + k*30}" class="s" font-size="21" fill="{C["muted"]}">{escape(l)}</text>' for k, l in enumerate(sub))
            + '</g>'
            + f'<path d="{trace}" stroke="{C["edge2"]}" stroke-width="2"/>'
            + f'<path d="{trace}" stroke="url(#gy)" stroke-width="2.5" stroke-linecap="round" class="pulse"/>'
            + f'<path d="{trace}" stroke="url(#gy)" stroke-width="8" stroke-linecap="round" class="pulse" opacity=".35" filter="url(#soft)"/>'
            + comet(trace, dur="5s")
            + nodes)
    L = trace_end - top + 60
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in STOPS)
    defs = (fx_defs(W, H) + grad("g", 38, 560, flow=True) + grad("gf", 40, 420, fade=True) + grad("gt", 40, 420, flow=True)
            + f'<linearGradient id="gy" gradientUnits="userSpaceOnUse" x1="0" y1="{top-30}" x2="0" y2="{trace_end+30}">{stops}</linearGradient>')
    css = (f".pulse{{stroke-dasharray:70 {L+70};animation:run 5s linear infinite}}"
           f"@keyframes run{{from{{stroke-dashoffset:{L+70}}}to{{stroke-dashoffset:0}}}}")
    return svg(W, H, f'{p["full_name"]} — {p["eyebrow"]}. {p["tagline_a"]} {p["tagline_b"]}', body, defs, css)


def plate_m(i, pr):
    W = 600
    art, css = ART[pr["art"]]()
    lines = wrap(pr["pitch"], 23, 520)
    y = 186
    pitch = "".join(f'<text x="40" y="{y + k*33}" class="s" font-size="23" fill="{C["muted"]}">{escape(l)}</text>'
                    for k, l in enumerate(lines))
    y += 33 * len(lines) + 8
    x, chips = 40, ""
    for k, s in enumerate(pr["stack"]):
        w = tw(s, 19) + 28
        if x + w > W - 40:
            x, y = 40, y + 46
        _, frag = chip(x, y, s, size=19, h=36, pad=14, delay=.6 + k * .08)
        chips += frag
        x += w + 10
    art_top = y + 70
    H = art_top + 300
    body = (panel(W, H) + aurora(W, H, seed=20 + i, strength=.8, stars=14)
            + f'<g class="up"><text x="40" y="70" class="m" font-size="17" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">P/{i:02d}</text>'
            + f'<text x="40" y="98" class="m" font-size="15" letter-spacing="2" fill="{C["dim"]}">{escape(pr["kicker"].upper())}</text></g>'
            + f'<g class="up" style="animation-delay:.15s">' + neon_text(38, 150, escape(pr["name"]), 46, ls="-.5") + '</g>'
            + f'<g class="up" style="animation-delay:.35s">{pitch}</g>' + chips
            + f'<path d="M40 {art_top - 30} H{W-40}" stroke="{C["edge"]}"/>'
            + f'<g transform="translate(-666 {art_top - 50})">{art}</g>')
    defs = fx_defs(W, H) + grad("g", 38, 560, flow=True) + grad("ga", 780, 1150, flow=True) + grad("gc", 40, 560) + grad("gf", 40, 420, fade=True)
    return svg(W, H, f'{pr["name"]} — {pr["pitch"]} Built with {", ".join(pr["stack"])}.', body, defs, css)


def impact_m(items):
    W, H = 600, 420
    body = panel(W, H) + aurora(W, H, seed=31, strength=.7, stars=12) + f'<path d="M300 44 V376 M40 210 H560" stroke="{C["edge"]}"/>'
    for k, it in enumerate(items):
        x, y = (40 if k % 2 == 0 else 330), (110 if k < 2 else 290)
        body += (f'<g class="up" style="animation-delay:{k * .15:.2f}s">'
                 + neon_text(x, y, escape(it["value"]), 54, fill="url(#g)")
                 + f'<rect x="{x}" y="{y + 10}" width="48" height="3" rx="1.5" fill="url(#g)" class="grow" style="animation-delay:{.4 + k * .15:.2f}s"/>'
                 + "".join(f'<text x="{x}" y="{y + 36 + j*24}" class="s" font-size="19" fill="{C["text"]}">{escape(l)}</text>'
                           for j, l in enumerate(wrap(it["label"], 19, 230)[:2]))
                 + '</g>')
    alt = "; ".join(f'{it["value"]} {it["label"]} ({it["sub"]})' for it in items)
    return svg(W, H, alt, body, fx_defs(W, H) + grad("g", 40, 560, flow=True) + grad("gf", 40, 420, fade=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="identity.json")
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()
    d = json.loads(Path(a.data).read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {"sp-hero.svg": hero(d), "sp-arsenal.svg": arsenal(d["arsenal"]),
             "sp-impact.svg": impact(d["impact"]), "sp-end.svg": closing(d),
             "sp-hero-m.svg": hero_m(d), "sp-arsenal-m.svg": arsenal(d["arsenal"], W=600),
             "sp-impact-m.svg": impact_m(d["impact"]), "sp-end-m.svg": closing(d, W=600)}
    for i, (key, title, path) in enumerate(d["sections"], 1):
        files[f"sp-h-{key}.svg"] = header(f"{i:02d}", title, path)
        files[f"sp-h-{key}-m.svg"] = header(f"{i:02d}", title, path, W=600)
    for i, pr in enumerate(d["projects"], 1):
        files[f"sp-p-{pr['slug']}.svg"] = plate(i, pr)
        files[f"sp-p-{pr['slug']}-m.svg"] = plate_m(i, pr)
    for kind, label in d["links"]:
        files[f"sp-link-{kind}.svg"] = pill(kind, label)
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
        print(f"{name:28} {len(text.encode()):>6} B")


if __name__ == "__main__":
    main()
