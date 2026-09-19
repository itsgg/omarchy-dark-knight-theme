#!/usr/bin/env python3
"""Emit neovim.lua: Omarchy's aether spec, with the indent guides taken off
the text ramp.

    OMARCHY_PATH=/usr/share/omarchy python3 src/neovim.py > neovim.lua

Why this file exists at all. Omarchy generates neovim.lua from
default/themed/neovim.lua.tpl for any theme that does not ship one, and that
template hands aether the palette and stops. aether then paints `muted` onto
both text and decoration: comments and line numbers, but also NonText, which
is what snacks.nvim draws every indent guide with, and IblIndent, which is
indent-blankline's. So the guides land at 3.95:1 on the ground, at comment
weight and in the comment colour, on every indented line of the file. On a
deeply nested file the guides are most of what the eye sees.

`muted` cannot be dimmed to fix it. The same key is the comment and line
number colour, and those are text, wanted near the 4.5:1 body floor rather
than below the 3:1 UI one. One value is being asked to be both decoration and
text, and the two want opposite brightnesses. So the split is made here, in
the one place that can tell them apart: aether's on_highlights, which runs
after every built-in and plugin group.

Where the guides go. `line` (1.60:1), which is already this theme's structure
colour and its inactive window border: present, never read as text. The scope
guides, which come out at full `cyan` (6.45:1, snacks, through Special) and
`blue` (6.43:1, indent-blankline) and so at the weight of code rather than of
chrome, go to `accent_dim` (3.20:1): still the marker for where you are, no
longer competing with the text it brackets. Comments, line numbers and every
other use of `muted` are untouched.

Three things worth knowing before editing this.

The template is read rather than copied. Shipping a hand-written aether spec
would freeze it against upstream the day it was written, and a key added to
neovim.lua.tpl would not reach this theme until somebody noticed. Reading the
installed template at render time means only the on_highlights block below is
ours, and it is why this script needs Omarchy present while the other
generators need only colors.toml.

It is still a freeze, for the same reason shell.controls.toml is one:
omarchy-theme-set-templates does not overwrite a file the theme ships, so an
Omarchy upgrade that changes neovim.lua.tpl reaches this theme only when
src/render.sh is run again. The cost is one re-render per upstream change, and
the alternative is not having the override at all.

Omarchy stages no .lua from a theme installed out of a git repo, by design:
Neovim runs it at startup. So this file reaches Neovim where the theme is a
local directory or a symlink to a checkout, and an install from GitHub keeps
the template's spec and the loud guides. The portable fix is upstream, in
neovim.lua.tpl, not here.
"""

import os
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = "default/themed/neovim.lua.tpl"

# Where on_highlights goes: beside `colors` in the aether spec's opts, not in
# LazyVim's. Both open with `opts = {`, so the colors table is what tells them
# apart, and the block is inserted between the two lines.
OPTS_OPEN = "    opts = {\n"
COLORS_OPEN = "      colors = {\n"
ANCHOR = OPTS_OPEN + COLORS_OPEN

# The guides, off the text ramp and onto structure. Keyed by colors.toml, so a
# palette rebuild moves them with everything else. Both indent plugins are
# covered because Omarchy's Neovim is LazyVim, which ships snacks, and either
# plugin may be the one installed.
OVERRIDES = (
    ("NonText", "line", "snacks links SnacksIndent here; also eol and extends"),
    ("Whitespace", "line", "listchars"),
    ("IblIndent", "line", "indent-blankline's own guide, painted from muted too"),
    ("SnacksIndent", "line", "set outright, so it cannot follow NonText elsewhere"),
    ("SnacksIndentScope", "accent_dim", "the scope guide: a marker, not a shout"),
    ("SnacksIndentChunk", "accent_dim", "same guide, chunk style"),
    ("IblScope", "accent_dim", "indent-blankline's scope guide, which is blue"),
    ("MiniIndentscopeSymbol", "accent_dim", "mini.indentscope, if that is the one"),
)

# Syntax, on the theme's own rule: one hue, carried by light. aether hands six
# syntax classes six ANSI hues, which this palette places at one chroma and
# one lightness on purpose, so in the editor every word weighed the same and
# nothing led the eye. Hue is kept for the things that are data rather than
# structure: strings, literals, types, and builtins. Everything that is
# grammar goes onto the grey ramp, below the code it organises. A definition
# is the brightest word on its line; a call is ordinary text.
#
# (group, colors.toml key, bold). Links in aether follow these: overriding
# Conditional reaches @keyword.conditional. The "@" groups listed are the ones
# aether sets outright rather than links, so they have to be named.
SYNTAX = (
    # Grammar: the grey ramp.
    ("Keyword", "light_foreground", False),
    ("Statement", "light_foreground", False),
    ("Conditional", "light_foreground", False),
    ("Repeat", "light_foreground", False),
    ("Exception", "light_foreground", False),
    ("Define", "light_foreground", False),
    ("Include", "light_foreground", False),
    ("PreProc", "light_foreground", False),
    ("@keyword", "light_foreground", False),
    ("@keyword.function", "light_foreground", False),
    # Names: ordinary text. Calls included; LSP links them through Function.
    ("Identifier", "foreground", False),
    ("Function", "foreground", False),
    ("@function.call", "foreground", False),
    ("@function.method.call", "foreground", False),
    ("@property", "foreground", False),
    ("@lsp.type.property", "foreground", False),
    ("@variable.member", "foreground", False),
    ("@variable.parameter", "foreground", False),
    # Docstrings are prose, not data. aether gives them a yellow of their own,
    # and in a file that documents itself that made the documentation the
    # most colourful thing on the screen. One step above a comment, so the two
    # are still told apart.
    ("@string.documentation", "dark_foreground", False),
    # Definitions: the brightest word on the line.
    ("@function", "bright_foreground", True),
    ("@function.method", "bright_foreground", True),
    ("@lsp.typemod.function.declaration", "bright_foreground", True),
    ("@lsp.typemod.method.declaration", "bright_foreground", True),
    # Data: the hues. Strings green, every literal orange, types the accent.
    ("Constant", "orange", False),
    ("Type", "accent", False),
    ("StorageClass", "accent", False),
    ("Structure", "accent", False),
    ("Typedef", "accent", False),
    ("@constructor", "accent", False),
)


def template_path():
    """The installed neovim.lua.tpl, or a message naming what is missing."""
    root = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
    path = pathlib.Path(root) / TEMPLATE
    if not path.is_file():
        raise SystemExit(
            f"neovim.py: no {path}. This generator reads Omarchy's own template "
            "so the spec cannot drift from it; run it on a machine with Omarchy "
            "installed, or point OMARCHY_PATH at a checkout.")
    return path


def resolve(text, palette):
    """Substitute {{ key }} from colors.toml, failing on anything left over.

    Omarchy's own substitution understands more than a bare key: there are
    mix, gradient and _rgb forms. None appear in neovim.lua.tpl today, and a
    silent pass-through would ship `{{ mix background foreground 10% }}` as a
    highlight colour, so anything still wearing braces after this is an error
    rather than a warning.
    """
    keys = re.findall(r"\{\{\s*([a-z0-9_]+)\s*\}\}", text)
    missing = sorted({k for k in keys if k not in palette})
    if missing:
        raise SystemExit("neovim.py: colors.toml has no " + ", ".join(missing))

    text = re.sub(r"\{\{\s*([a-z0-9_]+)\s*\}\}",
                  lambda m: palette[m.group(1)], text)

    left = sorted(set(re.findall(r"\{\{[^}]*\}\}", text)))
    if left:
        raise SystemExit(
            "neovim.py: neovim.lua.tpl now uses template forms this generator "
            "does not resolve: " + ", ".join(left))
    return text


def on_highlights(palette):
    width = max(len(group) for group, _, _ in OVERRIDES)
    lines = [
        "      -- Decoration is not text. aether paints NonText and IblIndent from\n",
        "      -- `muted`, which is also the comment colour, so every indent guide\n",
        "      -- arrives at comment weight. These move the guides onto the theme's\n",
        "      -- structure colour and the scope guides onto the dim accent; `muted`\n",
        "      -- itself, and so every comment and line number, is left alone.\n",
        "      on_highlights = function(hl)\n",
    ]
    for group, key, why in OVERRIDES:
        lines.append(f'        hl.{group:<{width}} = {{ fg = "{palette[key]}", '
                     f"nocombine = true }} -- {why}\n")
    lines += [
        "\n",
        "        -- Syntax: grammar on the grey ramp, names as text, definitions\n",
        "        -- brightest, and hue only for data. See src/neovim.py.\n",
    ]
    swidth = max(len(group) for group, _, _ in SYNTAX) + 4
    for group, key, bold in SYNTAX:
        index = f'["{group}"]'
        attrs = f'fg = "{palette[key]}"' + (", bold = true" if bold else "")
        lines.append(f"        hl{index:<{swidth}} = {{ {attrs} }} -- {key}\n")
    lines.append("      end,\n")
    return "".join(lines)


def main():
    palette = tomllib.load(open(ROOT / "colors.toml", "rb"))
    spec = resolve(template_path().read_text(), palette)

    if spec.count(ANCHOR) != 1:
        raise SystemExit(
            "neovim.py: neovim.lua.tpl no longer has exactly one aether "
            "`opts = { colors = {` to insert on_highlights after; re-read the "
            "template and fix the anchor.")

    sys.stdout.write(
        "-- Dark Knight for Neovim: Omarchy's aether spec, plus the indent guides\n"
        "-- and a syntax pass that keeps hue for data.\n"
        "--\n"
        "-- Generated by src/neovim.py from colors.toml and Omarchy's\n"
        f"-- {TEMPLATE}. Do not hand-edit: change the script.\n"
        "--\n"
        "-- Omarchy stages no .lua from a theme installed out of a git repo, so this\n"
        "-- file applies where the theme is a local directory or a symlink to this\n"
        "-- checkout. Installed from GitHub, the theme gets the template's spec.\n")
    sys.stdout.write(
        spec.replace(ANCHOR, OPTS_OPEN + on_highlights(palette) + COLORS_OPEN))


if __name__ == "__main__":
    main()
