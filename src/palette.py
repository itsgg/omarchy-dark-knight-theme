#!/usr/bin/env python3
"""Derive colors.toml from a photograph's measurements.

    python3 src/palette.py > colors.toml                 # the recorded image
    python3 src/palette.py <wallpaper>.jpg > colors.toml # measure another

The photograph this theme was measured from is no longer in the repository:
it was a film still, not ours to ship, and the wallpapers are all generated
now. What the theme needs from it is six numbers, and they are recorded below
as MEASURED, so the palette is still derived rather than picked and still
reproducible without the file. Given an image, the script measures that one
instead.

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

The accent is not a different hue either, and it is not a louder one. It was,
twice: gold, then the image's hue at 2.4 times the image's peak chroma. Both
read as a second theme laid over the first, and on 2026-09-17 the accent was
taken down to steel by hand, in colors.toml, which this script then silently
disagreed with. The decision lives here now. Steel, at the image's own chroma,
is what fills. The accent is marked by lightness first; it does carry more
chroma than anything in the image (19 against a peak of 13 for the recorded
photograph), because at steel's chroma it could not be told from the text
greys, but only as much as that takes and never more than the ANSI set.
"""

import colorsys
import math
import re
import subprocess
import sys

USAGE = "usage: palette.py [wallpaper] > colors.toml"

# backgrounds/0-batman-dark-knight-portrait.jpg, as measured by measure() on
# 2026-09-19, the day before it left the repository (it is in the history up
# to then): HLS hue, the slope and intercept of saturation against lightness,
# the share of warm pixels, the hue in Lab, and the peak chroma.
MEASURED = (203.05949533310115, -0.38402388257615666, 33.751225228248856,
            0.0007495069033530572, 248.78767155775904, 13.147585087665682)
SOURCE = "a recorded photograph (see MEASURED in src/palette.py)"


def sample(path, buckets=16):
    """The image as (share, hex, hue, saturation, lightness), largest share first."""
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
        rows.append((n, hx, h * 360, s * 100, l * 100))
    if not rows:
        raise SystemExit(f"palette: nothing parsed from {path}; is it an image?")
    total = sum(r[0] for r in rows)
    return [(n / total, hx, h, s, l)
            for n, hx, h, s, l in sorted(rows, key=lambda r: -r[0])]


def axis(rows):
    """The hue the image is built on, and how saturation falls as it lightens.

    Weighted by share, and only over samples with enough saturation to carry a
    hue: a near-black pixel has a hue, but it is noise.
    """
    lit = [(w, h, s, l) for w, _, h, s, l in rows if s > 5]
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


def lab_hue(rows):
    """The image's hue in Lab, which is not the same angle as its hue in HLS.

    Placing the accent at the HLS hue but in Lab space turned an ice blue into
    a teal. The ramp is still built with HLS because it is a straight lightness
    ladder; anything colourful is placed in Lab, so its hue is measured there.
    """
    lit = [(w, hx) for w, hx, _, _, _ in rows if chroma_of(hx) > 3]
    if not lit:
        raise SystemExit("palette: this image has no colour to build on")
    x = y = 0.0
    for w, hx in lit:
        _, a, b = lab(hx)
        h = math.atan2(b, a)
        x += w * math.cos(h)
        y += w * math.sin(h)
    return math.degrees(math.atan2(y, x)) % 360


def hexof(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, max(0.0, min(1.0, l / 100)),
                                  max(0.0, min(1.0, s / 100)))
    return "#{:02X}{:02X}{:02X}".format(*(round(c * 255) for c in (r, g, b)))


def ramp(hue, slope, intercept, lightness):
    """One step of the structural ramp: the image's own saturation at that
    lightness, and never under 6%, below which the hue stops reading at all."""
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


def _from_lin(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def lch(light, chroma, hue_deg, _shrink=0.995):
    """An sRGB colour at a given lightness, chroma and hue.

    Chroma is perceptual; HLS saturation is not. Equalising the ANSI set on
    HLS saturation put green, magenta and cyan at the same number as blue and
    they read twice as colourful, so the terminal palette looked like a
    different theme from the interface around it. Everything colourful here is
    now placed by chroma instead, which is what makes one hue read as loud as
    another.

    Out-of-gamut requests are answered by walking the chroma down rather than
    by clipping the channels, because clipping shifts the hue.
    """
    if not 0 <= light <= 100:
        raise SystemExit(f"palette: lightness {light} is outside 0 to 100")
    # Zero chroma is a grey, not a failure. The loop below never ran for it and
    # the function returned black for every achromatic request.
    floor = 1e-4
    while True:
        h = math.radians(hue_deg)
        a, b = chroma * math.cos(h), chroma * math.sin(h)
        fy = (light + 16) / 116
        fx, fz = fy + a / 500, fy - b / 200
        f = lambda v: v ** 3 if v ** 3 > 0.008856 else (v - 16 / 116) / 7.787
        x, y, z = f(fx) * 0.95047, f(fy), f(fz) * 1.08883
        r = 3.2406 * x - 1.5372 * y - 0.4986 * z
        g = -0.9689 * x + 1.8758 * y + 0.0415 * z
        bl = 0.0557 * x - 0.2040 * y + 1.0570 * z
        if all(-0.001 <= v <= 1.001 for v in (r, g, bl)):
            return "#{:02X}{:02X}{:02X}".format(
                *(round(_from_lin(v) * 255) for v in (r, g, bl)))
        if chroma <= floor:
            # Walking chroma down cannot reach the gamut, which means the
            # lightness itself is unreachable. Returning black here would be a
            # wrong colour presented as an answer; without a floor the shrink
            # runs into subnormal floats and never terminates.
            raise SystemExit(
                f"palette: no sRGB colour at lightness {light} and hue "
                f"{hue_deg}, at any chroma")
        chroma *= _shrink


def chroma_of(hx):
    _, a, b = lab(hx)
    return (a * a + b * b) ** 0.5


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
    return raise_until_at(make, start, ok, limit)[0]


def raise_until_at(make, start, ok, limit=99.0):
    """raise_until, and the lightness it stopped at, for a caller that has to
    come back and carry on from there."""
    l = start
    while l <= limit:
        c = make(l)
        if ok(c):
            return c, l
        l += 0.5
    # Returning make(limit) here would hand back a colour known to fail its
    # own floor and leave the audit to catch it, which is the shape of bug
    # this whole file exists to stop.
    raise SystemExit(
        f"palette: no lightness between {start} and {limit} satisfies the "
        "floor. The ground is probably too light for this constraint; "
        "change the floor deliberately rather than shipping a colour that "
        "misses it.")


# Perceptual chroma, not HLS saturation, and measured rather than asserted.
# Both of these were fixed numbers once, which meant a vivid wallpaper would
# have got the same quiet accent as a near-monochrome one. They are multiples
# of the image's own peak chroma now, so the theme is as colourful as the
# picture warrants. Steel is the image's chroma, not past it, and it is what
# fills: the selection, the dim accent. The ANSI set is the most colourful
# thing in the theme, because a terminal's red has to be told from its green.
#
# The accent is carried by light, like everything else here. At steel's
# chroma and L66 it sat CIE76 7 from light_foreground and 7 from
# dark_foreground, so focus, the selected row and a link were three greys
# among the text greys and nothing on the screen said "here". It is lifted to
# L76 and given only as much chroma as it takes to stand off the text ramp
# (ACCENT_APART, found rather than written down), never more than the ANSI
# set.
#
# The window border is the same colour, lower: L62. It was tried further up
# the road first, near-white at L92 after Omarchy's lumon, and on a ground at
# 6% lightness that was 14:1, above the body text's 12:1, so the frame
# outranked what it framed and haloed on a dark screen. lumon's ground is
# three times lighter, which is why it works there. A border has to be found,
# not read: 3:1 on the ground, unmistakable beside the inactive one, and
# darker than light_foreground, so it never outranks body text. It is not
# under every text step: dark_foreground, the dimmest, sits a shade below it.
STEEL_OVER_IMAGE = 0.83
ANSI_OVER_IMAGE = 1.75
ACCENT_LIGHT = 76.0
ACCENT_APART = 16.0
BORDER_LIGHT = 62.0
ANSI_LIGHT = 62.0


def measure(path):
    """The six numbers the palette is built from, off an image."""
    rows = sample(path)
    hue, slope, intercept = axis(rows)
    warm = sum(w for w, _, h, s, _ in rows if (h < 70 or h > 320) and s > 8)
    return (hue, slope, intercept, warm, lab_hue(rows),
            max(chroma_of(hx) for _, hx, _, _, _ in rows))


def build(measured):
    hue, slope, intercept, warm, accent_hue, peak_chroma = measured
    steel_chroma = peak_chroma * STEEL_OVER_IMAGE
    ansi_chroma = peak_chroma * ANSI_OVER_IMAGE

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

    # Steel: the same hue, at the image's own colourfulness. The fills.
    # accent_dim is exported rather than a local, so the preview's card border
    # and the scope guides are the same colour by construction. It was a local
    # once, the preview repeated its value as a literal, and the two drifted
    # apart the first time the accent moved.
    p["accent_dim"] = lch(45, steel_chroma, accent_hue)
    p["selection"] = lch(18, steel_chroma * 0.67, accent_hue)
    p["selection_background"] = p["selection"]
    # The text ramp's floors and the accent need each other. muted and
    # dark_foreground have to clear the selected row, which is the accent
    # composited over the ground; the accent has to stand off the text ramp,
    # which includes dark_foreground. So they are settled together: place the
    # floors against the current accent, place the accent against those
    # floors, and stop when the accent stops moving.
    #
    # The floors only ever go up. Each round starts from the lightness the
    # last one reached rather than from the bottom, because resetting them let
    # the two chase each other: a reviewer found an image where the accent
    # swapped between #93C993 and #94C893 for ever, each nudging
    # dark_foreground across the 4.5:1 line and back, while the second pairing
    # was valid all along. Going up only, the ramp can move a bounded number of
    # half-steps; once it holds still the accent, which depends on nothing
    # else, is the one the floors were just measured against.
    #
    # This was one pass once, with the row estimated from the accent at its
    # chroma ceiling on the theory that that was the lightest it could be. It
    # is not: composite() mixes gamma-encoded channels, so more chroma at one
    # Lab lightness can make the fill darker. Two reviewers found palettes
    # where the floors passed the estimate and failed the real row at audit
    # (4.5032 against 4.4799), and others where the estimate raised the text
    # for nothing.
    text = ("foreground", "light_foreground", "dark_foreground")
    # From below. The first round has no accent yet and so no selected row to
    # clear: the floors start at the lowest they could possibly be, and every
    # later round measures them against a real accent's row and raises them
    # only if that row demands it. Starting from a guessed accent instead (its
    # chroma ceiling, in an earlier version) could leave them higher than the
    # accent finally chosen needs, and going up only, they never came back.
    p.pop("accent", None)
    muted_from, dark_from = 40.0, 52.0
    for _ in range(300):
        sel_fill = (composite(p["accent"], p["background"], 0.16)
                    if "accent" in p else p["background"])
        # 4.5:1 on the base. muted is chrome on the raised surfaces, but on
        # the base it is every comment and every line number in the editor,
        # and those are read, not glanced at. At 3.95:1 a commented-out block
        # was the hardest text on the screen.
        p["muted"], muted_from = raise_until_at(
            lambda l: ramp(hue, slope, intercept, l), muted_from,
            lambda c: contrast(c, p["background"]) >= 4.5
            and contrast(c, p["lighter_background"]) >= 3.0
            and contrast(c, p["selection"]) >= 3.0
            and contrast(c, sel_fill) >= 3.0)
        # dark_foreground is text, not chrome, so its floor is 4.5:1 on the
        # same three surfaces. At the hand-picked L52 it read 4.49, 3.89 and
        # 4.05, which is the kind of miss that only a check finds.
        p["dark_foreground"], dark_from = raise_until_at(
            lambda l: ramp(hue, slope, intercept, l), dark_from,
            lambda c: contrast(c, p["lighter_background"]) >= 4.5
            and contrast(c, p["selection"]) >= 4.5
            and contrast(c, sel_fill) >= 4.5)

        # The accent: the least chroma that stands ACCENT_APART off every
        # step of the text ramp it appears beside, and never past the ANSI
        # set.
        previous, chroma = p.get("accent"), steel_chroma
        while True:
            p["accent"] = lch(ACCENT_LIGHT, chroma, accent_hue)
            if all(distance(p["accent"], p[k]) >= ACCENT_APART for k in text):
                break
            if chroma >= ansi_chroma:
                raise SystemExit(
                    f"palette: no accent at L{ACCENT_LIGHT:.0f} stands CIE76 "
                    f"{ACCENT_APART:.0f} off the text ramp without passing the "
                    "ANSI set's chroma. Move ACCENT_LIGHT rather than shipping "
                    "an accent that reads as text.")
            chroma = min(ansi_chroma, chroma + 0.25)
        if p["accent"] == previous:
            break
    else:
        raise SystemExit(
            "palette: the text floors and the accent did not settle. They "
            "only move one way, so this should be unreachable; it is a bug "
            "in build(), not a property of the image.")
    p["selection_foreground"] = p["bright_foreground"]
    p["active_border"] = lch(BORDER_LIGHT, chroma, accent_hue)

    # Borders. Active is solid, the accent's colour and darker than body
    # text; inactive is the image's own mid tone. The active border was a 45
    # degree gradient to accent_dim once, and on a 2px line the dark half read
    # as a missing border.
    p["hyprland_active_border"] = f'rgba({p["active_border"][1:]}ee)'
    p["hyprland_inactive_border"] = f'rgba({p["line"][1:]}cc)'

    # Semantic and ANSI.
    #
    # The photograph is one hue, so red and green are not in it and cannot be.
    # A terminal needs them anyway. The honest way to derive them from an image
    # that does not contain them is to let the image set the envelope rather
    # than the hue: it decides how saturated anything may be and how light,
    # and the hues are then placed at the widest mutual separation inside that
    # envelope.
    #
    # The ceiling is the image's own peak chroma, lifted so these read as
    # interface rather than as part of the photograph, and one ceiling for all
    # of them. An earlier palette put gold at 68% saturation against a family
    # at 20 to 38%, and terminal yellow outshouted everything on every screen
    # that had it.
    # Hue anchors, far apart and still recognisable as the colour their slot
    # is named after. Nothing here is borrowed from a design system; the
    # numbers are only positions on the wheel, and they are placed at one
    # perceptual chroma so no hue is louder than another.
    #
    # Terminal blue does not sit on the image's hue. That is the accent's, and
    # putting blue there too made the two CIE76 6.9 apart, separated only by
    # colourfulness, on screens that show both constantly. Cyan moves off blue
    # for the same reason.
    #
    # Blue was at 288 to get clear of the accent, and CIELAB bends blue toward
    # purple as it goes round, so 288 came out violet: #8E93BC, 18 from
    # magenta. The accent has since moved up to L76, which separates the two
    # by lightness, so blue can come back to 272 and be blue. It stands 17
    # from the accent, 27 from cyan and 24 from magenta there.
    ANCHORS = {"red": 15, "orange": 55, "yellow": 95, "green": 145,
               "cyan": 200, "blue": 272, "magenta": 335, "brown": 60}
    for slot, h in ANCHORS.items():
        if slot == "brown":
            p[slot] = lch(40.0, ansi_chroma * 0.8, h)
        else:
            p[slot] = lch(ANSI_LIGHT, ansi_chroma, h)
    # Bright slots are the same hue and chroma, raised in lightness until they
    # can actually be told from their normal counterpart. A floor rather than a
    # fixed step, because at one chroma a fixed step is not enough for every
    # hue: green and cyan once came out at CIE76 9.3 and 8.9, inside the range
    # where two terminal colours read as one.
    for slot in ("red", "yellow", "green", "cyan", "blue", "magenta"):
        h = ANCHORS[slot]
        p["bright_" + slot] = raise_until(
            lambda l, h=h: lch(l, ansi_chroma, h), ANSI_LIGHT + 2,
            lambda c, slot=slot: distance(c, p[slot]) >= 14.0)

    # Slot 8 is muted, not line. Omarchy's terminal templates put muted there
    # themselves, so this only reaches whatever reads colorN directly, but at
    # line's 1.6:1 that reader drew its dim text invisible: slot 8 is what
    # zsh-autosuggestions, fish hints and eza's dim columns are written in.
    ansi = ["background", "red", "green", "yellow", "blue", "magenta", "cyan",
            "foreground", "muted", "bright_red", "bright_green", "bright_yellow",
            "bright_blue", "bright_magenta", "bright_cyan", "bright_foreground"]
    return p, ansi, hue, slope, intercept, warm, peak_chroma


# The three forms a value in this file may take: a hex colour, a single
# Hyprland rgba, or a two-stop Hyprland gradient.
VALUE = re.compile(
    r"^(#[0-9A-Fa-f]{6}"
    r"|rgba\([0-9A-Fa-f]{8}\)"
    r"|rgba\([0-9A-Fa-f]{8}\) rgba\([0-9A-Fa-f]{8}\) \d{1,3}deg)$")


def emit(p, ansi, hue, slope, intercept, warm, peak, path):
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
    w(f"#   peak chroma  {peak:.1f}, the most colourful thing in the image\n#\n")
    w("# The accent is the image's own hue, measured in Lab because that is where\n")
    w(f"# it is placed. Steel, the fills, sits at chroma {peak * STEEL_OVER_IMAGE:.0f} or under: inside the\n")
    w("# photograph's own range. The accent is marked by lightness first, with\n")
    w(f"# only the chroma ({chroma_of(p['accent']):.0f}) it takes to stand off the text ramp, and the\n")
    w("# active window border is that colour again, darker than body text.\n#\n")
    w("# A monochrome photograph has no red and no green and a terminal needs\n")
    w("# them anyway, so the image sets the envelope rather than the hue. It\n")
    w(f"# fixes how colourful anything may be (chroma {peak * ANSI_OVER_IMAGE:.0f} for the ANSI set)\n")
    w("# while their lightness is fixed; the hues are then positions on the\n")
    w("# wheel, spaced far enough apart that the audit's distance floors pass.\n")
    w("# There is no gold and no imported accent.\n\n")
    w('mode = "dark"\n\n')

    def block(title, keys):
        w(f"# {title}\n")
        for k in keys:
            w(f'{k:24} = "{p[k]}"\n')
        w("\n")

    block("Ground, from the image's shadows down.",
          ["background", "dark_background", "darker_background", "lighter_background"])
    block("Structure and text, up the same ramp. Body text needs 4.5:1, UI 3:1.",
          ["line", "muted", "dark_foreground", "light_foreground", "foreground",
           "bright_foreground", "cursor"])
    block("The accent, and what it paints.",
          ["accent", "accent_dim", "active_border", "selection",
           "selection_background", "selection_foreground"])
    w("# Window borders.\n")
    w(f'hyprland_active_border   = "{p["hyprland_active_border"]}"\n')
    w(f'hyprland_inactive_border = "{p["hyprland_inactive_border"]}"\n\n')
    block("Semantic and ANSI. Yellow is the warning.",
          ["red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown"])
    block("Bright variants.",
          ["bright_red", "bright_yellow", "bright_green", "bright_cyan",
           "bright_blue", "bright_magenta"])
    w("# The 16 slots, for anything reading them directly.\n")
    for i, k in enumerate(ansi):
        w(f'color{i:<2} = "{p[k]}"\n')


def audit(p, ceiling=None):
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
                           ("dark_foreground", 4.5),
                           ("muted", 4.5 if name == "base" else 3.0),
                           ("accent", 3.0)):
            c = contrast(p[key], g)
            if c < floor:
                bad.append(f"{key} on {name}: {c:.2f}:1, floor {floor}")
    for slot in ("red", "green", "cyan", "blue", "magenta", "yellow"):
        d = distance(p[slot], p["bright_" + slot])
        if d < 14.0:
            bad.append(f"bright_{slot} is CIE76 {d:.1f} from {slot}, floor 14")
    for a, b, floor in (("blue", "cyan", 18.0), ("green", "cyan", 14.0),
                        # The accent and terminal blue both sit at the image's
                        # hue and appear on the same screen constantly, so they
                        # have to be separable too.
                        ("accent", "blue", 12.0),
                        # Warm neighbours, which sit closest of any pair here:
                        # red and orange were CIE76 12.4 apart at 25 and 55.
                        ("red", "orange", 14.0), ("orange", "yellow", 14.0),
                        ("red", "green", 25.0),
                        ("yellow", "accent", 25.0),
                        # The accent beside each step of the text ramp: at 7
                        # it was a grey among greys.
                        ("accent", "foreground", ACCENT_APART),
                        ("accent", "light_foreground", ACCENT_APART),
                        ("accent", "dark_foreground", ACCENT_APART)):
        d = distance(p[a], p[b])
        if d < floor:
            bad.append(f"{a} and {b} are CIE76 {d:.1f} apart, floor {floor}")
    # The frame never outranks what it frames, is still a UI element on the
    # ground, and cannot be mistaken for the inactive border.
    if relative_luminance(p["active_border"]) >= relative_luminance(p["light_foreground"]):
        bad.append("active_border is as light as the text it frames")
    if contrast(p["active_border"], p["background"]) < 3.0:
        bad.append("active_border is under 3:1 on the base")
    if distance(p["active_border"], p["line"]) < 30.0:
        bad.append("active_border is too close to the inactive border")
    if distance(p["line"], p["background"]) < 12.0:
        bad.append("line is invisible against the base")
    # No slot louder than the ANSI envelope. This check used to be "nothing
    # carries more chroma than the accent", from when the accent was the most
    # colourful thing in the theme, and then "every slot within 3 of the
    # quietest", which refused palettes build() had just made: a bright slot
    # is lighter, the gamut is narrower up there, and lch() walks its chroma
    # down by a different amount for every hue, so on a vivid image the
    # spread is wide and nothing is wrong. What the check protects is that no
    # hue outshouts the rest, and losing chroma to the gamut never does that.
    # So it is a ceiling. Without one (a palette read back from a file) there
    # is nothing to hold the slots to and the check is skipped, and says so.
    slots = ("red", "green", "yellow", "blue", "magenta", "cyan", "orange",
             "bright_red", "bright_green", "bright_yellow", "bright_blue",
             "bright_magenta", "bright_cyan")
    if ceiling is None:
        print("palette: no ANSI ceiling given, loudness not checked", file=sys.stderr)
    else:
        for slot in slots:
            if chroma_of(p[slot]) > ceiling + 1.5:
                bad.append(f"{slot} carries chroma {chroma_of(p[slot]):.0f}, "
                           f"over the ANSI ceiling of {ceiling:.0f}")
    for line in bad:
        print(f"palette: {line}", file=sys.stderr)
    return len(bad)


if __name__ == "__main__":
    # No default path. A relative one here once pointed outside the
    # repository and silently truncated colors.toml through the redirection
    # before failing. With no argument there is no file involved at all.
    if len(sys.argv) > 2:
        raise SystemExit(USAGE)
    path = sys.argv[1] if len(sys.argv) == 2 else SOURCE
    built = build(measure(path) if len(sys.argv) == 2 else MEASURED)
    emit(*built, path)
    failures = audit(built[0], built[6] * ANSI_OVER_IMAGE)
    if failures:
        print(f"palette: {failures} floor(s) not met", file=sys.stderr)
    sys.exit(1 if failures else 0)
