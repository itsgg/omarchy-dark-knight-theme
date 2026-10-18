#!/usr/bin/env python3
"""Draw two flat vector wallpapers and matching transparent splash artwork.

python3 src/artwork.py
Python defines the compositions; SVGs are editable exports, replaced on render.
No generated bitmaps, texture, gradient or filter.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

from bat import path
from plymouth import build as build_plymouth

ROOT = Path(__file__).resolve().parent.parent
P = tomllib.loads((ROOT / 'colors.toml').read_text())
BG = P['background']
OUT = ROOT / 'assets/artwork'


def svg(width, height, body, defs='', wallpaper=False):
    ground = f'<rect width="1920" height="1200" fill="{BG}"/>' if wallpaper else ''
    view = '0 0 1920 1200' if wallpaper else '0 0 1320 480'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="{view}"><defs>{defs}</defs>{ground}{body}</svg>')


def signal(cx, cy, radius):
    return (f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{P['line']}"/>'
            f'<path d="{path(radius * 1.55 / 1000, cx, cy)}" fill="{BG}"/>')


def skyline(buildings, base, bottom, colour):
    points = [(0, bottom), (0, base)]
    for x, width, height in buildings:
        points.extend(((x, base), (x, base-height),
                       (x+width, base-height), (x+width, base)))
    points.extend(((1920, base), (1920, bottom)))
    return '<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="{colour}"/>'


def gotham(wallpaper):
    if not wallpaper:
        return svg(1320, 480, signal(660, 240, 156))
    # Contiguous clusters and open gaps give the city a skyline, rather than
    # the regular rhythm of an equalizer. Two stepped crowns carry the identity.
    back = [(0, 140, 130), (140, 60, 185), (200, 95, 150), (340, 80, 300),
            (420, 110, 185), (530, 80, 160), (710, 150, 190), (860, 75, 135),
            (1020, 100, 220), (1120, 45, 190), (1370, 110, 280),
            (1480, 60, 220), (1700, 130, 165), (1830, 90, 190)]
    front = [(0, 210, 95), (255, 165, 145), (475, 245, 115),
             (765, 140, 165), (960, 220, 100), (1230, 180, 140),
             (1460, 215, 110), (1730, 190, 150)]
    body = '<path d="M1410 1030L1090 390L1410 390Z" fill="#12212A"/>'
    body += signal(1260, 430, 180)
    body += skyline(back, 1040, 1200, '#16242D')
    body += ('<path d="M350 740V718H365V696H376V670H384V696H395V718H410V740Z" fill="#16242D"/>'
             '<path d="M1385 760V740H1401V716H1420V690H1428V716H1447V740H1465V760Z" fill="#16242D"/>')
    body += skyline(front, 1130, 1200, '#0E181F')
    return svg(3840, 2400, body, wallpaper=True)


def cape_emblem(cx, cy, scale):
    return f'<path d="{path(scale, cx, cy)}" fill="{P["line"]}"/>'


def cape(wallpaper):
    if not wallpaper:
        return svg(1320, 480, cape_emblem(660, 240, .44))
    # Two equally coloured planes suggest the cape without simulating folds.
    body = ('<path d="M0 1200V895L600 550L790 1200Z" fill="#111E27"/>'
            '<path d="M1920 1200V895L1320 550L1130 1200Z" fill="#111E27"/>')
    body += cape_emblem(960, 540, .88)
    return svg(3840, 2400, body, wallpaper=True)


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
                preview_root = work/name
                build_plymouth(preview_root/'default/plymouth', name)
                subprocess.run(['omarchy-plymouth-preview', BG, P['foreground'], str(ROOT/logo),
                                str(work/'preview.png')], check=True,
                               env={**env, 'OMARCHY_PATH': str(preview_root)})
                subprocess.run(['magick', str(work/'preview.png'), '-depth', '8', '-strip',
                                '-define', 'png:exclude-chunks=date,time', str(work/'final.png')], check=True)
                (work/'final.png').replace(ROOT/preview)
                print(preview)
            else:
                print(f'{preview} skipped: omarchy-plymouth-preview unavailable')


if __name__ == '__main__':
    main()
