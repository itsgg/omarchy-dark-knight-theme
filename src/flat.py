"""The Dark Knight wallpaper: one, flat, and quiet.

The emblem centred where two accent axes cross, on a steel hairline grid that
runs out into the ground through a mask. It is the boot screen at full size:
unlock.py cuts the same origin out for Plymouth, so the machine boots into the
picture the desktop then wears.

No blur filters, no raster blocks and no gradient fills: every edge is a real
vector edge on a flat ground. The one soft thing is the grid, whose lines fade
out through a mask; a fade on a hairline cannot band. A wallpaper competes
with the windows for the same attention and loses if it tries to be the
subject, so this is built to sit behind a terminal all day.

Quiet is not invisible. The hairlines are strong enough to be seen on a real
panel, which on a ground at 6% lightness is still far below a window's text.
"""
import sys, pathlib, tomllib
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

# No vignette. There was one, a radial gradient from the ground down to the
# darkest ground at the corners, and it could not be made smooth: across half
# the frame it spans about 48 grey levels, so each level is a flat ring 40 to
# 200 pixels wide, which is concentric banding on any 8-bit panel. The render
# dithered it with noise and then saved a JPEG, which smooths noise away, so
# the rings came back. A flat ground has nothing to band, needs no dither, and
# is the same decision the rest of the theme already made.
def write(name, text):
    """Whole or not at all: written beside the target and renamed over it, so a
    render that dies half way leaves the last good SVG where it was."""
    scratch = pathlib.Path(name + ".tmp")
    scratch.write_text(text)
    scratch.replace(name)


def svg(body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}"><defs>{defs}</defs>'
            f'<rect width="{W}" height="{H}" fill="{INK}"/>{body}</svg>')

def grid(name, tile, ox, oy, width, opacity):
    """A hairline grid as an SVG pattern, with a line exactly through (ox, oy).

    The lines run through the middle of the tile, not along its edge. Along
    the edge is the obvious way to write it and half of every stroke falls
    outside the tile, where a pattern clips it: the grid came out at half its
    weight and a fraction of a pixel to one side of the axes it was meant to
    sit under. The opacities passed here are half what they were, so the look
    is the one that was chosen and the geometry is now the one intended.
    """
    h = tile / 2
    return (f'<pattern id="{name}" x="{(ox - h) % tile}" y="{(oy - h) % tile}" '
            f'width="{tile}" height="{tile}" patternUnits="userSpaceOnUse">'
            f'<path d="M{h} 0V{tile}M0 {h}H{tile}" fill="none" stroke="{STEEL}" '
            f'stroke-width="{width}" opacity="{opacity}"/></pattern>')


def emblem(cx, cy, scale, stroke_op, width=3.2, fill_op=0.0):
    out = ""
    if fill_op:
        # Solid first, so the axes stop at the mark instead of running through
        # it, then the accent tint over that.
        out += f'<path d="{path(scale, cx, cy)}" fill="{INK8}"/>'
        out += f'<path d="{path(scale, cx, cy)}" fill="{ACCENT}" opacity="{fill_op}"/>'
    return out + (f'<path d="{path(scale, cx, cy)}" fill="none" stroke="{ACCENT}" '
                  f'stroke-width="{width}" stroke-opacity="{stroke_op}" '
                  f'stroke-linejoin="round"/>')

# ------------------------------------------------------------------ origin
# The mask is the one gradient here and it is on the lines, not on a fill. The
# origin is the centre of the frame, and grid() puts a coarse line through it
# exactly.
CX, CY = W // 2, H // 2
defs = grid("fine", 60, CX, CY, 1, 0.12) + grid("coarse", 300, CX, CY, 1.5, 0.23) + f'''
<radialGradient id="fade" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="1850">
  <stop offset="0%"   stop-color="#fff" stop-opacity="1"/>
  <stop offset="55%"  stop-color="#fff" stop-opacity="0.85"/>
  <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
</radialGradient>
<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>'''
body = f'''
<g mask="url(#m)">
<rect width="{W}" height="{H}" fill="url(#fine)"/>
<rect width="{W}" height="{H}" fill="url(#coarse)"/>
<rect x="0" y="{CY - 1}" width="{W}" height="2" fill="{ACCENT}" opacity="0.42"/>
<rect x="{CX - 1}" y="0" width="2" height="{H}" fill="{ACCENT}" opacity="0.42"/>
</g>
{emblem(CX, CY, 0.62, 0.85, 3.0, fill_op=0.08)}'''
write("1-origin.svg", svg(body, defs))
print("1-origin")
