#!/bin/bash
# Register this working copy so Omarchy also stages its Neovim customizations.
set -euo pipefail

checkout=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
themes="$HOME/.config/omarchy/themes"
target="$themes/dark-knight"

command -v omarchy >/dev/null || { echo "Omarchy is required." >&2; exit 1; }
[[ -f $checkout/colors.toml && -f $checkout/neovim.lua ]] || {
  echo "Run install.sh from a complete Dark Knight checkout." >&2
  exit 1
}

mkdir -p -- "$themes"
# Resolve the parent, but not the final link: an existing link to this checkout
# is the expected result of a previous install.
target="$(cd -- "$themes" && pwd -P)/dark-knight"
case "$checkout/" in
  "$target/"*)
    echo "Clone Dark Knight outside $target, then run its install.sh." >&2
    exit 1
    ;;
esac

if [[ ! -L $target || $(readlink -f -- "$target") != "$checkout" ]]; then
  backup=""
  if [[ -e $target || -L $target ]]; then
    backup_root="$HOME/.local/state/dark-knight/backups"
    mkdir -p -- "$backup_root"
    backup=$(mktemp -d "$backup_root/install-$(date +%Y%m%d-%H%M%S)-XXXXXX")
    mv -T -- "$target" "$backup/theme"
    echo "Previous theme preserved at $backup/theme"
  fi

  if ! ln -sT -- "$checkout" "$target"; then
    if [[ -n $backup ]]; then
      mv -T -- "$backup/theme" "$target"
    fi
    exit 1
  fi
fi

# A symlink to a working copy is Omarchy's supported opt-in to theme Lua.
omarchy theme set dark-knight
echo "Dark Knight installed, including Neovim highlights. Restart Neovim."
