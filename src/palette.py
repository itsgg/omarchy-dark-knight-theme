#!/usr/bin/env python3
"""Derive colors.toml from the wallpaper this theme is worn with.

    python3 src/palette.py backgrounds/<wallpaper>.jpg > colors.toml

The first palette for this theme was ported from the itsgg.com design system,
where the accent is gold and the greys are near-neutral. Worn over the Batman
wallpaper it did not hold, and the reason is measurable rather than a matter of
taste. Quantised to sixteen buckets that image is monochromatic: every colour
that occupies any real area sits at hue 200 to 210, saturation falls from 32%
in the shadows to 13% at the highlight, and lightness runs 6% to 61%. Warm
pixels are 0.07% of it.

An image built on one hue gives a theme two honest choices: match it, or fight
it. This matches it. Every structural colour is that hue, hierarchy is carried
by lightness alone, and saturation falls as lightness rises exactly as it does
in the photograph. Nothing is imported.

Gold survives, at the share it actually has in the picture. It is no longer the
accent; it is the warning colour, which is the one job where a hue foreign to
everything around it is the point rather than the problem.

The accent is not a different hue either. It is the same hue with the
saturation turned up, which is the one axis the image leaves unused: the
photograph never exceeds 32% saturation, so 52% at a high lightness reads as
unmistakably deliberate while still being the same colour as everything else.
"""

import colorsys
import math
import re
import subprocess
import sys

USAGE = "usage: palette.py <wallpaper> > colors.toml"


def sample(path, buckets=16):
    """The image as (share, hue, saturation, lightness), largest share first."""
    try:
        out = subprocess.run(
        # -depth 8, or a Q16 build prints #RRRRGGGGBBBB and taking the first
            # six digits reads the wrong channel boundaries.
            ["magick", path, "-resize", "300x300", "-colors", str(buckets),
             "-depth", "8", "-format", "%c", "histogram:info:"],
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise SystemExit(f"palette: could not read {path} as an image ({e})")
    rows = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "#" not in line:
            continue
        try:
            n = int(line.split(":")[0])
        except ValueError:
            continue
        hx = line.split("#")[1].split()[0]
        if len(hx) != 6:
            continue
        r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        rows.append((n, h * 360, s * 100, l * 100))
    if not rows:
        raise SystemExit(f"palette: nothing parsed from {path}; is it an image?")
    total = sum(r[0] for r in rows)
    return [(n / total, h, s, l) for n, h, s, l in sorted(rows, key=lambda r: -r[0])]


def axis(rows):
    """The hue the image is built on, and how saturation falls as it lightens.

    Weighted by share, and only over samples with enough saturation to carry a
    hue: a near-black pixel has a hue, but it is noise.
    """
    lit = [(w, h, s, l) for w, h, s, l in rows if s > 5]
    if not lit:
        raise SystemExit(
            "palette: this image has no colour to build on (nothing above 5% "
            "saturation). A theme derived from it would be pure grey; pick a "
            "wallpaper with a hue, or write colors.toml by hand.")
    # Hue is circular: an arithmetic mean of 359 and 1 gives 180, which is the
    # opposite colour. Averaged as unit vectors instead.
    x = sum(w * math.cos(math.radians(h)) for w, h, _, _ in lit)
    y = sum(w * math.sin(math.radians(h)) for w, h, _, _ in lit)
    hue = math.degrees(math.atan2(y, x)) % 360
    # Saturation against lightness, as a straight line through the samples.
    n = sum(w for w, *_ in lit)
    ml = sum(w * l for w, _, _, l in lit) / n
    ms = sum(w * s for w, _, s, _ in lit) / n
    var = sum(w * (l - ml) ** 2 for w, _, _, l in lit)
    cov = sum(w * (l - ml) * (s - ms) for w, _, s, l in lit)
    slope = cov / var if var else 0.0
    return hue, slope, ms - slope * ml


def hexof(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, max(0.0, min(1.0, l / 100)),
                                  max(0.0, min(1.0, s / 100)))
    return "#{:02X}{:02X}{:02X}".format(*(round(c * 255) for c in (r, g, b)))


def ramp(hue, slope, intercept, lightness):
    """One step of the structural ramp: the image's own saturation at that lightness."""
    return hexof(hue, max(6.0, slope * lightness + intercept), lightness)


def relative_luminance(hx):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hx.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    ya, yb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(ya, yb), min(ya, yb)
    return (hi + 0.05) / (lo + 0.05)


def lab(hx):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(hx.lstrip("#")[i:i + 2], 16)) for i in (0, 2, 4))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def distance(a, b):
    """CIE76. Rough, and enough to answer "can these two be told apart"."""
    la, lb = lab(a), lab(b)
    return sum((u - v) ** 2 for u, v in zip(la, lb)) ** 0.5


def composite(fg, bg, alpha):
    """fg over bg at alpha, which is what a fill actually looks like."""
    f = [int(fg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(bg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(alpha * f[i] + (1 - alpha) * b[i]):02X}" for i in range(3))


def raise_until(make, start, ok, limit=99.0):
    """The lowest lightness at or above `start` that satisfies `ok`.

    Every floor in this file is expressed this way rather than by writing a
    lightness down, so a palette generated from a different wallpaper still
    meets it. Hand-picked lightnesses were how `muted` came out at 2.89:1 on
    an elevated surface, below the 3:1 that any UI element needs, in a key
    Omarchy's templates use 160 times.
    """
    l = start
    while l <= limit:
        c = make(l)
        if ok(c):
            return c
        l += 0.5
    # Returning make(limit) here would hand back a colour known to fail its
    # own floor and leave the audit to catch it, which is the shape of bug
    # this whole file exists to stop.
    raise SystemExit(
        f"palette: no lightness between {start} and {limit} satisfies the "
        "floor. The ground is probably too light for this constraint; "
        "change the floor deliberately rather than shipping a colour that "
        "misses it.")


def build(path):
    rows = sample(path)
    hue, slope, intercept = axis(rows)
    warm = sum(w for w, h, s, _ in rows if (h < 70 or h > 320) and s > 8)

    # Ground: below the image's own dominant, so a window sits on the picture
    # rather than being cut out of it.
    p = {
        "darker_background":  ramp(hue, slope, intercept, 2.5),
        "dark_background":    ramp(hue, slope, intercept, 4.0),
        "background":         ramp(hue, slope, intercept, 6.0),
        "lighter_background": ramp(hue, slope, intercept, 12.0),
        "line":               ramp(hue, slope, intercept, 21.0),
        "light_foreground":   ramp(hue, slope, intercept, 66.0),
        # Above anything in the photograph, because text sits on top of it.
        "foreground":         ramp(hue, slope, intercept, 81.0),
        "bright_foreground":  ramp(hue, slope, intercept, 93.0),
    }
    p["cursor"] = p["foreground"]

    # `muted` is the second most-used key in Omarchy's templates and lands on
    # elevated surfaces and selected rows as well as on the base, so its floor
    # is 3:1 against the lightest of them rather than against the base.
    p["muted"] = raise_until(
        lambda l: ramp(hue, slope, intercept, l), 40.0,
        lambda c: contrast(c, p["lighter_background"]) >= 3.0)

    # The accent: the same hue, on the axis the image never uses. The
    # photograph peaks at 32% saturation, so this is recognisably deliberate
    # and cannot read as foreign.
    p["accent"] = hexof(hue - 4, 52, 62)
    # Exported rather than a local, so the preview's card border and the window
    # border are the same two colours by construction. It was a local once, the
    # preview repeated its value as a literal, and the two drifted apart the
    # first time the accent moved.
    p["accent_dim"] = hexof(hue - 4, 44, 42)
    p["selection"] = hexof(hue - 4, 30, 16)
    p["selection_background"] = p["selection"]
    # And against the selected row, which is lighter still once the accent
    # fill is composited over it.
    sel_fill = composite(p["accent"], p["background"], 0.16)
    p["muted"] = raise_until(
        lambda l: ramp(hue, slope, intercept, l), 40.0,
        lambda c: contrast(c, p["lighter_background"]) >= 3.0
        and contrast(c, p["selection"]) >= 3.0
        and contrast(c, sel_fill) >= 3.0)
    # dark_foreground is text, not chrome, so its floor is 4.5:1 and it is
    # the same three surfaces. At the hand-picked L52 it read 4.49, 3.89 and
    # 4.05, which is the kind of miss that only a check finds.
    p["dark_foreground"] = raise_until(
        lambda l: ramp(hue, slope, intercept, l), 52.0,
        lambda c: contrast(c, p["lighter_background"]) >= 4.5
        and contrast(c, p["selection"]) >= 4.5
        and contrast(c, sel_fill) >= 4.5)
    p["selection_foreground"] = p["bright_foreground"]

    # Borders. Active runs bright to dark along the accent so a 2px line reads
    # as a bevel; inactive is the image's own mid tone.
    p["hyprland_active_border"] = f'rgba({p["accent"][1:]}ee) rgba({p["accent_dim"][1:]}ee) 45deg'
    p["hyprland_inactive_border"] = f'rgba({p["line"][1:]}cc)'

    # Semantic and ANSI. Held to the lightness band the steel occupies and to
    # roughly the saturation the image tops out at, so nothing shouts louder
    # than the picture. Gold is the warning, which is the one place a hue
    # foreign to everything else is doing its job.
    # Gold, at the design system's own hue (46 degrees, --gold-500) but held
    # to the family's saturation band. The literal #C9A227 sits at 68%
    # saturation and 47% lightness, where the rest of the ANSI set is 20 to
    # 38% and 56 to 62%: it was both louder than the accent and darker than
    # its neighbours, so terminal yellow shouted over the focus colour while
    # appearing far more often. The hue is what makes gold read as foreign,
    # which is the whole job of a warning; the saturation was only making it
    # shout.
    p["yellow"] = hexof(46, 40, 58)
    p["red"] = hexof(6, 34, 56)
    p["green"] = hexof(140, 20, 60)
    p["orange"] = hexof(32, 38, 58)
    # Far enough from blue to be a different colour. It was 188 degrees and
    # came out at CIE76 13.3 from blue, which is close enough to confuse.
    p["cyan"] = raise_until(
        lambda l: hexof(178, 30, l), 58.0,
        lambda c: distance(c, hexof(hue, 30, 58)) >= 18.0)
    p["blue"] = hexof(hue, 30, 58)
    p["magenta"] = hexof(280, 20, 62)
    p["brown"] = hexof(28, 22, 40)
    # A bright slot that cannot be told from its normal slot is a wasted slot.
    # Written as a floor rather than as a lightness, because at these
    # saturations a fixed ten-point step is not enough for every hue: green and
    # cyan came out at CIE76 9.3 and 8.9, which is inside the range where two
    # terminal colours read as the same one.
    for slot, (h, s) in {"red": (6, 40), "green": (140, 24), "cyan": (178, 30),
                         "blue": (hue, 32), "magenta": (280, 24)}.items():
        p["bright_" + slot] = raise_until(
            lambda l, h=h, s=s: hexof(h, s, l), 64.0,
            lambda c, slot=slot: distance(c, p[slot]) >= 14.0)
    p["bright_yellow"] = raise_until(
        lambda l: hexof(46, 40, l), 64.0,
        lambda c: distance(c, p["yellow"]) >= 14.0)

    ansi = ["background", "red", "green", "yellow", "blue", "magenta", "cyan",
            "foreground", "line", "bright_red", "bright_green", "bright_yellow",
            "bright_blue", "bright_magenta", "bright_cyan", "bright_foreground"]
    return p, ansi, hue, slope, intercept, warm


# The three forms a value in this file may take: a hex colour, a single
# Hyprland rgba, or a two-stop Hyprland gradient.
VALUE = re.compile(
    r"^(#[0-9A-Fa-f]{6}"
    r"|rgba\([0-9A-Fa-f]{8}\)"
    r"|rgba\([0-9A-Fa-f]{8}\) rgba\([0-9A-Fa-f]{8}\) \d{1,3}deg)$")


def emit(p, ansi, hue, slope, intercept, warm, path):
    bg = p["background"]
    w = sys.stdout.write
    # Every value is written between quotes into TOML, so every value is
    # checked to be a colour first. Nothing here takes user input today; this
    # is so that stays true if something later does.
    for k, v in p.items():
        # fullmatch, not match: `$` also matches before a final newline, so a
        # value ending in one would pass and then break the quoted TOML.
        if not VALUE.fullmatch(v):
            raise SystemExit(f"palette: {k} is not a colour or gradient: {v!r}")
    # And the path goes into a comment, so it must not be able to leave one.
    path = " ".join(str(path).split())
    w("# Dark Knight: one hue, carried by light.\n#\n")
    w(f"# Generated by src/palette.py from {path}.\n")
    w("# Do not hand-edit: change the script, or change the wallpaper and re-run it.\n#\n")
    w("# Quantised to sixteen buckets, that image is monochromatic. Measured:\n")
    w(f"#   hue          {hue:.0f} degrees, weighted over every sample with real saturation\n")
    w(f"#   saturation   falls {abs(slope):.2f} points per point of lightness\n")
    w(f"#                (about {intercept:.0f}% at black, {slope*61+intercept:.0f}% at the highlight)\n")
    w(f"#   warm pixels  {100*warm:.2f}% of the image\n#\n")
    w("# So every structural colour below is that one hue, with the image's own\n")
    w("# saturation for its lightness. Hierarchy is carried by lightness alone,\n")
    w("# which is how the photograph is built. Nothing is imported.\n#\n")
    w("# The accent is the same hue with saturation turned up to 52%, the one\n")
    w("# axis the photograph leaves unused: it never exceeds 32%, so the accent\n")
    w("# reads as deliberate while remaining the same colour as everything else.\n#\n")
    w("# Gold is not the accent any more. It is the warning colour, and it gets\n")
    w("# roughly the share of the screen it has in the picture. A warm hue is\n")
    w("# doing its job when it is foreign to everything around it; that is what\n")
    w("# a warning is, and it is not what a window frame is.\n\n")
    w('mode = "dark"\n\n')

    def block(title, keys):
        w(f"# {title}\n")
        for k in keys:
            v = p[k]
            if v.startswith("#") and k not in ("hyprland_active_border", "hyprland_inactive_border"):
                w(f'{k:24} = "{v}"  # contrast {contrast(v, bg):5.2f}:1 on the base\n')
            else:
                w(f'{k:24} = "{v}"\n')
        w("\n")

    block("Ground, from the image's shadows down.",
          ["background", "dark_background", "darker_background", "lighter_background"])
    block("Structure and text, up the same ramp. Body text needs 4.5:1, UI 3:1.",
          ["line", "muted", "dark_foreground", "light_foreground", "foreground",
           "bright_foreground", "cursor"])
    block("The accent, and what it paints.",
          ["accent", "accent_dim", "selection", "selection_background",
           "selection_foreground"])
    w("# Window borders.\n")
    w(f'hyprland_active_border   = "{p["hyprland_active_border"]}"\n')
    w(f'hyprland_inactive_border = "{p["hyprland_inactive_border"]}"\n\n')
    block("Semantic and ANSI. Gold is the warning.",
          ["red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown"])
    block("Bright variants.",
          ["bright_red", "bright_yellow", "bright_green", "bright_cyan",
           "bright_blue", "bright_magenta"])
    w("# The 16 slots, for anything reading them directly.\n")
    for i, k in enumerate(ansi):
        w(f'color{i:<2} = "{p[k]}"\n')


def audit(p):
    """Every floor this file claims, checked against what it produced.

    On stderr and with a non-zero exit, so `palette.py ... > colors.toml`
    still writes the file and still tells you it is wrong. These are the
    faults a review found on 2026-09-04, each now a check rather than a
    memory: muted below 3:1 on elevated surfaces, bright slots that could not
    be told from their normal slots, and cyan sitting on top of blue.
    """
    bad = []
    sel_fill = composite(p["accent"], p["background"], 0.16)
    grounds = {"base": p["background"], "elevated": p["lighter_background"],
               "selection": p["selection"], "selected row": sel_fill}
    for name, g in grounds.items():
        for key, floor in (("foreground", 4.5), ("light_foreground", 4.5),
                           ("dark_foreground", 4.5), ("muted", 3.0),
                           ("accent", 3.0)):
            c = contrast(p[key], g)
            if c < floor:
                bad.append(f"{key} on {name}: {c:.2f}:1, floor {floor}")
    for slot in ("red", "green", "cyan", "blue", "magenta", "yellow"):
        d = distance(p[slot], p["bright_" + slot])
        if d < 14.0:
            bad.append(f"bright_{slot} is CIE76 {d:.1f} from {slot}, floor 14")
    for a, b, floor in (("blue", "cyan", 18.0), ("green", "cyan", 14.0),
                        ("red", "green", 25.0),
                        ("yellow", "accent", 25.0), ("accent", "foreground", 20.0)):
        d = distance(p[a], p[b])
        if d < floor:
            bad.append(f"{a} and {b} are CIE76 {d:.1f} apart, floor {floor}")
    if distance(p["line"], p["background"]) < 12.0:
        bad.append("line is invisible against the base")
    # The accent is the loudest colour or it is not the accent. Terminal
    # yellow was at 68% saturation against an accent at 52% and a family at
    # 20 to 38%, so the warning colour outshouted the focus colour on every
    # screen that had both.
    def sat(hx):
        import colorsys
        r, g, b = (int(hx.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return colorsys.rgb_to_hls(r, g, b)[2] * 100
    ceiling = sat(p["accent"])
    for slot in ("red", "green", "yellow", "blue", "magenta", "cyan", "orange",
                 "bright_red", "bright_green", "bright_yellow", "bright_blue",
                 "bright_magenta", "bright_cyan"):
        if sat(p[slot]) > ceiling:
            bad.append(f"{slot} is more saturated than the accent "
                       f"({sat(p[slot]):.0f}% against {ceiling:.0f}%)")
    for line in bad:
        print(f"palette: {line}", file=sys.stderr)
    return len(bad)


if __name__ == "__main__":
    # No default. The relative one here pointed outside the repository when
    # run from the root, as the docstring told you to, and silently truncated
    # colors.toml through the redirection before failing.
    if len(sys.argv) != 2:
        raise SystemExit(USAGE)
    path = sys.argv[1]
    built = build(path)
    emit(*built, path)
    failures = audit(built[0])
    if failures:
        print(f"palette: {failures} floor(s) not met", file=sys.stderr)
    sys.exit(1 if failures else 0)
