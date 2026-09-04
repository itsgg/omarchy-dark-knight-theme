"""The Dark Knight wallpapers: three, flat, and quiet.

No blur filters and no raster blocks anywhere in this set. Every edge is a real
vector edge; the only soft thing in a frame is the vignette. The emblem appears
in all three at a different scale each time -- large as the subject, small at a
grid origin, tiny at a ring centre -- which is what ties them together.
"""
import sys, math, pathlib, tomllib
sys.path.insert(0, '.')
from bat import path

W, H = 3840, 2400

# Read from the palette rather than repeated here. These four were literals
# once, and when colors.toml was rebuilt from the wallpaper on 2026-09-04 the
# shipped wallpapers kept the old gold and became the only part of the theme
# that did not match it. A theme's own backgrounds are the last place a stale
# colour should survive.
_P = tomllib.load(open(pathlib.Path(__file__).parent.parent / "colors.toml", "rb"))

def _c(key):
    """A colour from the palette, or a message naming what is missing.

    A bare _P[key] raised KeyError at import time, which reports a missing
    palette key as a traceback from inside a wallpaper generator.
    """
    try:
        return _P[key]
    except KeyError:
        raise SystemExit(
            f"flat.py: colors.toml has no {key!r}; regenerate it with "
            "src/palette.py <wallpaper>")

INK    = _c("background")          # the ground
INK8   = _c("lighter_background")  # the one step up, for flat blocks
ACCENT = _c("accent")              # the emblem and every drawn mark
STEEL  = _c("muted")               # structure that must not compete
GOLD   = ACCENT                    # name kept for the drawing code below; there is no gold in this theme

VIGNETTE = f'''
<radialGradient id="vig" cx="0.5" cy="0.46" r="0.78">
  <stop offset="0%"   stop-color="{INK}"   stop-opacity="0"/>
  <stop offset="62%"  stop-color="{_c("dark_background")}" stop-opacity="0.42"/>
  <stop offset="100%" stop-color="{_c("darker_background")}" stop-opacity="0.88"/>
</radialGradient>'''

def svg(body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}"><defs>{VIGNETTE}{defs}</defs>'
            f'<rect width="{W}" height="{H}" fill="{INK}"/>{body}'
            f'<rect width="{W}" height="{H}" fill="url(#vig)"/></svg>')

def emblem(cx, cy, scale, stroke_op, width=3.2, fill_op=0.0):
    out = ""
    if fill_op:
        out += f'<path d="{path(scale, cx, cy)}" fill="{GOLD}" opacity="{fill_op}"/>'
    return out + (f'<path d="{path(scale, cx, cy)}" fill="none" stroke="{GOLD}" '
                  f'stroke-width="{width}" stroke-opacity="{stroke_op}" '
                  f'stroke-linejoin="round"/>')

# ------------------------------------------------------------------ 1: grid
# The origin sits on thirds, not dead centre. The emblem replaces the origin
# dot at a size where it still reads as a mark on the grid, not as the subject.
OX, OY = 1500, 1500
defs = f'''
<pattern id="fine" width="60" height="60" patternUnits="userSpaceOnUse">
  <path d="M60 0H0V60" fill="none" stroke="{STEEL}" stroke-width="1" opacity="0.16"/>
</pattern>
<pattern id="coarse" width="300" height="300" patternUnits="userSpaceOnUse">
  <path d="M300 0H0V300" fill="none" stroke="{STEEL}" stroke-width="1.5" opacity="0.32"/>
</pattern>'''
body = f'''
<rect width="{W}" height="{H}" fill="url(#fine)"/>
<rect width="{W}" height="{H}" fill="url(#coarse)"/>
<rect x="0" y="{OY}" width="{W}" height="2" fill="{GOLD}" opacity="0.30"/>
<rect x="{OX}" y="0" width="2" height="{H}" fill="{GOLD}" opacity="0.30"/>
{emblem(OX, OY, 0.50, 0.80, 2.8, fill_op=0.08)}'''
open("1-grid.svg", "w").write(svg(body, defs))

# ---------------------------------------------------------------- 2: emblem
# Outline only. Filled at this size it becomes the whole wallpaper; a 3px
# stroke keeps it a mark on a surface, which is the register the grid set.
ex, ey, es = 2380, 1420, 2.05
body = f'''
<rect x="0" y="{ey}" width="{W}" height="2" fill="{STEEL}" opacity="0.20"/>
<rect x="{ex}" y="0" width="2" height="{H}" fill="{STEEL}" opacity="0.20"/>
<path d="{path(es, ex, ey)}" fill="{INK8}"/>
<path d="{path(es, ex, ey)}" fill="none" stroke="{GOLD}" stroke-width="3"
      stroke-opacity="0.60" stroke-linejoin="round"/>'''
open("2-emblem.svg", "w").write(svg(body))

# ----------------------------------------------------------------- 3: rings
# Concentric hairlines off a centre near the right edge, so the arcs read as
# one sweep across the frame rather than as a target sitting in the middle.
cx, cy = 3260, 1010
GR = 150 + 5 * 205
rings = []
for i in range(1, 15):
    r = 150 + i * 205
    rings.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{STEEL}" '
                 f'stroke-width="1.5" opacity="{max(0.04, 0.22 - i*0.013):.3f}"/>')
ticks = []
for deg in range(0, 360, 15):
    a = math.radians(deg)
    inner, outer = (GR - 22, GR + 22) if deg % 45 == 0 else (GR - 10, GR + 10)
    ticks.append(f'<line x1="{cx+math.cos(a)*inner:.0f}" y1="{cy+math.sin(a)*inner:.0f}" '
                 f'x2="{cx+math.cos(a)*outer:.0f}" y2="{cy+math.sin(a)*outer:.0f}" '
                 f'stroke="{GOLD}" stroke-width="2" opacity="0.42"/>')
rings.insert(4, f'<circle cx="{cx}" cy="{cy}" r="{GR}" fill="none" stroke="{GOLD}" '
                f'stroke-width="2" opacity="0.50"/>' + "".join(ticks))
body = "".join(rings) + emblem(cx, cy, 0.40, 0.85, 2.6, fill_op=0.09)
open("3-rings.svg", "w").write(svg(body))
print("1 2 3")
