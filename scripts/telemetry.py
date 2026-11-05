#!/usr/bin/env python3
"""Draws the "Signal from GitHub" panel from public data only.

    python scripts/telemetry.py --user karteyareddy --out assets/sp-telemetry.svg

Contributions come from the public contribution calendar page, languages from
the REST API (set GITHUB_TOKEN to lift the anonymous rate limit). No third-party
stats service is involved, so the panel cannot go down with one.
"""
import argparse
import datetime as dt
import json
import os
import re
import urllib.request
from collections import defaultdict
from xml.sax.saxutils import escape

from identity import C, P, grad, panel, svg, fx_defs, aurora, neon_text, comet, set_theme, odometer, decode, code_rain

SKIP_LANGS = {"HTML", "CSS", "Dockerfile", "Makefile", "Shell", "Batchfile", "Procfile", "PowerShell"}
def lang_colors():
    return [P["cyan"], P["blue"], P["violet"], P["pink"], P["amber"], "#14B8A6", "#64748B"]


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-telemetry"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
    return body if raw else json.loads(body)


def contributions(user):
    html = get(f"https://github.com/users/{user}/contributions", raw=True)
    ids = dict(re.findall(r'data-date="(\d{4}-\d\d-\d\d)" id="(contribution-day-component-[\d-]+)"', html))
    tips = dict(re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)</tool-tip>', html))
    days = {}
    for date, cid in ids.items():
        m = re.match(r"\s*(\d+|No) contribution", tips.get(cid, ""))
        days[dt.date.fromisoformat(date)] = 0 if not m or m.group(1) == "No" else int(m.group(1))
    if not days:
        raise SystemExit("could not read the contribution calendar")
    return dict(sorted(days.items()))


def streaks(days):
    seq = list(days.items())
    longest = run = 0
    for _, n in seq:
        run = run + 1 if n else 0
        longest = max(longest, run)
    cur = 0
    i = len(seq) - 1
    if seq[i][1] == 0:          # today not counted yet: streak may still be alive
        i -= 1
    while i >= 0 and seq[i][1]:
        cur += 1
        i -= 1
    return cur, longest


def languages(user):
    repos = get(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner")
    total = defaultdict(int)
    count = 0
    for r in repos:
        if r["fork"] or r["name"].lower() == user.lower():
            continue
        count += 1
        for lang, b in get(r["languages_url"]).items():
            if lang not in SKIP_LANGS:
                total["SQL" if lang == "PLpgSQL" else lang] += b
    top = sorted(total.items(), key=lambda kv: -kv[1])
    s = sum(total.values()) or 1
    head = [kv for kv in top[:6] if kv[1] / s >= 0.005]
    rest = sum(b for _, b in top) - sum(b for _, b in head)
    out = [(k, b / s) for k, b in head]
    if rest / s >= 0.005:
        out.append(("Other", rest / s))
    return out, count


def smooth(points):
    """Catmull-Rom → cubic Bézier, clamped so the curve never dips below the baseline."""
    d = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    base = max(p[1] for p in points)
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(base, p1[1] + (p2[1] - p0[1]) / 6))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(base, p2[1] - (p3[1] - p1[1]) / 6))
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def draw(user, days, langs, repo_count):
    W, H = 1200, 560
    total = sum(days.values())
    active = sum(1 for n in days.values() if n)
    cur, longest = streaks(days)
    # A live streak is shown when there is one; otherwise that slot shows repo count
    # rather than a discouraging zero. Nothing here is estimated or rounded up.
    second = (str(cur), "day streak", "current, live") if cur else (str(repo_count), "public repos", "original work, no forks")
    stats = [(f"{total:,}", "contributions", "last 12 months"),
             second,
             (str(longest), "day streak", "longest this year"),
             (str(active), "active days", "last 12 months")]
    body = panel(W, H) + aurora(W, H, seed=41, strength=.7, stars=18) + code_rain(W, H, seed=43, cols=10)
    defs = (fx_defs(W, H) + grad("g", 56, 1144, flow=True) + grad("gf", 40, 420, fade=True)
            + f'<linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["blue"]}" stop-opacity=".32"/>'
              f'<stop offset="1" stop-color="{P["violet"]}" stop-opacity="0"/></linearGradient>')
    cw = (W - 112) / 4
    for k, (v, l, s) in enumerate(stats):
        x = 56 + k * cw
        if k:
            body += f'<path d="M{x-20:.0f} 50 V150" stroke="{C["edge"]}"/>'
        num, nd = odometer(f"{x:.0f}", 104, v, 54, begin=.3 + k * .2, uid=f"od{k}_")
        defs += nd
        body += (num + f'<g class="up" style="animation-delay:{k * .15:.2f}s">'
                 f'<text x="{x:.0f}" y="134" class="s" font-size="18" fill="{C["text"]}">{l}</text></g>'
                 + decode(f"{x:.0f}", 157, s, 15, cls="s", delay=.6 + k * .15))

    # weekly signal: the calendar collapsed into one waveform
    dates = list(days)
    weeks = [sum(days[d] for d in dates[i:i + 7]) for i in range(0, len(dates), 7)]
    top, base, x0, x1 = 210, 350, 56, 1144
    peak = max(weeks) or 1
    step = (x1 - x0) / max(len(weeks) - 1, 1)
    pts = [(x0 + i * step, base - (w / peak) * (base - top)) for i, w in enumerate(weeks)]
    line = smooth(pts)
    body += (decode(56, 196, "WEEKLY SIGNAL", 14, fill=C["cyan"], extra=' letter-spacing="3" font-weight="700"', delay=.8)
             + f'<text x="1144" y="196" class="m" font-size="13" fill="{C["dim"]}" text-anchor="end">peak week · {peak}</text>'
             f'<path d="M56 {base} H1144" stroke="{C["edge"]}"/>'
             f'<path d="{line} L{x1} {base} L{x0} {base} Z" fill="url(#ga)"/>'
             f'<path d="{line}" fill="none" stroke="url(#g)" stroke-width="9" stroke-linejoin="round" class="trace" opacity=".35" filter="url(#soft)"/>'
             f'<path d="{line}" fill="none" stroke="url(#g)" stroke-width="2.5" stroke-linejoin="round" class="trace"/>'
             + comet(line, dur="9s", begin="2.6s", r=5) + comet(line, dur="9s", begin="2.72s", r=3.5)
             + comet(line, dur="9s", begin="2.84s", r=2.4) + comet(line, dur="9s", begin="2.96s", r=1.6)
             + comet(line, dur="9s", begin="7s", color=P["cyan"], r=3))
    last = None
    for i in range(0, len(dates), 7):
        m = dates[i].strftime("%b")
        if m != last and i // 7 < len(pts):
            body += f'<text x="{pts[i//7][0]:.0f}" y="{base + 24}" class="m" font-size="12" fill="{C["dim"]}">{m.upper()}</text>'
            last = m

    # languages
    y = 420
    body += (decode(56, y, "LANGUAGES", 14, fill=C["cyan"], extra=' letter-spacing="3" font-weight="700"', delay=1.1)
             + f'<text x="1144" y="{y}" class="m" font-size="13" fill="{C["dim"]}" text-anchor="end">by bytes · markup excluded</text>')
    x, bw = 56.0, 1088
    bar = ""
    for k, (name, frac) in enumerate(langs):
        w = frac * bw
        bar += f'<rect x="{x:.1f}" y="{y+18}" width="{max(w-3, 1):.1f}" height="12" fill="{lang_colors()[k % 7]}"/>'
        x += w
    body += (f'<clipPath id="bar"><rect x="56" y="{y+18}" width="{bw}" height="12" rx="6"/></clipPath>'
             f'<clipPath id="fill"><rect x="56" y="{y+10}" width="0" height="28">'
             f'<animate attributeName="width" from="0" to="{bw}" begin=".6s" dur="1.8s" calcMode="spline" keySplines=".2 .7 .2 1" fill="freeze"/></rect></clipPath>'
             f'<g clip-path="url(#bar)"><g clip-path="url(#fill)">{bar}</g></g>'
             f'<g clip-path="url(#bar)"><rect x="-320" y="{y+18}" width="320" height="12" fill="url(#scan)" class="scan"/></g>')
    lx, ly = 56.0, y + 66
    for k, (name, frac) in enumerate(langs):
        label = f"{name}  {frac*100:.1f}%"
        wlab = len(label) * 18 * 0.55 + 34
        if lx + wlab > 1144:
            lx, ly = 56.0, ly + 30
        body += (f'<g class="up" style="animation-delay:{1.2 + k * .12:.2f}s">'
                 f'<circle cx="{lx+6:.1f}" cy="{ly-6}" r="6" fill="{lang_colors()[k % 7]}" filter="url(#ng)"/>'
                 f'<text x="{lx+20:.1f}" y="{ly}" class="s" font-size="18" fill="{C["text"]}">{escape(name)}'
                 f'<tspan fill="{C["dim"]}" dx="8">{frac*100:.1f}%</tspan></text></g>')
        lx += wlab + 14
    body += (f'<text x="1144" y="{H-22}" class="m" font-size="12" fill="{C["dim"]}" text-anchor="end">'
             f'public data · refreshed {dt.date.today():%d %b %Y}</text>')
    # offset lives only in the keyframe, so with motion disabled the line is simply drawn
    css = ".trace{stroke-dasharray:3000;animation:draw 2.6s ease-out both}@keyframes draw{from{stroke-dashoffset:3000}to{stroke-dashoffset:0}}"
    alt = (f"GitHub activity for {user}: {total} contributions in the last 12 months, current streak {cur} days, "
           f"longest streak {longest} days, {active} active days. Languages: "
           + ", ".join(f"{n} {f*100:.0f}%" for n, f in langs) + ".")
    return svg(W, H, alt, body, defs, css), alt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", default="assets/sp-telemetry.svg")
    a = ap.parse_args()
    days = contributions(a.user)
    cache = os.path.join(os.path.dirname(a.out) or ".", "telemetry-langs.json")
    try:
        langs, n = languages(a.user)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"langs": langs, "repos": n}, f)
    except Exception as e:  # rate limit or outage: reuse the last good language mix
        print(f"languages unavailable ({e}); using {cache}")
        with open(cache, encoding="utf-8") as f:
            c = json.load(f)
        langs, n = [tuple(x) for x in c["langs"]], c["repos"]
    for theme, out in (("dark", a.out), ("light", a.out.replace(".svg", "-light.svg"))):
        set_theme(theme)
        text, alt = draw(a.user, days, langs, n)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
    set_theme("dark")
    print(alt)


if __name__ == "__main__":
    main()
