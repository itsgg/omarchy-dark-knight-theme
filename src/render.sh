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

# Shared compositions for both wallpapers and matching Plymouth marks.
python3 artwork.py
