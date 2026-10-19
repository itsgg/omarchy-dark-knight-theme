#!/usr/bin/env python3
"""Build the SDDM artwork and layout without starting an authentication session."""
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

from bat import path

ROOT = Path(__file__).resolve().parent.parent


def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    palette = tomllib.loads((ROOT/'colors.toml').read_text())
    source = Path('/usr/share/sddm/themes/omarchy')
    shutil.copy2(ROOT/'assets/login/Main.qml', destination/'Main.qml')
    for name in ('entry.png', 'entry-failed.png', 'bullet.png', 'lock.png', 'lock-failed.png'):
        shutil.copy2(source/name, destination/name)
        colour = palette['red'] if 'failed' in name else palette['foreground']
        subprocess.run(['magick', str(destination/name), '-channel', 'RGB',
                        '+level-colors', f'{colour},{colour}', str(destination/name)], check=True)
    logo = (f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="220" '
            f'viewBox="0 0 600 220"><path d="{path(.44, 300, 110)}" '
            f'fill="{palette["line"]}"/></svg>')
    (destination/'logo.svg').write_text(logo)
    subprocess.run(['rsvg-convert', str(destination/'logo.svg'), '-o', str(destination/'logo.png')], check=True)
    (destination/'theme.conf').write_text('[General]\n')
    (destination/'metadata.desktop').write_text(
        '[SddmGreeterTheme]\nName=Dark Knight\nDescription=Dark Knight login\n'
        'Type=sddm-theme\nVersion=1.0\nQtVersion=6\n')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 src/login.py <output-directory>')
    build(Path(sys.argv[1]))
