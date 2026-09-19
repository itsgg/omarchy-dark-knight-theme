"""The Dark Knight wallpapers: two, flat, and quiet.

One vocabulary, twice. The first is a steel hairline grid, two accent axes
crossing on thirds, and the emblem at the origin at a size where it is a mark
on the grid rather than the subject. The second is that origin centred, with
the grid running out into the ground: the boot screen at full size.
No blur filters, no raster blocks and no gradient fills: every edge is a real
vector edge on a flat ground. The one soft thing is the second wallpaper's
grid, whose lines fade out through a mask; a fade on a hairline cannot band.

There were four. A skyline with a searchlight, the emblem large, and a field
of rings came and went on 2026-09-19, and before them two photographs. The grid
is what was kept, because it is the one that is the theme: a ground, a
line, one hue, and nothing asking to be looked at while there is work in front
of it. A wallpaper competes with the windows for the same attention and loses
if it tries to be the subject.

Quiet is not invisible. The first render put its hairlines at 0.16 to 0.32 and
at full size on a real panel the grid was not there at all, so every mark is
about half again stronger than that, which on a ground at 6% lightness is
still far below a window's text.
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

# ------------------------------------------------------------------ 1: grid
# The origin sits on thirds, not dead centre. The emblem replaces the origin
# dot at a size where it still reads as a mark on the grid, not as the subject.
OX, OY = 1500, 1500
defs = grid("fine", 60, OX, OY, 1, 0.12) + grid("coarse", 300, OX, OY, 1.5, 0.23)
body = f'''
<rect width="{W}" height="{H}" fill="url(#fine)"/>
<rect width="{W}" height="{H}" fill="url(#coarse)"/>
<rect x="0" y="{OY - 1}" width="{W}" height="2" fill="{ACCENT}" opacity="0.42"/>
<rect x="{OX - 1}" y="0" width="2" height="{H}" fill="{ACCENT}" opacity="0.42"/>
{emblem(OX, OY, 0.50, 0.80, 2.8, fill_op=0.08)}'''
write("1-grid.svg", svg(body, defs))


# --------------------------------------------------------------- 2: origin
# The boot screen, as a wallpaper. unlock.py cuts the grid's origin out for
# Plymouth: the emblem centred where the axes cross, the grid running out into
# the ground through a mask. It was made to be a logo and turned out to be the
# better picture of the two, so here it is at full size, and with it the
# desktop is the same image the machine booted into.
#
# The mask is the one gradient in the set and it is on the lines, not on a
# fill. The origin is the centre of the frame, and grid() puts a coarse line
# through it exactly.
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
write("2-origin.svg", svg(body, defs))
print("1-grid 2-origin")
