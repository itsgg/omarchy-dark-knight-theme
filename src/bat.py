"""The bat emblem, as cubic beziers.

Its geometry is the real emblem's, not a drawing of one. Two earlier versions
were authored from memory: a 3.3 to 1 boomerang with a crown on it, then a
tidier generic bat, and asked plainly whether the second was accurate the
answer was no. It had none of what makes the mark itself: the squared head
with its splayed ears and the flat notch between them, the deep round scoops
either side of the head where the wings curl up and hook inward, the side
points at mid height, and the single long cut-out a side running down to the
tail.

So the right half below is taken from a reference vector, Wikimedia Commons'
"Batman logo (solid black silhouette).svg", normalised to a half width of 500
about its own axis with the origin at the centre of its box. The left half is
that path mirrored and reversed, so the outline is exactly symmetric, which
the reference (a trace) is not quite, and is one closed path with no seam
down the middle, which matters the moment it is stroked rather than filled.
It is the modern emblem. No vector of the 2008 film's sharper variant was to
be found, and a guess at one is how the first two versions happened.
"""

# Right half: (kind, points...). 'L' = corner, 'C' = cubic. From the centre of
# the notch between the ears, round the wing, to the tail point.
START = (0, -113.3)
HALF = [
    ('L', (20.4, -113.4)),
    ('L', (30.7, -139.6)),
    ('C', (39, -160.7), (41.7, -166), (44.1, -166)),
    ('C', (45.8, -166), (47.6, -165.4), (48.1, -164.7)),
    ('C', (48.6, -163.9), (51.9, -142.1), (55.8, -116.1)),
    ('C', (59.4, -90.2), (62.9, -67.3), (63.2, -65.3)),
    ('C', (64.6, -59.8), (69.4, -59.3), (93.3, -62.3)),
    ('C', (164.8, -71.4), (225.2, -94), (250.6, -121.2)),
    ('C', (275.3, -147.6), (272.7, -176.5), (242.9, -205.9)),
    ('C', (224, -224.8), (225.4, -226.3), (253.4, -218.3)),
    ('C', (321.3, -198.7), (384, -161.9), (429.1, -115.3)),
    ('C', (454, -89.4), (469.1, -67.5), (481.6, -38.4)),
    ('C', (493.5, -11), (500, 27.8), (493.7, 31.9)),
    ('C', (491.5, 33.3), (485.4, 32.3), (469.5, 28.5)),
    ('C', (406.9, 12.9), (350.5, 20), (307.2, 48.9)),
    ('C', (287.1, 62.1), (273, 78.6), (260.9, 102.3)),
    ('C', (258.5, 107.1), (255.2, 111.6), (253.7, 112.6)),
    ('C', (251.7, 113.6), (245.3, 112.8), (233.3, 109.9)),
    ('C', (218.1, 106.3), (211.9, 105.6), (185.2, 105.5)),
    ('C', (158.3, 105.3), (152.8, 105.8), (141.1, 108.9)),
    ('C', (92.3, 122.4), (54.4, 151.9), (17.8, 205.5)),
    ('C', (6.1, 222.6), (2.3, 226.3), (0, 226.3)),
]

WIDTH, HEIGHT = 1000.0, 452.6          # tip to tip, lobe top to tail point
CENTRE_Y = 0.0                         # the origin is the centre of the box


def _mirror(p):
    return (-p[0], p[1])


def path(scale=1.0, cx=0.0, cy=0.0):
    def T(p):
        return (cx + p[0] * scale, cy + p[1] * scale)

    def fmt(p):
        x, y = T(p)
        return f"{x:.2f} {y:.2f}"

    def fmt_m(p):
        x, y = T(_mirror(p))
        return f"{x:.2f} {y:.2f}"

    d = [f"M {fmt(START)}"]
    for seg in HALF:
        if seg[0] == 'L':
            d.append(f"L {fmt(seg[1])}")
        else:
            d.append(f"C {fmt(seg[1])} {fmt(seg[2])} {fmt(seg[3])}")

    # Left half: walk the same segments backwards, mirrored. A reversed cubic
    # swaps its two control points and runs end -> start.
    pts = [START] + [s[-1] for s in HALF]
    for i in range(len(HALF) - 1, -1, -1):
        seg, start_pt = HALF[i], pts[i]
        if seg[0] == 'L':
            # The last of these lands back on START, which Z is about to do
            # anyway: a zero-length segment before a close.
            if i:
                d.append(f"L {fmt_m(start_pt)}")
        else:
            d.append(f"C {fmt_m(seg[2])} {fmt_m(seg[1])} {fmt_m(start_pt)}")
    d.append("Z")
    return " ".join(d)
