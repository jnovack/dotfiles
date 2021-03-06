set background=dark
hi clear

if exists("syntax_on")
    syntax reset
endif

let colors_name="ozmo"

hi Normal ctermbg=0 ctermfg=15 guibg=#000000 guifg=#d0d0d0 gui=none
hi StatusLineNC	ctermbg=7 ctermfg=0 guibg=#6c7b8b guifg=#000000 gui=bold
hi VertSplit	ctermbg=7 ctermfg=0 guibg=#6c7b8b guifg=#000000 gui=bold
hi Visual		ctermbg=7 ctermfg=0 guibg=#8598ac guifg=#000000 gui=bold
hi NonText		ctermfg=8	guibg=bg	guifg=#878787	gui=none

hi Cursor		guibg=#c6e2ff	guifg=#000000	gui=bold
hi FoldColumn	guibg=#363d45	guifg=fg	gui=none
hi Folded	 	guibg=#48525d	guifg=fg	gui=none
hi LineNr		guibg=#24292e	guifg=#a7a7a7	gui=none
hi SignColumn	guibg=#363d45	guifg=fg 	gui=none
hi StatusLine	guibg=#9fb6cd	guifg=#000000	gui=bold
hi VisualNOS	guibg=bg	guifg=#8598ac	gui=bold,underline
hi WildMenu		guibg=#e7e7e7	guifg=#000000	gui=bold

hi Directory		guibg=bg	guifg=#1e90ff	gui=none
hi ErrorMsg		guibg=#ee2c2c	guifg=#ffffff	gui=bold
hi DiffAdd      guibg=#008b00   guifg=fg        gui=none
hi DiffChange   guibg=#00008b   guifg=gray      gui=none
hi DiffDelete   guibg=#8b0000   guifg=fg        gui=none
hi DiffText     guibg=#00008b   guifg=cyan      gui=bold
hi IncSearch		guibg=#e7e7e7	guifg=#000000	gui=bold
hi ModeMsg		guibg=bg	guifg=fg	gui=bold
hi MoreMsg		guibg=bg	guifg=#d0d097	gui=bold
hi Question		guibg=bg	guifg=#e0c07e	gui=bold
hi Search		guibg=bg	guifg=#FFFF7A	gui=bold
hi SpecialKey		guibg=bg	guifg=#a28b5b	gui=none
hi Title		guibg=bg	guifg=#e7e7e7	gui=bold
hi WarningMsg		guibg=bg	guifg=#ee2c2c	gui=bold

hi Comment		guibg=bg	guifg=#878787	gui=bold
hi Constant		guibg=bg	guifg=#A322C3	gui=none
hi Error		guibg=bg	guifg=#ee2c2c	gui=none
hi Identifier		guibg=bg	guifg=#7ee0ce	gui=none
hi Ignore		guibg=bg	guifg=#373737	gui=none
hi lCursor		guibg=fg	guifg=bg	gui=bold
hi PreProc		guibg=bg	guifg=#d7a0d7	gui=none
hi Special		guibg=bg	guifg=#e0c07e	gui=none
hi Statement		guibg=bg	guifg=#7ec0ee	gui=none
hi Todo			guibg=bg	guifg=#bbbb87	gui=bold,underline
hi Type			guibg=bg	guifg=#f09479	gui=none
hi Underlined		guibg=bg	guifg=#1e90ff	gui=underline

hi htmlBold guibg=bg guifg=fg gui=bold
hi htmlItalic guibg=bg guifg=fg gui=italic
hi htmlUnderline guibg=bg guifg=fg gui=underline
hi htmlBoldItalic guibg=bg guifg=fg gui=bold,italic
hi htmlBoldUnderline guibg=bg guifg=fg gui=bold,underline
hi htmlBoldUnderlineItalic guibg=bg guifg=fg gui=bold,underline,italic
hi htmlUnderlineItalic guibg=bg guifg=fg gui=underline,italic

