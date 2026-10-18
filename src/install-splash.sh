#!/usr/bin/env bash
# Install a separate Plymouth theme; leave Omarchy's shared assets intact.
set -euo pipefail
variation=${1:-gotham}
case "$variation" in gotham|cape) ;; *) echo 'Usage: install-splash.sh [gotham|cape]' >&2; exit 1;; esac
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
python3 "$repo/src/plymouth.py" "$work" "$variation"
# Build unprivileged, then publish a fixed list to a theme-owned directory.
# The backup remains available if a rebuild fails.
pkexec /bin/bash -s -- "$work" <<'ROOT'
set -euo pipefail
source=$1
target=/usr/share/plymouth/themes/dark-knight
[[ ! -L "$target" ]]
backup=$(mktemp -d /var/tmp/dark-knight-plymouth.XXXXXXXX)
chmod 700 "$backup"
previous=$(plymouth-set-default-theme)
select_and_rebuild() {
  plymouth-set-default-theme "$1" || return
  # Match Omarchy's bootloader-aware rebuild path. Limine has no presets.
  if command -v limine-mkinitcpio >/dev/null 2>&1; then
    limine-mkinitcpio
  else
    mkinitcpio -P
  fi
}
if [[ -e /etc/plymouth/plymouthd.conf ]]; then
  cp -a /etc/plymouth/plymouthd.conf "$backup/plymouthd.conf"
fi
stage=$(mktemp -d /usr/share/plymouth/themes/.dark-knight.XXXXXXXX)
trap 'rm -rf "$stage"' EXIT
for asset in dark-knight.plymouth omarchy.script logo.png entry.png bullet.png lock.png progress_bar.png progress_box.png; do
  install -o root -g root -m 644 "$source/$asset" "$stage/$asset"
done
chmod 755 "$stage"
# Existing assets were backed up; the fixed directory contains only theme files.
if [[ -d $target ]]; then mv "$target" "$backup/previous-theme"; fi
if ! mv "$stage" "$target"; then
  if [[ -d $backup/previous-theme ]]; then mv "$backup/previous-theme" "$target"; fi
  echo "Plymouth publish failed; previous theme restored. Backup: $backup" >&2
  exit 1
fi
if ! select_and_rebuild dark-knight; then
  echo "Plymouth rebuild failed; restoring previous theme. Backup: $backup" >&2
  rm -rf "$target"
  if [[ -d $backup/previous-theme ]]; then mv "$backup/previous-theme" "$target"; fi
  if [[ -f $backup/plymouthd.conf ]]; then
    cp -a "$backup/plymouthd.conf" /etc/plymouth/plymouthd.conf
  else
    rm -f /etc/plymouth/plymouthd.conf
  fi
  select_and_rebuild "$previous" || true
  exit 1
fi
echo "Dark Knight splash installed. Backup: $backup"
ROOT
