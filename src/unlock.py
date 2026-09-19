#!/usr/bin/env python3
"""Emit the SVG for unlock.png: the wallpaper's origin, cut out of it.

    python3 src/unlock.py > unlock.svg

unlock.png is what Plymouth draws at boot and over the disk-unlock prompt. It
paints the ground itself, from colors.toml, centres this image unscaled, and
puts the password field 40px under its bottom edge. So the image is the
wallpaper's own vocabulary on a transparent ground: the hairline grid, the two
accent axes, and the emblem where they cross, at the wallpaper's proportions.
The boot screen and the desktop are then the same picture, and logging in
reads as the grid filling out to the edges.

The grid fades out toward the edge of the image through a mask. Without it the
patch ends in a hard rectangle and reads as a panel sitting on the screen; with
it the lines run out into the ground. It is the one gradient here and it is on
the lines, not on a fill.

The size is a budget, not a preference: anything taller pushes the password
field off a 1080 panel.
"""
import pathlib
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bat import path

W, H = 1320, 480
CX, CY = W / 2, H / 2
p = tomllib.load(open(pathlib.Path(__file__).resolve().parent.parent / "colors.toml", "rb"))
steel, accent, raised = p["muted"], p["accent"], p["lighter_background"]
d = path(0.30, CX, CY)
w = sys.stdout.write
def grid(name, tile, width, opacity):
    """Lines through the middle of the tile, so a pattern does not clip half of
    each stroke, offset so one of them runs exactly through the origin. The
    same construction as flat.py's, at half its scale."""
    h = tile / 2
    return (f'<pattern id="{name}" x="{(CX - h) % tile}" y="{(CY - h) % tile}" '
            f'width="{tile}" height="{tile}" patternUnits="userSpaceOnUse">'
            f'<path d="M{h} 0V{tile}M0 {h}H{tile}" fill="none" stroke="{steel}" '
            f'stroke-width="{width}" opacity="{opacity}"/></pattern>')


w(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>'
  + grid("fine", 30, 1, 0.12) + grid("coarse", 150, 1.25, 0.23) +
  '<radialGradient id="fade" cx="0.5" cy="0.5" r="0.5">'
  '<stop offset="0%" stop-color="#fff" stop-opacity="1"/>'
  '<stop offset="55%" stop-color="#fff" stop-opacity="0.75"/>'
  '<stop offset="100%" stop-color="#fff" stop-opacity="0"/></radialGradient>'
  f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>'
  '<g mask="url(#m)">'
  f'<rect width="{W}" height="{H}" fill="url(#fine)"/><rect width="{W}" height="{H}" fill="url(#coarse)"/>'
  f'<rect x="0" y="{CY - 0.75}" width="{W}" height="1.5" fill="{accent}" opacity="0.42"/>'
  f'<rect x="{CX - 0.75}" y="0" width="1.5" height="{H}" fill="{accent}" opacity="0.42"/></g>'
  f'<path d="{d}" fill="{raised}"/>'
  f'<path d="{d}" fill="{accent}" opacity="0.08"/>'
  f'<path d="{d}" fill="none" stroke="{accent}" stroke-width="1.8" stroke-opacity="0.85" stroke-linejoin="round"/></svg>')
