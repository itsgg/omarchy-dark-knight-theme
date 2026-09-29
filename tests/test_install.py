"""Run with python3 -m unittest discover -s tests. Requires bubblewrap.

Bind a disposable directory over the home path in a mount namespace so the
installer uses its real paths without touching the user's configuration.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOME_PATH = Path.home()


@unittest.skipUnless(shutil.which("bwrap"), "requires bubblewrap")
class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="dark-knight-test-")
        self.addCleanup(self.scratch.cleanup)
        self.home = Path(self.scratch.name)
        self.checkout = self.home / "checkout with spaces"
        self.checkout.mkdir()
        for name in ("install.sh", "colors.toml", "neovim.lua"):
            shutil.copy2(ROOT / name, self.checkout / name)
        self.target = self.home / ".config/omarchy/themes/dark-knight"
        self.target.parent.mkdir(parents=True)
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.command("omarchy", 'printf "%s\\n" "$*" >> "$HOME/applied"\n')

    def command(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\n" + body)
        path.chmod(0o755)

    def run_install(self, location="checkout with spaces"):
        env = dict(os.environ)
        env["PATH"] = str(HOME_PATH / "bin") + ":/usr/bin:/bin"
        return subprocess.run(
            ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--bind",
             str(self.home), str(HOME_PATH), "--unshare-net", "--chdir",
             str(HOME_PATH), "/bin/bash", str(HOME_PATH / location / "install.sh")],
            env=env, capture_output=True, text=True,
        )

    def backups(self):
        return list((self.home / ".local/state/dark-knight/backups").glob("*/theme"))

    def test_fresh_and_repeated_install(self):
        for _ in range(2):
            result = self.run_install()
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.readlink(self.target), str(HOME_PATH / self.checkout.name))
        self.assertEqual(self.backups(), [])
        self.assertEqual((self.home / "applied").read_text(),
                         "theme set dark-knight\ntheme set dark-knight\n")

    def test_existing_directory_is_preserved(self):
        self.target.mkdir()
        (self.target / "local-edit").write_text("keep me")
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual((self.backups()[0] / "local-edit").read_text(), "keep me")

    def test_broken_link_is_preserved(self):
        self.target.symlink_to("/missing-dark-knight-checkout")
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.readlink(self.backups()[0]), "/missing-dark-knight-checkout")

    def test_refuses_to_move_its_own_checkout(self):
        shutil.copytree(self.checkout, self.target)
        result = self.run_install(".config/omarchy/themes/dark-knight")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Clone Dark Knight outside", result.stderr)
        self.assertFalse(self.target.is_symlink())
        self.assertEqual(self.backups(), [])

    def test_failed_link_restores_previous_install(self):
        self.target.mkdir()
        (self.target / "local-edit").write_text("keep me")
        self.command("ln", "exit 1\n")
        result = self.run_install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Previous theme preserved", result.stdout)
        self.assertEqual((self.target / "local-edit").read_text(), "keep me")
        self.assertFalse((self.home / "applied").exists())

    def test_failed_apply_can_be_retried(self):
        self.command("omarchy", "exit 7\n")
        result = self.run_install()
        self.assertEqual(result.returncode, 7)
        self.assertNotIn("Dark Knight installed", result.stdout)
        self.assertTrue(self.target.is_symlink())
        self.command("omarchy", "exit 0\n")
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.backups(), [])
