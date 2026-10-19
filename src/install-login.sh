#!/usr/bin/env bash
# Install a dedicated SDDM theme without restarting the active session.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
python3 "$repo/src/login.py" "$work"
pkexec /bin/bash -s -- "$work" <<'ROOT'
set -euo pipefail
source=$1
parent=/usr/local/share/sddm/themes
target=$parent/dark-knight
config=/etc/sddm.conf.d/zz-dark-knight.conf
backup=$(mktemp -d /var/tmp/dark-knight-login.XXXXXXXX)
chmod 700 "$backup"
[[ ! -L "$target" && ! -L "$config" ]]
if [[ -e $config ]]; then cp -a "$config" "$backup/config"; fi
install -d -m 755 "$parent" /etc/sddm.conf.d
stage=$(mktemp -d "$parent/.dark-knight.XXXXXXXX")
trap 'rm -rf "$stage"' EXIT
for asset in Main.qml metadata.desktop theme.conf logo.png entry.png entry-failed.png bullet.png lock.png lock-failed.png; do
  install -o root -g root -m 644 "$source/$asset" "$stage/$asset"
done
chmod 755 "$stage"
if [[ -e $target ]]; then mv "$target" "$backup/theme"; fi
if ! mv "$stage" "$target"; then
  if [[ -e $backup/theme ]]; then mv "$backup/theme" "$target"; fi
  exit 1
fi
if ! printf '[Theme]\nThemeDir=/usr/local/share/sddm/themes\nCurrent=dark-knight\n' > "$config"; then
  rm -rf "$target"
  if [[ -e $backup/theme ]]; then mv "$backup/theme" "$target"; fi
  if [[ -f $backup/config ]]; then cp -a "$backup/config" "$config"; else rm -f "$config"; fi
  exit 1
fi
chmod 644 "$config"
echo "Dark Knight login installed. Backup: $backup"
ROOT
