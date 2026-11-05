#!/usr/bin/env python3
"""Draws the static "Signal Path" profile assets from identity.json.

    python scripts/identity.py --data identity.json --out assets

Every SVG is self-contained: system fonts only, no scripts, no external
references, CSS animation that switches off under prefers-reduced-motion.
Edit identity.json and re-run; nothing in here needs touching for content.
"""
import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

SANS = "'Segoe UI',Inter,-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"

C = {
    "bg": "#0A0C10", "panel": "#0E1117", "chip": "#11151D", "edge": "#1E2633",
    "edge2": "#2A3446", "text": "#E8ECF4", "muted": "#9AA3B5", "dim": "#5D6678",
    "cyan": "#22D3EE", "blue": "#4F7DFF", "violet": "#8B5CF6", "mid": "#7C8AA5",
}

BASE_CSS = (
    f".s{{font-family:{SANS}}}.m{{font-family:{MONO}}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


def grad(gid, x1=0, x2=1200, fade=False):
    end = '<stop offset="1" stop-color="#8B5CF6" stop-opacity="0"/>' if fade else '<stop offset="1" stop-color="#8B5CF6"/>'
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">'
            f'<stop offset="0" stop-color="#22D3EE"/><stop offset=".5" stop-color="#4F7DFF"/>{end}</linearGradient>')


def svg(w, h, title, body, defs="", css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t"><title id="t">{escape(title)}</title>'
            f'<defs>{defs}</defs><style>{BASE_CSS}{css}</style>{body}</svg>\n')


def panel(w, h):
    return (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="{C["bg"]}" stroke="{C["edge"]}"/>'
            f'<path d="M40 .5H{min(420, w-40)}" stroke="url(#gf)" stroke-width="2"/>')


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


def chip(x, y, label, size=20, h=40, core=False, pad=16):
    w = tw(label, size) + pad * 2
    stroke = "url(#gc)" if core else C["edge2"]
    dot = ""
    return w, (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{C["chip"]}" '
               f'stroke="{stroke}" stroke-width="{1.6 if core else 1}"/>'
               f'<text x="{x + w/2:.1f}" y="{y + h/2 + size*0.36:.1f}" class="s" font-size="{size}" '
               f'fill="{C["text"] if core else C["muted"]}" text-anchor="middle">{escape(label)}</text>{dot}')


# --------------------------------------------------------------------------- #
# Hero
# --------------------------------------------------------------------------- #
def hero(d):
    W, H = 1200, 460
    p = d["person"]
    stages = d["pipeline"]
    # the trace: a stepped line the pulse runs along, one node per stage
    trace = "M56 372 H236 L258 350 H516 L538 372 H796 L818 350 H1144"
    node_xy = [(176, 372), (420, 350), (690, 372), (970, 350)]
    nodes = ""
    for i, ((x, y), st) in enumerate(zip(node_xy, stages)):
        up = y == 350
        ly, cy = (y - 26, y - 48) if up else (y + 40, y + 62)
        nodes += (f'<circle cx="{x}" cy="{y}" r="14" fill="none" stroke="{C["cyan"]}" class="ring" '
                  f'style="animation-delay:{i*1.1:.1f}s"/>'
                  f'<circle cx="{x}" cy="{y}" r="7" fill="{C["bg"]}" stroke="url(#g)" stroke-width="2"/>'
                  f'<circle cx="{x}" cy="{y}" r="2.6" fill="{C["cyan"]}"/>'
                  f'<text x="{x}" y="{ly}" class="m" font-size="15" letter-spacing="3" fill="{C["cyan"]}" '
                  f'text-anchor="middle" font-weight="700">{escape(st["verb"])}</text>'
                  f'<text x="{x}" y="{cy if not up else cy}" class="s" font-size="15" fill="{C["dim"]}" '
                  f'text-anchor="middle">{escape(st["with"])}</text>')
    name_first, name_rest = p["name_lead"], p["name_main"]
    body = (
        panel(W, H)
        + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#dots)"/>'
        + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#glowA)"/>'
        + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#glowB)"/>'
        # eyebrow
        + f'<text x="56" y="76" class="m" font-size="15" letter-spacing="3" fill="{C["dim"]}">'
          f'<tspan fill="{C["cyan"]}" font-weight="700">{escape(p["handle"].upper())}</tspan>'
          f'<tspan dx="14">/</tspan><tspan dx="14">{escape(p["eyebrow"].upper())}</tspan></text>'
        # status chip
        + f'<rect x="896" y="52" width="248" height="36" rx="18" fill="{C["chip"]}" stroke="{C["edge2"]}"/>'
          f'<circle cx="918" cy="70" r="5" fill="{C["cyan"]}" class="blink"/>'
          f'<text x="934" y="75.5" class="m" font-size="14" fill="{C["muted"]}">{escape(p["status"])}</text>'
        # name + tagline
        + f'<text x="54" y="158" class="s" font-size="62" font-weight="700" fill="{C["text"]}" letter-spacing="-1">'
          f'<tspan font-weight="300" fill="{C["muted"]}">{escape(name_first)} </tspan>{escape(name_rest)}</text>'
        + f'<text x="56" y="218" class="s" font-size="32" font-weight="600" fill="{C["text"]}">'
          f'{escape(p["tagline_a"])} <tspan fill="url(#gt)">{escape(p["tagline_b"])}</tspan></text>'
        + f'<text x="56" y="258" class="s" font-size="19" fill="{C["muted"]}">{escape(p["subline"])}</text>'
        # pipeline trace
        + f'<path d="{trace}" fill="none" stroke="{C["edge2"]}" stroke-width="2"/>'
        + f'<path d="{trace}" fill="none" stroke="url(#g)" stroke-width="2.5" stroke-linecap="round" class="pulse"/>'
        + f'<circle cx="56" cy="372" r="4" fill="{C["dim"]}"/>'
        + f'<path d="M1144 362 l12 10 l-12 10" fill="none" stroke="{C["violet"]}" stroke-width="2.5"/>'
        + nodes
    )
    defs = (
        grad("g", 56, 1144) + grad("gf", 40, 420, fade=True) + grad("gt", 300, 760)
        + '<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">'
          '<circle cx="1.5" cy="1.5" r="1.1" fill="#fff" opacity=".055"/></pattern>'
        + '<radialGradient id="glowA" cx="1020" cy="40" r="560" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#8B5CF6" stop-opacity=".26"/><stop offset="1" stop-color="#8B5CF6" stop-opacity="0"/></radialGradient>'
        + '<radialGradient id="glowB" cx="120" cy="470" r="480" gradientUnits="userSpaceOnUse">'
          '<stop offset="0" stop-color="#22D3EE" stop-opacity=".12"/><stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></radialGradient>'
    )
    css = (
        ".pulse{stroke-dasharray:150 1150;stroke-dashoffset:1300;animation:run 5.5s linear infinite}"
        "@keyframes run{to{stroke-dashoffset:0}}"
        ".ring{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 4.4s ease-out infinite}"
        "@keyframes ring{0%{opacity:.7;transform:scale(.5)}60%,100%{opacity:0;transform:scale(1.6)}}"
        ".blink{animation:blink 2.4s ease-in-out infinite}@keyframes blink{50%{opacity:.25}}"
    )
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
    body = (
        f'<path d="M40 0 V48" stroke="url(#gv)" stroke-width="2"/>'
        f'<circle cx="40" cy="62" r="9" fill="none" stroke="url(#g)" stroke-width="2.5"/>'
        f'<circle cx="40" cy="62" r="3" fill="{C["blue"]}"/>'
        f'<text x="74" y="46" class="m" font-size="16" letter-spacing="3" fill="{C["blue"]}" font-weight="700">{idx}</text>'
        f'<text x="72" y="96" class="s" font-size="44" font-weight="700" fill="url(#g)" letter-spacing="-.5">{escape(title)}</text>'
        + (f'<path d="M{x_line:.0f} 82 H{R}" stroke="url(#gl)" stroke-width="1.5" opacity=".7"/>' if x_line < R - 40 else "")
        + f'<text x="{R}" y="46" class="m" font-size="15" fill="{C["mid"]}" text-anchor="end">{escape(path)}</text>'
    )
    defs = (grad("g", 30, 74 + title_w) + grad("gl", x_line, R, fade=True)
            + '<linearGradient id="gv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4F7DFF" stop-opacity="0"/>'
              '<stop offset="1" stop-color="#4F7DFF" stop-opacity=".8"/></linearGradient>')
    return svg(W, H, f"{idx} — {title}", body, defs)


# --------------------------------------------------------------------------- #
# Technology arsenal
# --------------------------------------------------------------------------- #
def arsenal(groups, W=1200):
    narrow = W < 800
    m = 40 if narrow else 56
    x0, x1, label_x = (m if narrow else 312), W - m, m
    y, body, alt = 60, "", []
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
            cw, frag = chip(x, y, label, size=21, h=42, core=core)
            body += frag
            x += cw + 12
        lab = (f'<text x="{label_x}" y="{row_top + 27}" class="m" font-size="{18 if narrow else 15}" letter-spacing="3" '
               f'fill="{C["cyan"]}" font-weight="700">{escape(g["label"].upper())}</text>')
        note = (f'<text x="{x1 if narrow else label_x}" y="{row_top + (27 if narrow else 50)}" class="s" font-size="{18 if narrow else 15}" '
                f'fill="{C["dim"]}"{" text-anchor=\"end\"" if narrow else ""}>{escape(g["note"])}</text>')
        body += lab + note
        alt.append(f'{g["label"]}: ' + ", ".join(i.lstrip("*") for i in g["items"]))
        y += 42 + 42
    y += 2
    legend = (f'<rect x="{m}" y="{y - 9}" width="26" height="18" rx="9" fill="none" stroke="url(#gc)" stroke-width="1.6"/>'
              f'<text x="{m + 38}" y="{y + 5}" class="s" font-size="{18 if narrow else 15}" fill="{C["dim"]}">'
              f'{"Used in public repos below." if narrow else "Outlined in colour: used in the public repositories below."}</text>')
    H = y + 36
    body = panel(W, H) + body + legend
    defs = grad("gc", x0, x1) + grad("gf", 40, min(420, W - 40), fade=True)
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
    for i, (x, y) in enumerate((x, y) for y in ys for x in xs):
        s += (f'<rect x="{x-11}" y="{y-11}" width="22" height="22" rx="6" fill="{C["bg"]}" stroke="{C["edge2"]}"/>'
              f'<circle cx="{x}" cy="{y}" r="5" class="sig" style="animation-delay:-{(i*0.7)%3:.1f}s"/>')
    s += f'<text x="1096" y="306" class="m" font-size="13" fill="{C["dim"]}" text-anchor="end">QUBO → QAOA → green wave</text>'
    css = (".wave{stroke-dasharray:14 10;animation:flow 1.6s linear infinite}@keyframes flow{to{stroke-dashoffset:-48}}"
           ".sig{animation:sig 3s steps(1) infinite}@keyframes sig{0%{fill:#22D3EE}33%{fill:#F59E0B}66%{fill:#F43F5E}}")
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
    P = [(ox + x * 1.05, oy + y * 1.05) for x, y in pts]
    bones = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
             (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]
    s = "".join(f'<path d="M{P[a][0]:.0f} {P[a][1]:.0f} L{P[b][0]:.0f} {P[b][1]:.0f}" stroke="{C["edge2"]}" stroke-width="3"/>'
                for a, b in bones)
    s += "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{5 if i in (4, 8, 12, 16, 20) else 4}" fill="url(#ga)" class="lm" '
                 f'style="animation-delay:{i*0.08:.2f}s"/>' for i, (x, y) in enumerate(P))
    # confidence gate
    s += (f'<text x="1040" y="118" class="m" font-size="13" fill="{C["dim"]}">confidence</text>'
          f'<rect x="1040" y="128" width="100" height="8" rx="4" fill="{C["edge"]}"/>'
          f'<rect x="1040" y="128" width="91" height="8" rx="4" fill="url(#ga)"/>'
          f'<path d="M1125 122 V142" stroke="{C["muted"]}" stroke-width="1.5" stroke-dasharray="2 2"/>'
          f'<text x="1040" y="160" class="m" font-size="13" fill="{C["cyan"]}">0.91 ≥ 0.85</text>'
          f'<text x="1040" y="182" class="m" font-size="13" fill="{C["dim"]}">else → human</text>')
    css = ".lm{animation:lm 3.2s ease-in-out infinite}@keyframes lm{50%{opacity:.35}}"
    return s, css


def art_chat():
    s = (f'<rect x="790" y="62" width="230" height="46" rx="16" fill="{C["chip"]}" stroke="{C["edge2"]}"/>'
         f'<text x="810" y="91" class="s" font-size="16" fill="{C["muted"]}">Can we move it to 6 pm?</text>'
         f'<rect x="880" y="128" width="262" height="76" rx="16" fill="none" stroke="url(#ga)" stroke-width="1.8" stroke-dasharray="6 5" class="draft"/>'
         f'<text x="900" y="156" class="m" font-size="12" fill="{C["cyan"]}" letter-spacing="2">AI DRAFT · MEMORY ON</text>'
         f'<text x="900" y="184" class="s" font-size="16" fill="{C["text"]}">Sure — 6 pm works. See you then.</text>'
         f'<rect x="960" y="222" width="96" height="34" rx="17" fill="url(#ga)"/>'
         f'<text x="1008" y="244" class="s" font-size="15" font-weight="700" fill="{C["bg"]}" text-anchor="middle">Approve</text>'
         f'<rect x="1066" y="222" width="76" height="34" rx="17" fill="none" stroke="{C["edge2"]}"/>'
         f'<text x="1104" y="244" class="s" font-size="15" fill="{C["muted"]}" text-anchor="middle">Edit</text>'
         f'<text x="1142" y="290" class="m" font-size="13" fill="{C["dim"]}" text-anchor="end">nothing sends without a human</text>')
    css = ".draft{animation:dash 6s linear infinite}@keyframes dash{to{stroke-dashoffset:-110}}"
    return s, css


ART = {"traffic": art_traffic, "hand": art_hand, "chat": art_chat}


def plate(i, pr):
    W, H = 1200, 330
    art, css = ART[pr["art"]]()
    lines = wrap(pr["pitch"], 23, 640)[:3]
    pitch = "".join(f'<text x="56" y="{174 + k*33}" class="s" font-size="23" fill="{C["muted"]}">{escape(l)}</text>'
                    for k, l in enumerate(lines))
    x, chips = 56, ""
    for s in pr["stack"]:
        w, frag = chip(x, 262, s, size=17, h=34, pad=14)
        if x + w > 740:
            break
        chips += frag
        x += w + 10
    body = (panel(W, H)
            + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#glow)"/>'
            + f'<text x="56" y="70" class="m" font-size="15" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">'
              f'P/{i:02d}<tspan dx="14" fill="{C["dim"]}">{escape(pr["kicker"].upper())}</tspan></text>'
            + f'<text x="54" y="128" class="s" font-size="50" font-weight="700" fill="{C["text"]}" letter-spacing="-.5">{escape(pr["name"])}</text>'
            + pitch + chips
            + f'<path d="M760 40 V290" stroke="{C["edge"]}"/>'
            + art)
    defs = (grad("ga", 780, 1150) + grad("gf", 40, 420, fade=True)
            + '<radialGradient id="glow" cx="980" cy="160" r="360" gradientUnits="userSpaceOnUse">'
              '<stop offset="0" stop-color="#4F7DFF" stop-opacity=".13"/><stop offset="1" stop-color="#4F7DFF" stop-opacity="0"/></radialGradient>')
    return svg(W, H, f'{pr["name"]} — {pr["pitch"]} Built with {", ".join(pr["stack"])}.', body, defs, css)


# --------------------------------------------------------------------------- #
# Impact strip
# --------------------------------------------------------------------------- #
def impact(items):
    W, H = 1200, 210
    cw = (W - 112) / len(items)
    body = panel(W, H)
    for k, it in enumerate(items):
        x = 56 + k * cw
        if k:
            body += f'<path d="M{x - 20:.0f} 48 V162" stroke="{C["edge"]}"/>'
        body += (f'<text x="{x:.0f}" y="112" class="s" font-size="64" font-weight="700" fill="url(#g)" letter-spacing="-1">{escape(it["value"])}</text>'
                 f'<text x="{x:.0f}" y="148" class="s" font-size="19" fill="{C["text"]}">{escape(it["label"])}</text>'
                 f'<text x="{x:.0f}" y="173" class="s" font-size="16" fill="{C["dim"]}">{escape(it["sub"])}</text>')
    alt = "; ".join(f'{it["value"]} {it["label"]} ({it["sub"]})' for it in items)
    return svg(W, H, alt, body, grad("g", 56, 1144) + grad("gf", 40, 420, fade=True))


# --------------------------------------------------------------------------- #
# Link pills and the closing line
# --------------------------------------------------------------------------- #
GLYPH = {
    "linkedin": '<rect x="22" y="17" width="26" height="26" rx="6" fill="none" stroke="url(#g)" stroke-width="2"/>'
                '<path d="M29 28v9M29 24v.5M34 37v-9M34 31.5c0-2 1.6-3.5 3.5-3.5s3.5 1.5 3.5 3.5V37" stroke="#E8ECF4" stroke-width="2.2" stroke-linecap="round" fill="none"/>',
    "email": '<rect x="21" y="19" width="28" height="22" rx="5" fill="none" stroke="url(#g)" stroke-width="2"/>'
             '<path d="M23 22l12 9 12-9" stroke="#E8ECF4" stroke-width="2.2" fill="none" stroke-linejoin="round"/>',
    "github": '<circle cx="35" cy="30" r="13" fill="none" stroke="url(#g)" stroke-width="2"/>'
              '<path d="M30 37v-3.5c0-1.4.5-2.3 1.2-2.8-3-.4-5-1.6-5-5 0-1.2.4-2.2 1.2-3-.1-.4-.5-1.6.1-3.1 0 0 1-.3 3.3 1.2a11 11 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.6 1.5.2 2.7.1 3.1.8.8 1.2 1.8 1.2 3 0 3.4-2 4.6-5 5 .7.5 1.2 1.4 1.2 2.8V37" stroke="#E8ECF4" stroke-width="1.8" fill="none" stroke-linejoin="round"/>',
}


def pill(kind, label):
    w = 70 + tw(label, 20) + 26
    body = (f'<rect x=".75" y=".75" width="{w-1.5:.0f}" height="58.5" rx="29.25" fill="{C["bg"]}" stroke="{C["edge2"]}" stroke-width="1.5"/>'
            + GLYPH[kind]
            + f'<text x="64" y="37" class="s" font-size="20" font-weight="600" fill="{C["text"]}">{escape(label)}</text>')
    return svg(int(w), 60, label, body, grad("g", 20, 50))


def closing(d):
    W, H = 1200, 170
    body = (f'<path d="M40 0 V60 Q40 84 64 84 H560" fill="none" stroke="url(#g)" stroke-width="2"/>'
            f'<circle cx="572" cy="84" r="9" fill="none" stroke="{C["violet"]}" stroke-width="2.5"/>'
            f'<circle cx="572" cy="84" r="3.5" fill="{C["violet"]}" class="blink"/>'
            f'<text x="600" y="78" class="s" font-size="30" font-weight="600" fill="url(#gt)">{escape(d["closing"])}</text>'
            f'<text x="600" y="110" class="m" font-size="14" letter-spacing="3" fill="{C["mid"]}">{escape(d["signoff"].upper())}</text>')
    css = ".blink{animation:blink 2.4s ease-in-out infinite}@keyframes blink{50%{opacity:.2}}"
    return svg(W, H, d["closing"], body, grad("g", 40, 560) + grad("gt", 600, 1100), css)


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
        nodes += (f'<circle cx="56" cy="{y}" r="14" fill="none" stroke="{C["cyan"]}" class="ring" style="animation-delay:{i*1.1:.1f}s"/>'
                  f'<circle cx="56" cy="{y}" r="8" fill="{C["bg"]}" stroke="url(#gy)" stroke-width="2"/>'
                  f'<circle cx="56" cy="{y}" r="3" fill="{C["cyan"]}"/>'
                  f'<text x="90" y="{y - 4}" class="m" font-size="19" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">{escape(st["verb"])}</text>'
                  f'<text x="90" y="{y + 22}" class="s" font-size="19" fill="{C["dim"]}">{escape(st["with"])}</text>')
    trace = f"M56 {top - 30} V{trace_end + 30}"
    body = (panel(W, H)
            + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#dots)"/>'
            + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#glowA)"/>'
            + f'<text x="40" y="70" class="m" font-size="17" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">{escape(p["handle"].upper())}</text>'
            + f'<text x="40" y="98" class="m" font-size="16" letter-spacing="2" fill="{C["dim"]}">{escape(p["eyebrow"].upper())}</text>'
            + f'<text x="38" y="168" class="s" font-size="50" font-weight="300" fill="{C["muted"]}">{escape(p["name_lead"])}</text>'
            + f'<text x="38" y="224" class="s" font-size="54" font-weight="700" fill="{C["text"]}" letter-spacing="-1">{escape(p["name_main"])}</text>'
            + f'<text x="40" y="276" class="s" font-size="30" font-weight="600" fill="{C["text"]}">{escape(p["tagline_a"])} '
              f'<tspan fill="url(#gt)">{escape(p["tagline_b"].split()[0])}</tspan></text>'
            + f'<text x="40" y="312" class="s" font-size="30" font-weight="600" fill="url(#gt)">{escape(" ".join(p["tagline_b"].split()[1:]))}</text>'
            + "".join(f'<text x="40" y="{y_sub + 24 + k*30}" class="s" font-size="21" fill="{C["muted"]}">{escape(l)}</text>' for k, l in enumerate(sub))
            + f'<path d="{trace}" stroke="{C["edge2"]}" stroke-width="2"/>'
            + f'<path d="{trace}" stroke="url(#gy)" stroke-width="2.5" stroke-linecap="round" class="pulse"/>'
            + nodes)
    L = trace_end - top + 60
    defs = (grad("gf", 40, 420, fade=True) + grad("gt", 40, 420)
            + f'<linearGradient id="gy" gradientUnits="userSpaceOnUse" x1="0" y1="{top-30}" x2="0" y2="{trace_end+30}">'
              '<stop offset="0" stop-color="#22D3EE"/><stop offset=".5" stop-color="#4F7DFF"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient>'
            + '<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="#fff" opacity=".055"/></pattern>'
            + '<radialGradient id="glowA" cx="560" cy="40" r="460" gradientUnits="userSpaceOnUse">'
              '<stop offset="0" stop-color="#8B5CF6" stop-opacity=".26"/><stop offset="1" stop-color="#8B5CF6" stop-opacity="0"/></radialGradient>')
    css = (f".pulse{{stroke-dasharray:70 {L+70};animation:run 5s linear infinite}}"
           f"@keyframes run{{from{{stroke-dashoffset:{L+70}}}to{{stroke-dashoffset:0}}}}"
           ".ring{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 4.4s ease-out infinite}"
           "@keyframes ring{0%{opacity:.7;transform:scale(.5)}60%,100%{opacity:0;transform:scale(1.6)}}")
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
    for s in pr["stack"]:
        w = tw(s, 19) + 28
        if x + w > W - 40:
            x, y = 40, y + 46
        _, frag = chip(x, y, s, size=19, h=36, pad=14)
        chips += frag
        x += w + 10
    art_top = y + 70
    H = art_top + 300
    body = (panel(W, H)
            + f'<text x="40" y="70" class="m" font-size="17" letter-spacing="3" fill="{C["cyan"]}" font-weight="700">P/{i:02d}</text>'
            + f'<text x="40" y="98" class="m" font-size="15" letter-spacing="2" fill="{C["dim"]}">{escape(pr["kicker"].upper())}</text>'
            + f'<text x="38" y="150" class="s" font-size="46" font-weight="700" fill="{C["text"]}" letter-spacing="-.5">{escape(pr["name"])}</text>'
            + pitch + chips
            + f'<path d="M40 {art_top - 30} H{W-40}" stroke="{C["edge"]}"/>'
            + f'<g transform="translate(-666 {art_top - 50})">{art}</g>')
    defs = grad("ga", 780, 1150) + grad("gf", 40, 420, fade=True)
    return svg(W, H, f'{pr["name"]} — {pr["pitch"]} Built with {", ".join(pr["stack"])}.', body, defs, css)


def impact_m(items):
    W, H = 600, 420
    body = panel(W, H) + f'<path d="M300 44 V376 M40 210 H560" stroke="{C["edge"]}"/>'
    for k, it in enumerate(items):
        x, y = (40 if k % 2 == 0 else 330), (110 if k < 2 else 290)
        body += (f'<text x="{x}" y="{y}" class="s" font-size="54" font-weight="700" fill="url(#g)" letter-spacing="-1">{escape(it["value"])}</text>'
                 + "".join(f'<text x="{x}" y="{y + 34 + j*24}" class="s" font-size="19" fill="{C["text"]}">{escape(l)}</text>'
                           for j, l in enumerate(wrap(it["label"], 19, 230)[:2])))
    alt = "; ".join(f'{it["value"]} {it["label"]} ({it["sub"]})' for it in items)
    return svg(W, H, alt, body, grad("g", 40, 560) + grad("gf", 40, 420, fade=True))


def closing_m(d):
    W, H = 600, 190
    a, b = d["closing"].split(". ", 1)
    body = (f'<path d="M40 0 V40 Q40 60 60 60 H70" fill="none" stroke="url(#g)" stroke-width="2"/>'
            f'<circle cx="82" cy="60" r="9" fill="none" stroke="{C["violet"]}" stroke-width="2.5"/>'
            f'<text x="108" y="70" class="s" font-size="32" font-weight="600" fill="url(#gt)">{escape(a)}.</text>'
            f'<text x="108" y="110" class="s" font-size="32" font-weight="600" fill="url(#gt)">{escape(b)}</text>'
            f'<text x="108" y="146" class="m" font-size="15" letter-spacing="2" fill="{C["mid"]}">{escape(d["signoff"].upper())}</text>')
    return svg(W, H, d["closing"], body, grad("g", 40, 90) + grad("gt", 108, 480))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="identity.json")
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()
    d = json.loads(Path(a.data).read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {"sp-hero.svg": hero(d), "sp-arsenal.svg": arsenal(d["arsenal"]),
             "sp-impact.svg": impact(d["impact"]), "sp-end.svg": closing(d)}
    files.update({"sp-hero-m.svg": hero_m(d), "sp-arsenal-m.svg": arsenal(d["arsenal"], W=600),
                  "sp-impact-m.svg": impact_m(d["impact"]), "sp-end-m.svg": closing_m(d)})
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
