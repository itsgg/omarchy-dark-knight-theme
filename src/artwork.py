#!/usr/bin/env python3
"""Compose Gotham and Cape wallpapers with matching transparent splash artwork.

python3 src/artwork.py
Python defines the compositions; SVGs are editable exports, replaced on render.
All artwork uses editable solid vector shapes, with no embedded raster images.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

from bat import path
from scenes import city
from plymouth import preview as preview_plymouth

ROOT = Path(__file__).resolve().parent.parent
P = tomllib.loads((ROOT / 'colors.toml').read_text())
BG = P['background']
OUT = ROOT / 'assets/artwork'


def svg(width, height, body, defs='', wallpaper=False):
    view_height = 1920*height/width if wallpaper else 480
    ground = f'<rect width="1920" height="{view_height:g}" fill="{BG}"/>' if wallpaper else ''
    view = f'0 0 1920 {view_height:g}' if wallpaper else '0 0 1320 480'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="{view}"><defs>{defs}</defs>{ground}{body}</svg>')


def signal(cx, cy, radius):
    return (f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{P['line']}"/>'
            f'<path d="{path(radius * 1.55 / 1000, cx, cy)}" fill="{BG}"/>')


def vector_scene(style, width, height):
    portrait = height > width
    if style == 'gotham':
        cx = width*(.64 if portrait else .67)
        cy = height*(.51 if portrait else .34)
        radius = width*(.18 if portrait else .08)
        body = (f'<path d="M{width*.7:g} {height*.87:g}'
                f'L{cx-radius*.8:g} {cy:g}L{cx+radius*.8:g} {cy:g}Z" fill="#12212A"/>')
        body += signal(cx, cy, radius)
        body += city(width, height, 1.7 if portrait else 1.05)
    else:
        scale = width*(.0007 if portrait else .00048)
        # Exact cubic extrema place the emblem box centre 1.71052865 below its origin.
        body = f'<path d="{path(scale, width/2, height/2 - 1.71052865*scale)}" fill="{P["line"]}"/>'
    return body


def splash():
    return svg(1320, 480, f'<path d="{path(.44, 660, 240)}" fill="{P["muted"]}"/>')


def gotham(wallpaper):
    return svg(5120, 3200, vector_scene('gotham', 1920, 1200), wallpaper=True) if wallpaper else splash()


def cape(wallpaper):
    return svg(5120, 3200, vector_scene('cape', 1920, 1200), wallpaper=True) if wallpaper else splash()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.artwork-', dir=ROOT) as scratch:
        work = Path(scratch)
        viewer = work / 'imv'
        viewer.write_text('#!/bin/sh\nexit 0\n')
        viewer.chmod(0o755)
        env = {**os.environ, 'PATH': f"{work}:{os.environ['PATH']}"}
        for name, draw, wallpaper, logo, preview in (
            ('gotham', gotham, '1-gotham.png', 'unlock.png', 'preview-unlock.png'),
            ('cape', cape, '2-cape.png', 'unlock-cape.png', 'preview-unlock-cape.png'),
        ):
            for is_wallpaper, target in ((True, ROOT/'backgrounds'/wallpaper), (False, ROOT/logo)):
                source = work/'source.svg'
                source.write_text(draw(is_wallpaper))
                run = subprocess.run
                run(['rsvg-convert', str(source), '-o', str(work/'raw.png')], check=True)
                run(['magick', str(work/'raw.png'), '-depth', '8', '-strip', '-define',
                     'png:exclude-chunks=date,time', str(work/'final.png')], check=True)
                (work/'final.png').replace(target)
                source.replace(OUT/f'{name}-{"wallpaper" if is_wallpaper else "splash"}.svg')
                print(target.relative_to(ROOT))
            if shutil.which('omarchy-plymouth-preview'):
                preview_plymouth(ROOT/preview, name)
                print(preview)
            else:
                print(f'{preview} skipped: omarchy-plymouth-preview unavailable')


if __name__ == '__main__':
    main()
