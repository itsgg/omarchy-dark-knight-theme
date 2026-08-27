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

python3 flat.py >/dev/null

for f in [0-9]-*.svg; do
  rsvg-convert -w 3840 -h 2400 "$f" -o /tmp/dk-render.png
  magick /tmp/dk-render.png -attenuate 0.22 +noise Gaussian -depth 8 \
    -quality 93 -sampling-factor 4:4:4 -strip "../backgrounds/${f%.svg}.jpg"
  echo "backgrounds/${f%.svg}.jpg"
done

# The preview card has no wide near-black gradient, so it needs no dither --
# and skipping it takes the PNG from 2.4M to ~120K.
rsvg-convert -w 1800 -h 1012 preview.svg -o ../preview.png
echo "preview.png"
rm -f /tmp/dk-render.png
