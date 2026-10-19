#!/usr/bin/env python3
"""Recompose the flat Gotham and Cape artwork for phones and tablets."""
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from artwork import ROOT, BG, vector_scene

PROFILES = (
    ('iphone', 'portrait', 1440, 3120),
    ('android', 'portrait', 1440, 3200),
    ('ipad', 'portrait', 3072, 4096),
    ('ipad', 'landscape', 4096, 3072),
)
SOURCES = ROOT / 'assets/artwork/mobile'
OUTPUT = ROOT / 'wallpapers'


def composition(style, width, height):
    h = height/width*1000
    body = f'<rect width="1000" height="{h:g}" fill="{BG}"/>'
    body += vector_scene(style, 1000, h)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 1000 {h:g}">{body}</svg>')


def main():
    SOURCES.mkdir(parents=True, exist_ok=True)
    outputs = []
    with tempfile.TemporaryDirectory(prefix='.mobile-', dir=ROOT) as scratch:
        work = Path(scratch)
        for device, orientation, width, height in PROFILES:
            folder = OUTPUT/device
            folder.mkdir(parents=True, exist_ok=True)
            for style in ('gotham', 'cape'):
                suffix = f'-{orientation}' if device == 'ipad' else ''
                target = folder/f'{style}{suffix}.png'
                source_name = f'{device}-{style}{suffix}.svg'
                source = work/'source.svg'
                source.write_text(composition(style, width, height))
                subprocess.run(['rsvg-convert', str(source), '-o', str(work/'raw.png')], check=True)
                subprocess.run(['magick', str(work/'raw.png'), '-depth', '8', '-strip',
                                '-define', 'png:exclude-chunks=date,time', str(work/'final.png')], check=True)
                (work/'final.png').replace(target)
                source.replace(SOURCES/source_name)
                outputs.append(target)
                print(target.relative_to(ROOT))

        # A labelled contact sheet, kept separate from the wallpaper files.
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="1420" viewBox="0 0 1240 1420">',
                 f'<rect width="1240" height="1420" fill="{BG}"/>',
                 '<g font-family="sans-serif" fill="#CCCFD1">',
                 '<text x="35" y="42" font-size="24">Dark Knight: phone and tablet wallpapers</text>']
        for row, style in enumerate(('gotham', 'cape')):
            top = 102+row*650
            parts.append(f'<text x="35" y="{top-12}" font-size="19">{style.title()}</text>')
            for col, (device, orientation, width, height) in enumerate(PROFILES):
                suffix = f'-{orientation}' if device == 'ipad' else ''
                x, w = 35+col*300, 260
                image_h = w*height/width
                parts.append(f'<image href="{device}-{style}{suffix}.svg" x="{x}" y="{top}" width="{w}" height="{image_h:g}"/>')
                device_label = {'iphone': 'iPhone', 'android': 'Android', 'ipad': 'iPad'}[device]
                label = f'{device_label} {orientation if device == "ipad" else ""}'.strip()
                parts.append(f'<text x="{x}" y="{top+image_h+24:g}" font-size="14">{label} ({width}x{height})</text>')
        parts.extend(['</g>', '</svg>'])
        sheet = SOURCES/'preview.svg'
        sheet.write_text(''.join(parts))
        subprocess.run(['rsvg-convert', str(sheet), '-o', str(work/'preview.png')], check=True)
        subprocess.run(['magick', str(work/'preview.png'), '-strip', '-define',
                        'png:exclude-chunks=date,time', str(work/'final.png')], check=True)
        (work/'final.png').replace(OUTPUT/'preview.png')

        with ZipFile(work/'dark-knight-mobile.zip', 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for target in sorted(outputs):
                info = ZipInfo(str(target.relative_to(OUTPUT)))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, target.read_bytes())
        (work/'dark-knight-mobile.zip').replace(OUTPUT/'dark-knight-mobile.zip')


if __name__ == '__main__':
    main()

