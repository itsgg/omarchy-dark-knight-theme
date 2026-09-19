#!/usr/bin/env bash
# Re-render everything Dark Knight derives from colors.toml: the GTK and shell
# files, btop.theme, neovim.lua, the wallpaper and the
# Plymouth mark. preview.png is not here: it is a screenshot, taken by
# preview.sh.
set -euo pipefail
cd "$(dirname "$0")"

# One scratch directory, and the trap before anything is made in it. There
# were two mktemp calls once with the trap after the second, so a failure of
# the second left the first behind.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Every generated file goes through here: written to scratch, moved into place
# only if its generator succeeded. A plain `generator >../file` truncates the
# shipped file before the generator has run, so a palette missing one key left
# a zero-byte shell.bar.toml behind under `set -e`. neovim.lua was always
# written this way, because it is the generator most likely to fail (it reads
# Omarchy's own template); the rest were not, and two reviewers said so.
# mktemp rather than a fixed /tmp name: a fixed one is another render's
# output, or a symlink pointing at something that is not ours to truncate.
emit() {
  local out=$1
  shift
  "$@" >"$work/emit"
  place "$work/emit" "$out"
}

# The images take the same road, for the same reason: an encoder that dies
# half way through (a full disk is enough) leaves a truncated PNG where a good
# one was. They are written in scratch by the tool that makes them and only
# then moved. The first pass of emit() covered the text files and left these
# writing straight into the repository, and a reviewer said so.
place() {
  # No timestamps in a PNG, or every render is a change to commit whether or
  # not anything changed. ImageMagick writes tIME and date chunks by default,
  # and so does whatever Omarchy's Plymouth preview uses.
  if [[ $2 == *.png ]]; then
    magick "$1" -strip -define png:exclude-chunks=date,time "$work/stripped.png"
    mv "$work/stripped.png" "$1"
  fi
  mv "$1" "../$2"
  chmod 644 "../$2"
  echo "$2"
}

# Everything derived from colors.toml, not only the wallpapers. gtk.css and
# shell.controls.toml were left out once and a wallpaper change silently left
# GTK and the shell wearing the previous palette.
emit gtk.css python3 gtk.py
emit gtk3.css python3 gtk.py --gtk3
for section in controls bar launcher menu lock; do
  emit "shell.$section.toml" python3 controls.py "$section"
done
emit btop.theme python3 btop.py
emit neovim.lua python3 neovim.py

python3 flat.py >/dev/null

# The Plymouth mark. Transparent, so no noise pass and no JPEG.
python3 unlock.py >"$work/unlock.svg"
rsvg-convert "$work/unlock.svg" -o "$work/unlock.png"
place "$work/unlock.png" unlock.png
# And what it looks like at boot, which is the card the Plymouth switcher
# shows. Omarchy draws it, so this is the other step that needs Omarchy here.
if command -v omarchy-plymouth-preview >/dev/null; then
  colour() { python3 -c 'import sys,tomllib; print(tomllib.load(open("../colors.toml","rb"))[sys.argv[1]])' "$1"; }
  # omarchy-plymouth-preview ends in `imv -f <output>`: it opens the result
  # full screen and blocks until that window is closed, which from a script
  # is a render that hangs with a viewer over somebody's work. A no-op imv
  # ahead of the real one on PATH, for this one call.
  mkdir -p "$work/bin"
  printf '#!/bin/sh\nexit 0\n' >"$work/bin/imv"
  chmod +x "$work/bin/imv"
  PATH="$work/bin:$PATH" \
  omarchy-plymouth-preview "$(colour background)" "$(colour foreground)" \
    "$(realpath ../unlock.png)" "$work/preview-unlock.png" >/dev/null
  place "$work/preview-unlock.png" preview-unlock.png
else
  echo "preview-unlock.png skipped: no omarchy-plymouth-preview" >&2
fi

# Lossless, and no noise pass. These were JPEGs dithered with Gaussian noise
# while they had a vignette to keep from banding; with a flat ground there is
# no gradient to band, and PNG keeps a one pixel hairline one pixel wide,
# which JPEG does not.
for f in [0-9]-*.svg; do
  rsvg-convert -w 3840 -h 2400 "$f" -o "$work/render.png"
  magick "$work/render.png" -depth 8 -strip -define png:compression-level=9 "$work/wallpaper.png"
  place "$work/wallpaper.png" "backgrounds/${f%.svg}.png"
done
