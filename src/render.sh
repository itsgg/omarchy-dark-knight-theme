#!/usr/bin/env bash
# Re-render the three Dark Knight wallpapers and the preview card.
#
# flat.py writes the three SVGs from bat.py's emblem; this renders them.
#
# The Gaussian noise pass is not decoration. These are near-black grounds with
# a wide vignette, and at 8 bits per channel that gradient bands into visible
# concentric rings without a dither. Do not move it into the SVG as an
# feTurbulence overlay -- librsvg flattens that into a uniform +3-level wash,
# which pushes the ground off --ink-900.
set -euo pipefail
cd "$(dirname "$0")"

# Everything derived from colors.toml, not only the wallpapers. gtk.css and
# shell.controls.toml were left out once and a wallpaper change silently left
# GTK and the shell wearing the previous palette.
python3 gtk.py >../gtk.css
python3 controls.py >../shell.controls.toml
echo "gtk.css"
echo "shell.controls.toml"

python3 flat.py >/dev/null

for f in [0-9]-*.svg; do
  rsvg-convert -w 3840 -h 2400 "$f" -o /tmp/dk-render.png
  magick /tmp/dk-render.png -attenuate 0.22 +noise Gaussian -depth 8 \
    -quality 93 -sampling-factor 4:4:4 -strip "../backgrounds/${f%.svg}.jpg"
  echo "backgrounds/${f%.svg}.jpg"
done

# The preview card is the terminal and palette composited OVER a real wallpaper,
# so it shows the theme as a desktop rather than as a flat swatch sheet. The
# overlay is transparent SVG, and the backdrop is the wallpaper the palette was
# derived from, so the screenshot shows the theme over the image it was built
# for rather than over one of its own generated grounds.
# No dither here: the card has no wide near-black gradient to band, and skipping
# it takes the PNG from 2.4M to ~150K.
# The overlay is a template: every colour in it is a {{key}} from colors.toml,
# resolved here. It used to hold literal hexes, which meant the preview kept
# showing the palette the theme had when somebody last edited the SVG by hand.
python3 - <<'RESOLVE' >/tmp/dk-overlay.svg
import pathlib, re, sys, tomllib
p = tomllib.load(open("../colors.toml", "rb"))
s = pathlib.Path("preview-overlay.svg").read_text()
missing = sorted({k for k in re.findall(r"\{\{([a-z_]+)\}\}", s) if k not in p})
if missing:
    sys.exit("render: colors.toml has no " + ", ".join(missing))
sys.stdout.write(re.sub(r"\{\{([a-z_]+)\}\}", lambda m: p[m.group(1)], s))
RESOLVE
rsvg-convert -w 1800 -h 1012 /tmp/dk-overlay.svg -o /tmp/dk-overlay.png
magick ../backgrounds/0-batman-dark-knight-portrait.jpg -resize 1800x1012^ -gravity center -extent 1800x1012 \
  /tmp/dk-overlay.png -composite ../preview.png
rm -f /tmp/dk-overlay.png
echo "preview.png"
rm -f /tmp/dk-render.png
