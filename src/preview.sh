#!/usr/bin/env bash
# Take preview.png: the theme as a real desktop, in the layout every stock
# Omarchy theme's preview uses, so the switcher's carousel compares like with
# like. Neovim top left, btop top right, a terminal listing bottom left, Files
# bottom right, the bar across the top.
#
#     src/preview.sh          # with Dark Knight applied
#
# It takes over an empty workspace for about fifteen seconds and then puts you
# back where you were. Everything it opens is pointed at this repository, so
# the screenshot shows the theme's own files and nobody's home directory.
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
ws=9
back=$(hyprctl activeworkspace -j | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

if [[ $(hyprctl workspaces -j | python3 -c "import json,sys; print(sum(w['windows'] for w in json.load(sys.stdin) if w['id']==$ws))") != 0 ]]; then
  echo "preview: workspace $ws is not empty" >&2
  exit 1
fi

addresses() { hyprctl clients -j | python3 -c "import json,sys; print(' '.join(c['address'] for c in json.load(sys.stdin) if c['workspace']['id']==$ws))"; }
everywhere() { hyprctl clients -j | python3 -c "import json,sys; print(' '.join(c['address'] for c in json.load(sys.stdin)))"; }
pointer=$(hyprctl cursorpos)
existed=" $(everywhere) "
opened=()

# What this closes is what it opened, and nothing else. launch() records each
# window as it arrives. Files is the exception it has to allow for: it
# sometimes maps a second window late, which launch() never sees, and the
# first version left that behind. So the other thing closed is a Files window
# on this workspace, showing this repository's folder, that did not exist
# anywhere when the script started. An
# earlier fix closed everything on the workspace instead, on the grounds that
# it had been empty, and two reviewers pointed out what that does to a window
# somebody opens or moves there in the fifteen seconds this takes.
cleanup() {
  local address
  for address in "${opened[@]}" $(hyprctl clients -j | python3 -c "
import json, sys
for c in json.load(sys.stdin):
    if (c['workspace']['id'] == $ws and c['class'] == 'org.gnome.Nautilus'
            and '$(basename "$repo")' in c['title']):
        print(c['address'])"); do
    [[ $existed == *" $address "* ]] && continue
    hyprctl dispatch "hl.dsp.window.close({ window = \"address:$address\" })" >/dev/null || true
  done
  hyprctl dispatch "hl.dsp.focus({ workspace = \"$back\" })" >/dev/null || true
  # Last, because the workspace switch above can warp the pointer itself.
  hyprctl dispatch "hl.dsp.cursor.move({ x = ${pointer%,*}, y = ${pointer#*, } })" >/dev/null || true
}
trap cleanup EXIT


# Launch one window and wait for it, so the next split lands where it should.
launch() {
  local before after address
  before=$(addresses)
  setsid -f "$@" >/dev/null 2>&1
  for _ in $(seq 40); do
    sleep 0.25
    after=$(addresses)
    for address in $after; do
      if [[ " $before " != *" $address "* ]]; then
        opened+=("$address")
        last=$address
        return 0
      fi
    done
  done
  echo "preview: $1 never opened a window" >&2
  exit 1
}

# Focus follows the mouse here, and a re-tile under a still pointer refocuses
# whatever is now beneath it: the first run of this script split Neovim where
# it meant to split btop, because that is where the pointer happened to be.
# So focusing a window means putting the pointer on it as well.
focus() {
  local centre
  centre=$(hyprctl clients -j | python3 -c "
import json, sys
for c in json.load(sys.stdin):
    if c['address'] == '$1':
        print(c['at'][0] + c['size'][0] // 2, c['at'][1] + c['size'][1] // 2)")
  if [[ -z $centre ]]; then
    echo "preview: window $1 is gone, so the layout cannot be built" >&2
    exit 1
  fi
  hyprctl dispatch "hl.dsp.cursor.move({ x = ${centre% *}, y = ${centre#* } })" >/dev/null
  hyprctl dispatch "hl.dsp.focus({ window = \"address:$1\" })" >/dev/null
  sleep 0.2
}

hyprctl dispatch "hl.dsp.focus({ workspace = \"$ws\" })" >/dev/null
sleep 0.4

# On code, not on the docstring at the top. LazyVim puts the cursor back where
# it last was after the file loads, so a plain +N loses; this runs after that.
launch foot -D "$repo" nvim src/palette.py \
  -c "lua vim.defer_fn(function() vim.cmd('normal! 232Gzt') end, 1200)"
nvim=$last
launch foot -D "$repo" btop
btop=$last
focus "$nvim"
launch foot -D "$repo" bash -c 'eza -la --icons --group-directories-first; exec bash --norc -i'
focus "$btop"
launch nautilus --new-window "$repo"

# Out of the picture: the bottom right corner of the gaps.
hyprctl dispatch "hl.dsp.cursor.move_to_corner({ corner = 1 })" >/dev/null 2>&1 || true

# LazyVim finishes painting well after its window maps, and btop needs a
# couple of samples before its graphs are graphs.
sleep 5
# Made whole in scratch and then moved, so an encoder that dies half way does
# not leave a truncated preview.png where a good one was. No timestamps in it
# either, or every retake is a change whether or not a pixel moved.
raw=$(mktemp --suffix=.png)
out=$(mktemp --suffix=.png)
grim "$raw"
magick "$raw" -resize 1800x -strip -define png:exclude-chunks=date,time "$out"
mv "$out" "$repo/preview.png"
chmod 644 "$repo/preview.png"
rm -f "$raw"
echo "preview.png"
