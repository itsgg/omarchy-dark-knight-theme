-- No upstream Neovim colorscheme ships the Dark Knight palette. Kanagawa is
-- the closest match in the LazyVim ecosystem: warm gold (#c0a36e) on a
-- near-black ground, which is the same relationship as --gold-500 on --ink-900.
return {
	{ "rebelot/kanagawa.nvim" },
	{
		"LazyVim/LazyVim",
		opts = {
			colorscheme = "kanagawa",
		},
	},
}
