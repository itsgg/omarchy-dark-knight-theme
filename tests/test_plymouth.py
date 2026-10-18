"""Validate invisible icon assets and exercise privileged installation in a namespace."""
from pathlib import Path
import os
from itertools import product
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from plymouth import build


@unittest.skipUnless(shutil.which('magick') and Path('/usr/share/omarchy/default/plymouth').is_dir(),
                     'requires ImageMagick and installed Omarchy assets')
class PlymouthTest(unittest.TestCase):
    def test_build_keeps_dialogue_and_hides_only_icon(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as scratch:
            stage = Path(scratch)/'theme'
            build(stage, 'gotham')
            alpha = subprocess.check_output(['magick', str(stage/'lock.png'), '-alpha', 'extract',
                                             '-format', '%[fx:maxima]', 'info:'], text=True)
            self.assertEqual(float(alpha), 0)
            vendor_lock = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'))/'default/plymouth/lock.png'
            dimensions = lambda path: subprocess.check_output(['magick', 'identify', '-format', '%wx%h', str(path)])
            self.assertEqual(dimensions(stage/'lock.png'), dimensions(vendor_lock))
            original = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy'))/'default/plymouth/omarchy.script'
            def dialogue(text):
                return '\n'.join(line for line in text.splitlines() if not line.startswith('Window.SetBackground'))
            self.assertEqual(dialogue(original.read_text()), dialogue((stage/'omarchy.script').read_text()))
            self.assertEqual((stage/'logo.png').read_bytes(), (ROOT/'unlock.png').read_bytes())
            self.assertIn('ImageDir=/usr/share/plymouth/themes/dark-knight',
                          (stage/'dark-knight.plymouth').read_text())

    @unittest.skipUnless(shutil.which('bwrap'), 'requires bubblewrap')
    def test_install_and_failed_rebuild_rollback(self):
        for bootloader, fail in product(('limine', 'mkinitcpio'), ('none', 'rebuild', 'publish')):
            with self.subTest(bootloader=bootloader, fail=fail), tempfile.TemporaryDirectory(dir=ROOT) as scratch:
                root = Path(scratch)
                for name in ('themes/dark-knight', 'config', 'var', 'tmp', 'bin'):
                    (root/name).mkdir(parents=True)
                sentinel = root/'themes/dark-knight/previous'
                sentinel.write_text('previous theme')
                config = root/'config/plymouthd.conf'
                config.write_text('[Daemon]\nTheme=omarchy\n')
                (root/'bin/pkexec').write_text('#!/bin/sh\nexec "$@"\n')
                (root/'bin/plymouth-set-default-theme').write_text('''#!/bin/bash
if (( $# == 0 )); then echo omarchy; exit 0; fi
printf '[Daemon]\\nTheme=%s\\n' "$1" > /etc/plymouth/plymouthd.conf
''')
                (root/'bin/mv').write_text('''#!/bin/bash
if [[ $DK_TEST_FAIL == publish && $1 == /usr/share/plymouth/themes/.dark-knight.* && $2 == /usr/share/plymouth/themes/dark-knight ]]; then exit 1; fi
exec /usr/bin/mv "$@"
''')
                rebuild = """#!/bin/bash
printf '%s %s\\n' "${0##*/}" "$*" >> /var/tmp/rebuild.log
if [[ $DK_TEST_FAIL == rebuild ]] && grep -q 'Theme=dark-knight' /etc/plymouth/plymouthd.conf; then exit 1; fi
"""
                (root/'bin/mkinitcpio').write_text(rebuild)
                if bootloader == 'limine':
                    (root/'bin/limine-mkinitcpio').write_text(rebuild)
                for name in ('dirname', 'mktemp', 'rm', 'python3', 'magick', 'cp', 'chmod', 'install', 'grep'):
                    (root/'bin'/name).symlink_to(shutil.which(name))
                for command in (root/'bin').iterdir():
                    if not command.is_symlink():
                        command.chmod(0o755)
                args = [shutil.which('bwrap'), '--ro-bind', '/', '/', '--dev', '/dev', '--unshare-user',
                        '--uid', '0', '--gid', '0', '--unshare-net']
                for source, destination in [('themes', '/usr/share/plymouth/themes'),
                                            ('config', '/etc/plymouth'), ('var', '/var/tmp'), ('tmp', '/tmp')]:
                    args += ['--bind', str(root/source), destination]
                env = {**os.environ, 'PATH': f'{root}/bin', 'DK_TEST_FAIL': fail}
                result = subprocess.run(args+['/bin/bash', str(ROOT/'src/install-splash.sh'), 'gotham'],
                                        env=env, capture_output=True, text=True)
                if fail != 'none':
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f'Plymouth {fail} failed', result.stderr)
                    self.assertEqual(sentinel.read_text(), 'previous theme')
                    self.assertEqual(config.read_text(), '[Daemon]\nTheme=omarchy\n')
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(sentinel.exists())
                    self.assertIn('Theme=dark-knight', config.read_text())
                    self.assertTrue((root/'themes/dark-knight/lock.png').is_file())
                log = root/'var/rebuild.log'
                if fail == 'publish':
                    self.assertFalse(log.exists())
                else:
                    expected = 'limine-mkinitcpio ' if bootloader == 'limine' else 'mkinitcpio -P'
                    self.assertEqual(log.read_text().splitlines(), [expected] * (2 if fail == 'rebuild' else 1))
