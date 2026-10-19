"""Exercise failed-login feedback and installer rollback without authenticating."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


class LoginTest(unittest.TestCase):
    def test_failed_login_stays_visible_until_typing_resumes(self):
        try:
            from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl
            from PySide6.QtGui import QGuiApplication
            from PySide6.QtQml import QQmlEngine, QQmlComponent
        except ImportError:
            self.skipTest('requires PySide6')
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        app = QGuiApplication.instance() or QGuiApplication([])

        class User(QObject):
            lastUser = Property(str, lambda self: 'test', constant=True)

        class Sessions(QObject):
            lastIndex = Property(int, lambda self: 0, constant=True)

            @Slot(result=int)
            def rowCount(self):
                return 0

        class Sddm(QObject):
            loginFailed = Signal()
            loginSucceeded = Signal()

        engine = QQmlEngine()
        user, sessions, sddm = User(), Sessions(), Sddm()
        for name, value in [('userModel', user), ('sessionModel', sessions), ('sddm', sddm)]:
            engine.rootContext().setContextProperty(name, value)
        from login import build
        with tempfile.TemporaryDirectory() as scratch:
            stage = Path(scratch)
            build(stage)
            self.assertIn('fill="#283943"', (stage/'logo.svg').read_text())
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(stage/'Main.qml')))
            root = component.create()
            self.assertIsNotNone(root, str(component.errors()))
            password = next(child for child in root.findChildren(QObject)
                            if child.inherits('QQuickTextInput'))
            password.setProperty('text', 'wrong password')
            sddm.loginFailed.emit()
            app.processEvents()
            self.assertEqual(password.property('text'), '')
            self.assertTrue(root.property('loginFailed'))
            password.setProperty('text', 'retry')
            self.assertFalse(root.property('loginFailed'))
            root.deleteLater()
            app.processEvents()

    @unittest.skipUnless(shutil.which('bwrap'), 'requires bubblewrap')
    def test_install_and_failed_publish_restore_existing_target(self):
        for previous in ('directory', 'file'):
            for fail in (False, True):
                with self.subTest(previous=previous, fail=fail), tempfile.TemporaryDirectory(dir=ROOT) as scratch:
                    work = Path(scratch)
                    for name in ('themes', 'config', 'var', 'tmp', 'bin'):
                        (work/name).mkdir()
                    target = work/'themes/dark-knight'
                    if previous == 'directory':
                        target.mkdir()
                        (target/'previous').write_text('old theme')
                    else:
                        target.write_text('old file')
                    config = work/'config/zz-dark-knight.conf'
                    config.write_text('[Theme]\nCurrent=previous\n')
                    (work/'bin/pkexec').write_text('#!/bin/sh\nexec "$@"\n')
                    (work/'bin/mv').write_text('''#!/bin/bash
if [[ $DK_TEST_FAIL == yes && $1 == /usr/local/share/sddm/themes/.dark-knight.* && $2 == /usr/local/share/sddm/themes/dark-knight ]]; then exit 1; fi
exec /usr/bin/mv "$@"
''')
                    for command in (work/'bin').iterdir():
                        command.chmod(0o755)
                    args = ['bwrap', '--ro-bind', '/', '/', '--dev', '/dev', '--unshare-user',
                            '--uid', '0', '--gid', '0', '--unshare-net']
                    for source, destination in [('themes', '/usr/local/share/sddm/themes'),
                                                ('config', '/etc/sddm.conf.d'), ('var', '/var/tmp'), ('tmp', '/tmp')]:
                        args += ['--bind', str(work/source), destination]
                    result = subprocess.run(args+['bash', str(ROOT/'src/install-login.sh')],
                                            env={**os.environ, 'PATH': f'{work}/bin:/usr/bin',
                                                 'DK_TEST_FAIL': 'yes' if fail else 'no'},
                                            capture_output=True, text=True)
                    if fail:
                        self.assertNotEqual(result.returncode, 0)
                        old = target/'previous' if previous == 'directory' else target
                        self.assertEqual(old.read_text(), 'old theme' if previous == 'directory' else 'old file')
                        self.assertEqual(config.read_text(), '[Theme]\nCurrent=previous\n')
                    else:
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertTrue((target/'Main.qml').is_file())
                        self.assertIn('Current=dark-knight', config.read_text())
