"""Regressions for failed artwork exports and unavailable splash previews."""
from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
spec = importlib.util.spec_from_file_location('artwork', ROOT / 'src/artwork.py')
artwork = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artwork)


class ArtworkExportTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        (self.root / 'backgrounds').mkdir()
        self.sources = self.root / 'assets/artwork'
        self.sources.mkdir(parents=True)
        for key, value in [('ROOT', self.root), ('OUT', self.sources)]:
            patcher = patch.object(artwork, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_encoder_failure_preserves_previous_svg_and_png(self):
        source = self.sources / 'gotham-wallpaper.svg'
        target = self.root / 'backgrounds/1-gotham.png'
        source.write_text('previous SVG')
        target.write_bytes(b'previous PNG')

        def fail_encoder(args, **kwargs):
            if args[0] == 'rsvg-convert':
                Path(args[-1]).write_bytes(b'intermediate PNG')
            else:
                raise subprocess.CalledProcessError(1, args)

        with patch.object(artwork.subprocess, 'run', side_effect=fail_encoder):
            with self.assertRaises(subprocess.CalledProcessError):
                artwork.main()
        self.assertEqual(source.read_text(), 'previous SVG')
        self.assertEqual(target.read_bytes(), b'previous PNG')

    def test_missing_preview_tool_is_reported_and_old_previews_preserved(self):
        previews = [self.root / name for name in ('preview-unlock.png', 'preview-unlock-cape.png')]
        for preview in previews:
            preview.write_bytes(b'existing preview')

        def encode(args, **kwargs):
            Path(args[-1]).write_bytes(b'exported image')

        output = io.StringIO()
        with patch.object(artwork.subprocess, 'run', side_effect=encode):
            with patch.object(artwork.shutil, 'which', return_value=None):
                with redirect_stdout(output):
                    artwork.main()
        for preview in previews:
            self.assertEqual(preview.read_bytes(), b'existing preview')
            self.assertIn(f'{preview.name} skipped:', output.getvalue())
