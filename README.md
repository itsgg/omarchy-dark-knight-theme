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
src/render.sh   # gtk.css, shell.controls.toml, the wallpapers and the preview
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

### Neovim and VS Code

This theme no longer ships `neovim.lua` or `vscode.json`. They pointed both
editors at Kanagawa, chosen because it is "warm gold on near-black, the same
relationship as `--gold-500` on `--ink-900`". That relationship no longer
exists: the palette is one cold hue carried by lightness. Omarchy generates
both editors from `colors.toml` through its own templates, so they now match
the rest of the theme exactly rather than approximately.

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

**It needs one symlink to do anything.** Nothing in Omarchy copies a theme's
`gtk.css` anywhere GTK looks, so on its own the file is inert:

```sh
ln -sfn ~/.local/state/omarchy/current/theme/gtk.css ~/.config/gtk-4.0/gtk.css
```

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

