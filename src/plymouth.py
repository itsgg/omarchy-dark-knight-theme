#!/usr/bin/env python3
"""Build Dark Knight's Plymouth assets with centred masked-password layout."""
import os
import base64
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent

ORIGINAL_BULLET_LAYOUT = '''      bullet.x = entry.x + 20 + index * (7 + 5);
      bullet.y = entry.y + entry.image.GetHeight() / 2 - 3.5;
      bullet.sprites[index].SetPosition(bullet.x, bullet.y, 10002);
    }

    bullet.sprites[index].SetOpacity(1);'''
CENTERED_BULLET_LAYOUT = '''    }

    # Reposition every sprite as the masked password grows or shrinks.
    bullet.x = entry.x + (entry.image.GetWidth() - (bullets_to_show * 12 - 5)) / 2 + index * 12;
    bullet.y = entry.y + entry.image.GetHeight() / 2 - 3.5;
    bullet.sprites[index].SetPosition(bullet.x, bullet.y, 10002);
    bullet.sprites[index].SetOpacity(1);'''


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
    script = '\n'.join(lines)+'\n'
    if script.count(ORIGINAL_BULLET_LAYOUT) != 1:
        raise ValueError('Plymouth bullet layout changed; inspect the vendor script before building')
    (destination/'omarchy.script').write_text(script.replace(ORIGINAL_BULLET_LAYOUT, CENTERED_BULLET_LAYOUT))
    definition = (source/'omarchy.plymouth').read_text()
    definition = definition.replace('Name=Omarchy', 'Name=Dark Knight')
    definition = definition.replace('Description=Omarchy splash screen.', 'Description=Dark Knight splash without a lock icon.')
    definition = definition.replace('/usr/share/plymouth/themes/omarchy', '/usr/share/plymouth/themes/dark-knight')
    definition = definition.replace('ConsoleLogBackgroundColor=0x1a1b26', f'ConsoleLogBackgroundColor=0x{palette["background"][1:]}')
    (destination/'dark-knight.plymouth').write_text(definition)


def preview(target, variation):
    """Render the actual assets with the same centered bullet geometry."""
    import tempfile
    palette = tomllib.loads((ROOT/'colors.toml').read_text())
    with tempfile.TemporaryDirectory(prefix='.splash-preview-', dir=ROOT) as scratch:
        work = Path(scratch)
        build(work, variation)
        def image(name, x, y, width, height):
            data = base64.b64encode((work/name).read_bytes()).decode('ascii')
            return (f'<image x="{x:g}" y="{y:g}" width="{width}" height="{height}" '
                    f'href="data:image/png;base64,{data}"/>')
        # The vendor script centers the 1320x480 logo then places entry below it.
        body = image('logo.png', 300, 300, 1320, 480)
        body += image('entry.png', 817, 820, 286, 48)
        for index in range(4):
            body += image('bullet.png', 960-43/2+index*12, 844-3.5, 7, 7)
        source = work/'preview.svg'
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">'
                          f'<rect width="1920" height="1080" fill="{palette["background"]}"/>'
                          f'{body}</svg>')
        rendered = work/'preview.png'
        subprocess.run(['rsvg-convert', str(source), '-o', str(rendered)], check=True)
        rendered.replace(target)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python3 src/plymouth.py <output-directory> <gotham|cape>')
    build(Path(sys.argv[1]), sys.argv[2])
