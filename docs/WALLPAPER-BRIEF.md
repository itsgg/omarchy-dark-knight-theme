# Flat wallpaper design, 2026-10-18

Two distinct flat vector wallpapers and matching splash screens for the
Dark Knight theme. Keep the original bat geometry and Foot's #0A1014 ground.
Use solid shapes and a limited blue-grey palette. No gradients, textures,
3D effects, grids, dials or text.

## Research

- [GNOME background guidance](https://developer.gnome.org/hig/reference/backgrounds.html):
  keep important elements safe from cropping and UI overlays, check different
  aspect ratios, and inspect the result when blurred for the lock screen.
- [GNOME production notes](https://github.com/GNOME/gnome-backgrounds/blob/main/README.md):
  inspect actual pixels for sharpness and banding. Solid vector fills avoid
  the low-contrast gradient issue in this design.
- [KDE wallpaper guidance](https://community.kde.org/Design/Wallpapers/Wallpaper_design_guidelines):
  use broad shapes, quiet upper regions, a limited palette and visible dark
  tones. Wallpaper must keep working when partially covered by windows.
  Its no-logo rule is for Plasma submissions; this personal theme explicitly
  uses the Batman emblem as its identity.

## Compositions

Gotham uses a flat city skyline, a subdued solid signal disc and a negative
bat silhouette. A flat beam connects the disc to the city. The upper left
stays open; the skyline is anchored to the lower frame. Its splash distils
the same design to the signal disc and bat.

Cape uses a single solid bat silhouette with generous space around it.
The lower frame carries broad angular cape-inspired planes. Its splash
keeps the same emblem geometry and solid fill.

The illustration is authored in src/artwork.py, using the existing vector
in src/bat.py. Editable SVG exports are saved alongside the exported PNGs. The
wallpapers are 3840x2400, with transparent 1320x480 splash canvases. No
image generation or Blender is required to regenerate these final designs.

## Validation

Check 16:10 and 16:9 crops, blurred backdrops and partial window coverage.
Inspect both splash motifs in Omarchy's real password-prompt layout. Verify
exactly two wallpapers in the staged switcher. Keep rejected iterations in
local state backups, outside the theme. Do not rebuild initramfs for previews.
