# Dark Knight

An [Omarchy](https://omarchy.org) theme. One hue, carried by light.

Built from the wallpaper it is worn with, and from nothing else.

Quantised to sixteen buckets that photograph is monochromatic: every colour
with any real area sits at hue 203 in HLS and 249 in Lab, saturation falls from
34% in the shadows to 10% at the highlight, chroma never passes 13, and warm
pixels are 0.07% of the frame. So the theme is built the same way. Every
structural colour is that hue with the image's own saturation for its
lightness, and hierarchy is carried by lightness alone.

The accent is the image's own hue, measured in Lab because that is the space
it is placed in, carried at 2.4 times the image's peak chroma. Both of those
are measured rather than written down, so a vivid wallpaper would get a vivid
accent and this one gets a quiet one.

A monochrome photograph has no red and no green, and a terminal needs them
anyway. So the image sets the envelope rather than the hue: its peak chroma
fixes how colourful anything may be, the ANSI set sits at 1.75 times it and so
below the accent, and the hues are then positions on the wheel, spaced far
enough apart that the distance floors pass. There is no gold and no imported
accent.

`src/palette.py` derives `colors.toml` from the wallpaper, so the palette is
reproducible rather than picked by eye:

```sh
python3 src/palette.py backgrounds/<wallpaper>.jpg > colors.toml
src/render.sh   # gtk.css, shell.controls.toml, neovim.lua, wallpapers, preview
```

`render.sh` regenerates everything else derived from `colors.toml`, so a
wallpaper change cannot leave one surface wearing the previous palette.

![Dark Knight](preview.png)

## Install

```sh
omarchy theme install https://github.com/itsgg/omarchy-dark-knight-theme.git
```

Omarchy takes the theme name from the repo name, so this lands as `dark-knight`
and applies itself. To switch back to it later:

```sh
omarchy theme set "Dark Knight"
```

### Or as a working copy, which is what gets `neovim.lua`

`omarchy theme install` clones into `~/.config/omarchy/themes`, and a clone
there came from a stranger, so `omarchy-theme-set` holds it to a list that
drops any `.lua` at the top of the theme, which is the only place `neovim.lua`
can be: Neovim runs it at startup. A symlink to your own working copy is not
held to that list, in Omarchy's words "theirs to fill however they like". Same
theme, one staging rule apart:

```sh
git clone https://github.com/itsgg/omarchy-dark-knight-theme.git ~/src/dark-knight
ln -sT ~/src/dark-knight ~/.config/omarchy/themes/dark-knight
omarchy theme set "Dark Knight"
```

`ln -sT` rather than `ln -s`, and no `-f`: if the clone install has already
left a `themes/dark-knight` directory there, a plain `ln -s` puts the link
*inside* it and the outer clone keeps being the theme. The `-T` form refuses
instead. Delete that directory first, it is a clone and holds nothing of
yours, and run the link again.

That install gets the indent guides below; the clone install gets Omarchy's
generated spec instead, and everything else about the theme is identical.

Two consequences of the link, both by design. `omarchy theme update` passes
over it, because a working copy is not Omarchy's to pull, so it updates with
`git -C ~/src/dark-knight pull` and a `theme set` after. And `omarchy theme
install` of this repo replaces the link with a clone, which quietly drops back
to the generated spec.

### Updating an install that is already there

Installed the ordinary way, with `omarchy theme install`, so a clone:

```sh
omarchy theme update
omarchy theme refresh
```

Two commands rather than one chained with `&&`: `omarchy theme update` returns
the exit status of the last clone it pulled, so an unrelated theme failing to
pull would skip the refresh this theme needs, and an early failure is hidden
by a later success.

Both halves are needed. `omarchy theme update` pulls every cloned theme under
`~/.config/omarchy/themes` and restages nothing, and a pull changes only that
directory: what Neovim, GTK and the bar read is the copy under
`~/.local/state/omarchy/current/theme`, which a theme set rebuilds.
`omarchy theme refresh` is that set, on whatever theme is current, with the
wallpaper left alone. From another theme, `omarchy theme set "Dark Knight"`
instead, which is the same rebuild plus the switch.

Installed as a working copy, which Omarchy deliberately will not pull:

```sh
git -C ~/src/dark-knight pull && omarchy theme refresh
```

A working copy restages the whole theme that way, `neovim.lua` included. A
clone install gets everything except that file, which Omarchy will not hand it
at all. There are two ways to have it anyway, and the first leaves the install
you already have alone.

#### Keeping the clone install, and dimming the guides from Neovim

Omarchy's generated spec is an ordinary lazy.nvim spec, so a spec of your own
merges into it. This one adds the `on_highlights` that `neovim.lua` would have
carried, and derives both colours from the palette in front of it rather than
naming this theme's, so it stays right under any Omarchy theme built on
aether:

```lua
-- ~/.config/nvim/lua/plugins/zz-indent-guides.lua
return {
  {
    "bjarneo/aether.nvim",
    name = "aether",
    optional = true,
    opts = {
      on_highlights = function(hl, c)
        local function blend(from, to, amount)
          local out = "#"
          for i = 2, 6, 2 do
            local a = tonumber(from:sub(i, i + 1), 16)
            local b = tonumber(to:sub(i, i + 1), 16)
            out = out .. string.format("%02X", math.floor(a + (b - a) * amount + 0.5))
          end
          return out
        end

        local guide = blend(c.bg, c.fg, 0.14)
        local scope = blend(c.bg, c.accent or c.blue, 0.6)

        for _, group in ipairs({ "NonText", "Whitespace", "SnacksIndent", "IblIndent" }) do
          hl[group] = { fg = guide, nocombine = true }
        end
        for _, group in ipairs({ "SnacksIndentScope", "SnacksIndentChunk", "IblScope", "MiniIndentscopeSymbol" }) do
          hl[group] = { fg = scope, nocombine = true }
        end
      end,
    },
  },
}
```

The `zz-` in the filename is load-bearing. lazy.nvim imports
`lua/plugins/*.lua` in alphabetical order and a later spec's `opts` wins, so
`indent-guides.lua` would be overridden by the `theme.lua` Omarchy symlinks in
while `zz-indent-guides.lua` is not. On a clone install nothing else sets
these groups and either name works; on a working copy, only the `zz-` name
stays in charge of them. Two `on_highlights` callbacks do not merge, the later
one replaces the earlier.

`optional = true` means the spec adds nothing on a setup that never mentions
aether; it does not test which theme is applied, and on this one Omarchy's own
`all-themes.lua` names aether anyway. What decides whether the callback does
anything is whether aether is the colorscheme in use, which is most Omarchy
themes. That is also why the colours are derived rather than named: under this
theme they land on #252B2E and #336581, against the #283943 and #236A8C the
theme ships, the same two places on the ramp measured rather than written
down; under another aether theme they are that theme's.

#### Or moving the clone onto a working copy

The other way is to become the kind of install Omarchy will hand `.lua` to.
The clone first, so that nothing is removed until the thing replacing it is on
disk: `git clone` refuses a destination that already holds anything, and fails
there rather than after the removal.

```sh
git clone https://github.com/itsgg/omarchy-dark-knight-theme.git ~/src/dark-knight
rm -rf ~/.config/omarchy/themes/dark-knight
ln -sT ~/src/dark-knight ~/.config/omarchy/themes/dark-knight
omarchy theme set "Dark Knight"
```

That `rm -rf` takes a git repository with it. It is a clone of this one, so
its history is on GitHub, but edits, untracked files and unpushed commits in
it are not: `git -C ~/.config/omarchy/themes/dark-knight status` before, if
you have ever opened it. The desktop keeps its current look throughout either
way, because the staged copy under `~/.local/state` is not touched until the
set. Restart Neovim afterwards, since it reads its spec at startup.

### Neovim and VS Code

Both editors come from `colors.toml` through Omarchy's own templates, so they
match the rest of the theme exactly rather than approximately. The theme used
to ship `neovim.lua` and `vscode.json` pointing both at Kanagawa, chosen
because it is "warm gold on near-black, the same relationship as `--gold-500`
on `--ink-900`". That relationship no longer exists, and both files went.

`neovim.lua` is back, as one override rather than another colorscheme.
Omarchy's template hands aether the palette and stops there, and aether spends
`muted` on text and on decoration alike: comments and line numbers, but also
`NonText`, which is what snacks.nvim draws every indent guide with, and
`IblIndent`, which is indent-blankline's. So the guides arrive at 3.95:1 on
the ground, in the comment colour and at comment weight, on every indented
line of the file. The scope guide arrives louder still, at full `cyan` (6.45:1
under snacks) or `blue` (6.43:1 under indent-blankline): the weight of code,
for a piece of chrome. Dimming `muted` cannot fix that, because it is also the
comment colour and comments are text. So `src/neovim.py` reads Omarchy's
template, resolves it from `colors.toml`, and inserts an `on_highlights` block
that puts the guides on `line` (1.60:1, already this theme's structure colour
and its inactive window border) and the scope guides on `accent_dim` (3.20:1).
Comments, line numbers and every other use of `muted` are untouched.

Shipping the file freezes the rest of the spec the way `shell.controls.toml`
freezes its section: Omarchy does not overwrite a file the theme ships, so a
change to `neovim.lua.tpl` upstream arrives here only when `src/render.sh` is
run again.

Which install gets the file is the staging rule above: a working copy does, a
clone in `~/.config/omarchy/themes` does not, because Omarchy stages no `.lua`
from one. Nothing in `colors.toml` can stand in for it either, since the whole
problem is one palette key spent on text and on decoration at once and only
code can tell those apart. A clone install is not stuck, though: the same
override in your own Neovim config does the same work, and is under
[Updating](#updating-an-install-that-is-already-there). Fixing it for everyone
at once would mean fixing it a level up, in aether or in `neovim.lua.tpl`,
where it would reach every theme that takes Omarchy's generated spec rather
than this one alone.

## About the emblem

The bat is drawn from scratch in `src/bat.py`, as cubic beziers rather than
traced.

## Where the colors come from

Not from the site's primitives any more. `src/palette.py` measures the
wallpaper and derives every value from it:

| Key | Value | How it is decided |
|---|---|---|
| `background` | `#0A1014` | the image's hue at 6% lightness, with the image's own saturation for that lightness |
| `line` | `#283943` | the same ramp at 21% |
| `muted` | `#5D7583` | raised until it clears 3:1 on every surface it lands on |
| `dark_foreground` | `#7F919C` | raised until it clears 4.5:1 on the same three |
| `foreground` | `#CCCFD1` | the ramp above anything in the photograph, because text sits on top of it |
| `accent` | `#4F9EC9` | the image's Lab hue, at 2.4x its peak chroma (31) |
| `red` `green` `yellow` `blue` `magenta` `cyan` | one chroma, one lightness | fixed hues, all at 1.75x the image's peak chroma (23) so none is louder than the accent |

Chroma, not saturation. An earlier version equalised the ANSI set on HLS
saturation and green, magenta and cyan came out reading twice as colourful as
blue at the same number, so the terminal looked like a different theme from the
interface around it.

The script audits its own output against those floors and exits non-zero if
one is missed, so a palette generated from a different wallpaper either meets
them or says which it did not.

## Square corners

Everything, deliberately.

This theme has no other decoration: one hue, no gradients in content, no
shadow carrying meaning, hierarchy by lightness alone. A corner radius was the
only softening gesture in it, and it was inherited from Omarchy's default
rather than chosen. Nearly every window on this desktop is a terminal, which is
a monospace grid, and the 2px border is a line: both read more decisively as a
rectangle than as a rounded one.

It is set in `~/.config/hypr/looknfeel.lua`, not here, because Hyprland owns
window rounding:

```lua
hl.config({ decoration = { rounding = 0 } })
```

The shell follows that value on its own (`Commons/Style.qml`: `cornerRadius`
mirrors `decoration:rounding`), so the bar, menu, notifications and OSD go
square with it. **It does not watch `looknfeel.lua`**: it re-polls Hyprland at
startup, when a gaps toggle file changes, and when a theme is applied. So after
changing the value the windows change immediately and the panels keep their old
corners until something triggers that poll, and `omarchy-restart-shell` is the
reliable one. Do not use `omarchy-refresh-shell` for this: it resets
`shell.json` to defaults and drops any bar plugins.

GTK is separate again. libadwaita rounds its widgets from its own stylesheet
and Hyprland cannot reach inside a window, so `gtk.css` carries a blanket
`border-radius: 0`, with circular controls left circular because a squared-off
avatar is a different widget rather than a sharper corner.

## GTK and icons

Omarchy generates seventeen surfaces from `colors.toml`, and GTK is not one of
them: `omarchy-theme-set-gnome` only flips Adwaita between light and dark and
sets the icon theme. Every GTK application therefore falls back to stock
Adwaita-dark, which here means Nautilus, its previewer and the file-chooser
portal that every application opens.

`gtk.css` fills that in, generated from the palette by `src/gtk.py`. It names
libadwaita's semantic colours explicitly rather than only the accent, which is
what stops a stock blue turning up in a selection or a link, and it maps the
theme's ramp onto depth: windows on the base, the file view recessed below it,
sidebars, cards and popovers raised above it.

**They need two symlinks to do anything.** Nothing in Omarchy copies a theme's
`gtk.css` anywhere GTK looks, so on their own the files are inert:

```sh
ln -sfn ~/.local/state/omarchy/current/theme/gtk.css  ~/.config/gtk-4.0/gtk.css
ln -sfn ~/.local/state/omarchy/current/theme/gtk3.css ~/.config/gtk-3.0/gtk.css
```

Two files rather than one, because GTK3 does not know `alertdialog`, `banner`,
`toast` or `menubutton`, and it is still the toolkit behind
`xdg-desktop-portal-gtk`, which draws the file chooser every application opens.
That chooser was the last surface wearing stock Adwaita. Measured after the
GTK3 file landed: header `#0B1116`, sidebar `#0A1115`, list `#0D1317`, border
`#25698A`, which are this theme's colours rather than Adwaita's `#353535` and
`#2d2d2d`.

`xdg-desktop-portal-gtk` caches its stylesheet, so restart it (or log out)
after the first link or the chooser keeps its old look.

Pointing at `current/theme` rather than at this theme means it follows theme
switches on its own, and any theme shipping a `gtk.css` gets picked up too.

`icons.theme` is `Yaru-prussiangreen-dark`, which `omarchy-theme-set-gnome`
applies on its own. It is chosen by measurement rather than by name: its folder
colour is `#6BADAA` at chroma 22.3, within a point of the 23 this theme
gives its ANSI set, so icons sit under the accent instead of over it.
`Yaru-blue-dark` matches the accent's hue more closely but its folders are
`#5AA8FD` at chroma 49.4, half again more colourful than the accent itself
(31), and with an icon on every row that is the loudest thing in a window.

## Backgrounds

Five: two photographs and three generated.

The palette is derived from `0-batman-dark-knight-portrait.jpg`, so that one
is the theme's reference image and the one the preview above is composited
over. It is numbered `0-` for a reason. `omarchy-theme-set` sorts the backgrounds and
takes the first one when the current wallpaper is not already among them, which
is the case when you switch in from another theme; when it is among them, it
advances to the next instead, so re-running it on the theme you are already
using cycles. Two caveats: the sort is over full paths, so anything you drop in
`~/.config/omarchy/backgrounds/dark-knight/` sorts ahead of everything here, and
the advance is decided by the current path rather than by whether the theme
changed. `1-` through `3-` are the generated grounds and `4-` is the second
photograph.

| File | |
|---|---|
| `0-batman-dark-knight-portrait.jpg` | the reference image; every colour in `colors.toml` is measured from it |
| `4-batman-motorcycle-gotham.jpg` | the same world, warmer and busier; the palette is not derived from this one |

The other three are generated, no raster source at all.

They are deliberately flat: no blur filters anywhere, every edge a real vector
edge, and the only soft thing in a frame is the vignette. A wallpaper competes
with your windows for the same attention and loses if it tries to be the
subject, so these are built to sit behind a terminal all day.

| File             | What it is                                                     |
|------------------|----------------------------------------------------------------|
| `1-grid.jpg`     | Steel hairline grid, accent axes on thirds, emblem at the origin. |
| `2-emblem.jpg`   | The emblem as a dark mass with an accent rim, off-center.       |
| `3-rings.jpg`    | Concentric hairlines off a center near the right edge, one measured accent ring. |

The emblem appears in all three generated grounds at a different scale each time: the subject in
one, a mark at a grid origin in another, the source of the sweep in the third.
That is what makes them a set rather than three unrelated images.

`src/bat.py` holds the emblem, authored as cubic beziers rather than straight
segments: the trailing edge is a run of smooth scallops between sharp downward
spikes, which polylines cannot produce. Two constraints the shape depends on
are noted in that file. The wing's top edge must never dip below the shoulder,
or the head reads as a crown sitting on a separate shape. The notch between the
ears stays narrow and shallow.

`src/flat.py` composes the three wallpapers and reads `colors.toml` for its
colors, so they follow the palette. `src/render.sh` renders everything.

### The noise pass is load-bearing

These are near-black grounds with a wide vignette. At 8 bits per channel that
gradient bands into visible concentric rings without a dither, so `render.sh`
adds Gaussian noise after rasterizing. Do not move it into the SVG as an
`feTurbulence` overlay: librsvg flattens that into a uniform +3-level wash,
which pushes the ground off the base.

