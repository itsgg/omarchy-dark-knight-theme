# Installing and updating

## Full installation

```sh
git clone https://github.com/itsgg/omarchy-dark-knight-theme.git ~/.local/share/dark-knight-theme
bash ~/.local/share/dark-knight-theme/install.sh
```

The installer links the checkout to `~/.config/omarchy/themes/dark-knight`
and applies the theme. Omarchy stages `neovim.lua` from a working-copy link,
so its quiet indent guides and syntax colours arrive with the palette. This
explicit install opts into running the theme's Lua in Neovim.

Keep the checkout in place: the installed theme links to it. A checkout
elsewhere works too; run its `install.sh`. Running it again re-applies the
theme without making another backup when the link already points to it.
Restart Neovim after installing.

### Existing installs

Use the same commands above. An existing theme directory or link is moved
intact into a unique directory under `~/.local/state/dark-knight/backups/`.
The installer prints that path. Local edits, untracked files, and git history
are preserved. It does not delete or pull the previous checkout.

If the checkout destination already exists, inspect it before using it;
`git clone` refuses to overwrite it. Run `install.sh` from a checkout outside
`~/.config/omarchy/themes/dark-knight`. The installer refuses to link a
directory to itself.

If applying the theme fails, the checkout and link remain installed. Resolve
the reported error and rerun `install.sh`.

Remove any earlier personal Neovim override for this theme, such as
`lua/plugins/zz-dark-knight.lua` or `zz-indent-guides.lua`, if you want the
shipped highlights to take effect. Later `on_highlights` callbacks can replace
or override the theme's callback. The installer leaves Neovim user files alone.

## Updating

Omarchy deliberately skips working-copy links during `omarchy theme update`.
Update this checkout, then re-apply:

```sh
git -C ~/.local/share/dark-knight-theme pull --ff-only && omarchy theme refresh
```

Use the path you cloned to if different. Refresh applies the current theme
and leaves the wallpaper alone. If another theme is selected, use
`omarchy theme set "Dark Knight"` after the pull instead. Updates to the
checkout's `neovim.lua` reach Neovim on each refresh or theme switch.

## Wallpaper variations

Apply Dark Knight first, then choose Gotham or Cape using the staged paths:

```sh
omarchy theme bg set ~/.local/state/omarchy/current/theme/backgrounds/1-gotham.png
omarchy theme bg set ~/.local/state/omarchy/current/theme/backgrounds/2-cape.png
```

Run the command for the variation you want. Use `omarchy theme bg next` to
cycle. After updating from an earlier version, select one of these files:
the old `1-origin.png` wallpaper has been replaced. A theme refresh preserves
the previous wallpaper link, so it cannot repair a link to that removed file.
Wallpaper changes leave the boot splash alone; its commands are below.

## Standard Omarchy installation

```sh
omarchy theme install https://github.com/itsgg/omarchy-dark-knight-theme.git
```

This installs the palette, but Omarchy excludes Lua from cloned themes and
generates its own Neovim spec. The syntax and indent-guide overrides are
therefore missing. Omarchy does not run the repository's `install.sh`.
Use the full installation above to include those customizations.

For a standard install, run `omarchy theme update`, then
`omarchy theme refresh`. Running `omarchy theme install` over a working-copy
link replaces the link with a standard clone; run your checkout's
`install.sh` again to restore the full installation.

## Removing the full installation

Switch to another installed theme first. Check that
`~/.config/omarchy/themes/dark-knight` is still the working-copy symlink, then
remove just that link:

```sh
unlink ~/.config/omarchy/themes/dark-knight
```

The checkout and any backups remain. To restore an earlier install, move its
printed `backups/.../theme` path back to `~/.config/omarchy/themes/dark-knight`
after removing the link, then apply Dark Knight again.

## GTK

Nothing in Omarchy copies a theme's `gtk.css` anywhere GTK looks, so on their
own the two files are inert. `hooks/gtk-follow-theme` links them and restarts
the file-chooser portal, which reads its stylesheet once at start:

```sh
omarchy hook install theme-set ~/.config/omarchy/themes/dark-knight/hooks/gtk-follow-theme
omarchy theme refresh
```

The links point at `~/.local/state/omarchy/current/theme`, not at this theme,
so they follow every later theme switch and any theme shipping a `gtk.css` is
picked up too. A real `gtk.css` that is already there is left alone.

## Plymouth

`unlock.png` is the mark for the boot and disk-unlock screen. Omarchy does not
apply it on a theme switch; that is its own command, and it shows a password
dialog because it rebuilds the initramfs:

```sh
bash ~/.config/omarchy/themes/dark-knight/src/install-splash.sh gotham
```

Gotham is the default splash. To use the Cape splash:

```sh
bash ~/.config/omarchy/themes/dark-knight/src/install-splash.sh cape
```

The installer creates a separate `dark-knight` Plymouth theme. It preserves
Omarchy's password callbacks and field position and hides the external lock
icon with a transparent asset. Omarchy's shared theme files are left intact.
A backup is printed after installation; a failed rebuild restores the
previous theme and attempts to rebuild it again. This affects the boot and
disk-unlock screen, not the desktop lock screen or SDDM login screen.
Rebuilding uses `limine-mkinitcpio` when installed, matching Omarchy's
Limine setup; other systems use `mkinitcpio -P`.

To restore Omarchy's shared layout, including its external lock icon:

```sh
omarchy plymouth set by theme dark-knight
```

Wallpaper selection is independent. Commands for both wallpapers and splash
previews are in [Choose a variation](../README.md#choose-a-variation).

## Obsidian

Omarchy syncs the theme stylesheet into Obsidian vaults recorded in
`~/.config/obsidian/obsidian.json`. If you open Obsidian for the first time,
clone a vault, or create a new vault after applying this theme, sync it with:

```sh
omarchy theme refresh
```

This writes `theme.css` into each vault's `.obsidian/themes/Omarchy/`
directory so Obsidian picks up the theme without switching themes away and back.


## Matching SDDM login, 2026-10-19

Run the following to install the dedicated login theme:

```sh
bash ~/.config/omarchy/themes/dark-knight/src/install-login.sh
```

It
uses the bat emblem in the wallpaper colour at 60% opacity, with a blue-grey
password border, centred placeholder and dots, and no lock icon. The installer writes to
`/usr/local/share/sddm/themes/dark-knight` and
`/etc/sddm.conf.d/zz-dark-knight.conf`. It keeps backups in
`/var/tmp/dark-knight-login.*` and does not restart SDDM or the current session.

Run `python3 src/login.py <preview-directory>` and
`sddm-greeter-qt6 --test-mode --theme <preview-directory>` for a preview.
Autologin may bypass the greeter; this theme does not change autologin.

Boot and disk unlock use `bash src/install-splash.sh gotham` for the circular
Bat-Signal emblem, or `bash src/install-splash.sh cape` for the standalone emblem.
Both use dim artwork and a blue-grey password border. Masked dots stay centred while
password length changes, and the lock icon remains hidden.
