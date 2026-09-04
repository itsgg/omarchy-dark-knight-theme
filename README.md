# Dark Knight

An [Omarchy](https://omarchy.org) theme. One hue, carried by light.

Retuned on 2026-09-04 against the wallpaper it is worn with. Quantised to
sixteen buckets that photograph is monochromatic: every colour with any real
area sits at hue 203, saturation falls from 34% in the shadows to 10% at the
highlight, and warm pixels are 0.07% of the frame. So the theme is built the
same way. Every structural colour is that one hue with the image's own
saturation for its lightness, hierarchy is carried by lightness alone, and the
accent is the same hue with the saturation turned up to 52%, which is the one
axis the photograph leaves unused.

The gold from the [itsgg.com](https://itsgg.com) design system is still here,
with one job: it is the warning colour. A hue foreign to everything around it
is doing its job in a warning and fighting the picture in a window frame, and
it now gets about the share of the screen it has in the image.

`src/palette.py` derives `colors.toml` from the wallpaper, so the palette is
reproducible rather than picked by eye:

```sh
python3 src/palette.py backgrounds/<wallpaper>.jpg > colors.toml
src/render.sh          # the three wallpapers and the preview follow it
```

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

The bat is drawn from scratch in `src/bat.py`. It is a fan rendition, not a
copy of any official artwork. Batman and the bat emblem are trademarks of DC
Comics. This is an unofficial, non-commercial fan theme with no affiliation
with or endorsement by DC. See [NOTICE](NOTICE).

## Where the colors come from

Not from the site's primitives any more. `src/palette.py` measures the
wallpaper and derives every value from it:

| Key | Value | How it is decided |
|---|---|---|
| `background` | `#0A1014` | the image's hue at 6% lightness, with the image's own saturation for that lightness |
| `line` | `#283943` | the same ramp at 21% |
| `muted` | `#607786` | raised until it clears 3:1 on every surface it lands on |
| `dark_foreground` | `#84949E` | raised until it clears 4.5:1 on the same three |
| `foreground` | `#CCCFD1` | the ramp above anything in the photograph, because text sits on top of it |
| `accent` | `#6CB0D0` | the same hue at 52% saturation, the one axis the image leaves unused |
| `yellow` | `#BFAB69` | the design system's gold hue, held to the family's saturation band |

The script audits its own output against those floors and exits non-zero if
one is missed, so a palette generated from a different wallpaper either meets
them or says which it did not.

## Backgrounds

Three, all generated. No stock photography, no raster source at all.

They are deliberately flat: no blur filters anywhere, every edge a real vector
edge, and the only soft thing in a frame is the vignette. A wallpaper competes
with your windows for the same attention and loses if it tries to be the
subject, so these are built to sit behind a terminal all day.

| File             | What it is                                                     |
|------------------|----------------------------------------------------------------|
| `1-grid.jpg`     | Steel hairline grid, accent axes on thirds, emblem at the origin. |
| `2-emblem.jpg`   | The emblem as a dark mass with an accent rim, off-center.       |
| `3-rings.jpg`    | Concentric hairlines off a center near the right edge, one measured accent ring. |

The emblem appears in all three at a different scale each time: the subject in
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

