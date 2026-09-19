# Installing and updating

The short version is in the [README](../README.md#install). This is the rest:
the working-copy install, how to update either kind, and how to get the
Neovim override on a clone install that Omarchy will not hand a `.lua` to.

## As a working copy, which is what gets `neovim.lua`

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

That install gets `neovim.lua` (the indent guides and the syntax pass). The
clone install gets Omarchy's generated spec instead, which means the same
colours without those; everything else about the theme is identical.

Two consequences of the link, both by design. `omarchy theme update` passes
over it, because a working copy is not Omarchy's to pull, so it updates with
`git -C ~/src/dark-knight pull` and a `theme set` after. And `omarchy theme
install` of this repo replaces the link with a clone, which quietly drops back
to the generated spec.

## Updating an install that is already there

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

### Keeping the clone install, and dimming the guides from Neovim

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
theme they land on #252B2E and #607A8C, against the #283943 and #596D7B the
theme ships, the same two places on the ramp measured rather than written
down; under another aether theme they are that theme's.

### Or moving the clone onto a working copy

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
apply it on a theme switch; that is its own command, and it asks for your
password because it rebuilds the initramfs:

```sh
omarchy plymouth set by theme dark-knight
```
