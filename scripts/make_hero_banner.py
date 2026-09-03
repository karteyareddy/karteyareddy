#!/usr/bin/env python3
from pathlib import Path

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 280" width="1200" height="280" role="img" aria-label="Karteya Reddy Banner">
  <defs>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1117" />
      <stop offset="40%" stop-color="#161b22" />
      <stop offset="75%" stop-color="#093322" />
      <stop offset="100%" stop-color="#052c36" />
    </linearGradient>
    <linearGradient id="text-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="50%" stop-color="#39D353" />
      <stop offset="100%" stop-color="#00F0FF" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Card with Rounded Corners -->
  <rect width="1200" height="280" rx="16" fill="url(#bg-grad)" stroke="#30363d" stroke-width="2" />

  <!-- Cyber Grid Lines -->
  <path d="M 0,70 L 1200,70 M 0,140 L 1200,140 M 0,210 L 1200,210" stroke="#ffffff" stroke-opacity="0.04" stroke-width="1" />
  <path d="M 200,0 L 200,280 M 400,0 L 400,280 M 600,0 L 600,280 M 800,0 L 800,280 M 1000,0 L 1000,280" stroke="#ffffff" stroke-opacity="0.04" stroke-width="1" />

  <!-- Abstract Waving Accent Lines -->
  <path d="M -50,220 Q 300,120 600,220 T 1250,160" fill="none" stroke="#00F0FF" stroke-opacity="0.25" stroke-width="3" filter="url(#glow)" />
  <path d="M -50,240 Q 300,140 600,240 T 1250,180" fill="none" stroke="#39D353" stroke-opacity="0.35" stroke-width="3" filter="url(#glow)" />

  <!-- Glowing Accent Dots & Markers -->
  <circle cx="80" cy="50" r="4" fill="#00F0FF" filter="url(#glow)" />
  <circle cx="1120" cy="50" r="4" fill="#39D353" filter="url(#glow)" />
  <circle cx="80" cy="230" r="4" fill="#39D353" filter="url(#glow)" />
  <circle cx="1120" cy="230" r="4" fill="#00F0FF" filter="url(#glow)" />

  <!-- Main Title -->
  <text x="600" y="125" text-anchor="middle" font-family="ui-sans-serif, system-ui, -apple-system, sans-serif" font-weight="900" font-size="52" fill="url(#text-grad)" letter-spacing="4" filter="url(#glow)">KARTEYA REDDY</text>

  <!-- Subtitle -->
  <text x="600" y="175" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Consolas, monospace" font-weight="600" font-size="20" fill="#c9d1d9" letter-spacing="3">AI / ML &amp; FULL-STACK SOFTWARE ENGINEER</text>

  <!-- Cyber Decorative Status -->
  <text x="600" y="225" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Consolas, monospace" font-size="13" fill="#39D353" letter-spacing="2">[ SYSTEM_STATUS // ONLINE ]</text>
</svg>'''

Path('assets/hero-banner.svg').write_text(svg, encoding='utf-8')
print('Wrote assets/hero-banner.svg')
