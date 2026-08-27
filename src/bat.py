"""The bat emblem, as cubic beziers.

The earlier version was straight line segments, which is why it read as a
sawblade: the classic emblem's trailing edge is a run of smooth scallops
between sharp downward spikes, and you cannot get that from polylines.

The right half is authored below as a path from the centre top round to the
centre bottom; the left half is that same path mirrored and reversed, so the
result is one closed outline with no seam down the middle (which matters --
a seam shows the moment you stroke it rather than fill it).
"""

# Right half: (kind, points...). 'L' = corner, 'C' = cubic.
START = (0, -88)                       # centre dip between the ears
HALF = [
    ('L', (50, -170)),                                  # right ear, inner edge
    ('L', (96, -62)),                                   # ear -> shoulder
    ('C', (215, -66), (392, -98), (512, -128)),         # wing, top edge -> tip
    ('C', (478, -66), (440, -6), (356, 52)),            # trailing edge, tip -> spike 1
    ('C', (300, -14), (232, -8), (170, 92)),            # scallop -> spike 2
    ('C', (122, 40), (62, 54), (0, 140)),               # scallop -> centre point
]

# Two things this shape depends on, both learned by getting them wrong:
#   - the wing's top edge must not dip below the shoulder. When it sags, the
#     head reads as a crown perched on a separate boomerang.
#   - the notch between the ears stays narrow and shallow. Widen it and the
#     head stops being a head.

WIDTH, HEIGHT = 1024.0, 310.0          # tip-to-tip, ear-tip to centre point


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
            d.append(f"L {fmt_m(start_pt)}")
        else:
            d.append(f"C {fmt_m(seg[2])} {fmt_m(seg[1])} {fmt_m(start_pt)}")
    d.append("Z")
    return " ".join(d)
