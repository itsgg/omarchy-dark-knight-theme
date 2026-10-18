#!/usr/bin/env python3
"""Build Dark Knight's Plymouth assets using Omarchy's unchanged dialogue script."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent


def build(destination, variation):
    if variation not in ('gotham', 'cape'):
        raise ValueError('variation must be gotham or cape')
    source = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'default/plymouth'
    palette = tomllib.loads((ROOT / 'colors.toml').read_text())
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('omarchy.script', 'bullet.png', 'entry.png', 'progress_bar.png', 'progress_box.png'):
        shutil.copyfile(source / name, destination / name)
    logo = ROOT / ('unlock.png' if variation == 'gotham' else 'unlock-cape.png')
    shutil.copyfile(logo, destination / 'logo.png')
    for name in ('bullet.png', 'entry.png', 'progress_bar.png'):
        subprocess.run(['magick', str(destination/name), '-channel', 'RGB', '+level-colors',
                        f'{palette["foreground"]},{palette["foreground"]}', str(destination/name)], check=True)
    # Keep the vendor script's positioning and password callbacks intact.
    # A transparent lock has the original dimensions and contributes no pixels.
    subprocess.run(['magick', '-size', '84x96', 'xc:none', '-strip',
                    str(destination/'lock.png')], check=True)
    colour = ', '.join(f'{int(palette["background"][i:i+2], 16)/255:.3f}' for i in (1, 3, 5))
    script = (destination/'omarchy.script').read_text()
    lines = script.splitlines()
    for index, line in enumerate(lines):
        for setting in ('Top', 'Bottom'):
            if line.startswith(f'Window.SetBackground{setting}Color('):
                lines[index] = f'Window.SetBackground{setting}Color({colour});'
    (destination/'omarchy.script').write_text('\n'.join(lines)+'\n')
    definition = (source/'omarchy.plymouth').read_text()
    definition = definition.replace('Name=Omarchy', 'Name=Dark Knight')
    definition = definition.replace('Description=Omarchy splash screen.', 'Description=Dark Knight splash without a lock icon.')
    definition = definition.replace('/usr/share/plymouth/themes/omarchy', '/usr/share/plymouth/themes/dark-knight')
    definition = definition.replace('ConsoleLogBackgroundColor=0x1a1b26', f'ConsoleLogBackgroundColor=0x{palette["background"][1:]}')
    (destination/'dark-knight.plymouth').write_text(definition)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python3 src/plymouth.py <output-directory> <gotham|cape>')
    build(Path(sys.argv[1]), sys.argv[2])
