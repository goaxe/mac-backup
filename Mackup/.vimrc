"=============================================================================
"     FileName: .vimrc
"         Desc: 
"       Author: Jian Huang
"        Email: huangjian1993@gmail.com
"     HomePage: https://cn.linkedin.com/in/huangjian1993
"      Version: 0.0.1
"   LastChange: 2015-08-28 16:53:49
"      History:
"=============================================================================

set nocompatible            " be iMproved, required
filetype off                " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
" alternatively, pass a path where Vundle should install plugins
" call vundle#begin('~/some/path/here')

" let Vundle manage Vundle, required
Bundle 'VundleVim/Vundle.vim'

Bundle 'dantezhu/authorinfo'
Bundle 'tomasr/molokai'
Bundle 'altercation/vim-colors-solarized'
Bundle 'scrooloose/nerdtree'
Bundle 'scrooloose/nerdcommenter'
Bundle 'fholgado/minibufexpl.vim'
Bundle 'kien/rainbow_parentheses.vim'
Bundle 'fatih/vim-go'
Bundle 'majutsushi/tagbar'
Bundle 'kien/ctrlp.vim'
Bundle 'Valloric/YouCompleteMe'
Bundle 'dkprice/vim-easygrep'
Bundle 'Lokaltog/vim-powerline'
Bundle 'Mizuchi/STL-Syntax'
Bundle 'xolox/vim-misc'
Bundle 'xolox/vim-lua-ftplugin'
Bundle 'dyng/ctrlsf.vim'
Bundle 'Yggdroot/indentLine'
Bundle 'vim-scripts/a.vim'
Bundle 'derekwyatt/vim-fswitch'
Bundle 'derekwyatt/vim-protodef'
Bundle 'gcmt/wildfire.vim'
Bundle 'jiangmiao/auto-pairs'

"Bundle 'scrooloose/syntastic'
"Bundle 'nathanaelkane/vim-indent-guides'
"Bundle 'Valloric/ycmd'
"Bundle 'davidhalter/jedi-vim'

" All of your Plugins must be added before the following line
call vundle#end()          " required
filetype plugin indent on  " required
" To ignore plugin indent changes, instead use:
" filetype plugin on
"
" Brief help
" :PluginList     - lists configured plugins
" :PluginInstall  - installs plugins; append `!` to update or just :PluginUpdate
" :PluginSearch foo - searches for foo; append `!` to refresh local cache
" :PluginClean    - confirms removal of unused plugins; append `!` to auto-approve removal
"
" see :h vundle for more details or wiki for FAQ
" Put your non-Plugin stuff after this line
"
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" common settings
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

let mapleader=";"
"colorscheme default

map <Leader>lb 0
map <Leader>le $
map <Leader>gg gg=G<CR>

vnoremap <Leader>y "+y
nmap <Leader>p "+p
vmap <C-c> "+y
vmap <C-x> "+c
vmap <C-v> c<ESC>"+p
imap <C-v> <C-r><C-o>+
nmap <C-v> "+p

nmap <Leader>q :q<CR>
nmap <Leader>w :w<CR>
nmap <Leader>WQ :wa<CR>:q<CR>
nmap <Leader>Q :qa!<CR>

"nnoremap nw <C-W><C-W>
nnoremap <Leader>lw <C-W>l
nnoremap <Leader>hw <C-W>h
nnoremap <Leader>kw <C-W>k
nnoremap <Leader>jw <C-W>j

nmap <Leader>pa %

nnoremap <Leader>R :call Replace(0, 0, input('Replace '.expand('<cword>').' with: '))<CR>
nnoremap <Leader>rw :call Replace(0, 1, input('Replace '.expand('<cword>').' with: '))<CR>
nnoremap <Leader>rc :call Replace(1, 0, input('Replace '.expand('<cword>').' with: '))<CR>
nnoremap <Leader>rcw :call Replace(1, 1, input('Replace '.expand('<cword>').' with: '))<CR>
nnoremap <Leader>rwc :call Replace(1, 1, input('Replace '.expand('<cword>').' with: '))<CR>

"map <leader>ss :mksession! my.vim<cr> :wviminfo! my.viminfo<cr>
map <leader>ss :mksession! my.vim<cr>
"map <leader>rs :source my.vim<cr> :rviminfo my.viminfo<cr>
map <leader>rs :source my.vim<cr>
set mouse=a
set selection=exclusive
set selectmode=mouse,key

set nocompatible
set wildmenu
set gcr=a:block-blinkon0

set guioptions-=l
set guioptions-=L
set guioptions-=r
set guioptions-=R
set guioptions-=m
set guioptions-=T
set laststatus=2

set showcmd
set ruler
set number
"set cursorline
"set cursorcolumn

set showmatch
set matchtime=1
set ignorecase
set smartcase
set incsearch

set backspace=2

set fillchars=vert:\ ,stl:\ ,stlnc:\

set scrolloff=3
"set list
"set listchars=tab:\>\ ,trail:.,extends:>,precedes:<,eol:$
"set listchars=trail:.,extends:>,precedes:<,eol:$
"set listchars=eol:$
"set hlsearch
set guifont=YaHei\ Consolas\ Hybrid\ 16
set wrap
set whichwrap+=<,>,h,l
set expandtab
set tabstop=4
set shiftwidth=4
set softtabstop=4
"set foldmethod=indent
set foldmethod=syntax
set nofoldenable

set sessionoptions="blank,globals,localoptions,tabpages,sesdir,folds,help,options,resize,winpos,winsize"
set undodir=~/.undo_history/
set undofile

 
source $VIMRUNTIME/ftplugin/man.vim
nmap <Leader>man :Man 3 <cword><CR>

" 替换函数。参数说明：
" confirm：是否替换前逐一确认
" wholeword：是否整词匹配
" replace：被替换字符串
function! Replace(confirm, wholeword, replace)
    wa
    let flag = ''
    if a:confirm
        let flag .= 'gec'
    else
        let flag .= 'ge'
    endif
    let search = ''
    if a:wholeword
        let search .= '\<' . escape(expand('<cword>'), '/\.*$^~[') . '\>'
    else
        let search .= expand('<cword>')
    endif
    let replace = escape(a:replace, '/\&~')
    execute 'argdo %s/' . search . '/' . replace . '/' . flag . '| update'
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" file settings
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

filetype on
filetype plugin on
filetype indent on
syntax enable
syntax on

au BufNewFile,BufRead *.py,*.pyw setf python

set nobackup
setlocal noswapfile
set bufhidden=hide
 
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" plugin settings
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
" dantezhu/authorinfo
let g:vimrc_author='Jian Huang'
let g:vimrc_email='huangjian1993@gmail.com'
let g:vimrc_homepage='https://cn.linkedin.com/in/huangjian1993'
nnoremap <leader>at :AuthorInfo<CR>

" altercation/vim-colors-solarized tomasr/molokai
" colorscheme
set background=dark
if has("gui_running")
  "colorscheme solarized
else
  "color molokai
  "color phd
endif
"colorscheme solarized
colorscheme molokai
"colorscheme phd

" scrooloose/nerdtree
nmap <Leader>fl :NERDTreeToggle<CR>
let NERDTreeWinSize=22
let NERDTreeWinPos="left"
let NERDTreeShowHidden=1
let NERDTreeIgnore=[ '\.pyc$', '\.pyc$', '\.pyo$', '\.obj$', '\.o$', '\.so$', '\.egg$', '^\.git$', '^\.svn$', '^\.hg$' ]
let NERDTreeMinimalUI=1
let NERDTreeAutoDeleteBuffer=1

" scrooloose/syntastic
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*
let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 1
let g:syntastic_cpp_compiler = 'g++' "change the compiler to g++ to support c++11. 
let g:syntastic_cpp_compiler_options = '-std=c++11 -stdlib=libc++' "set the options of g++ to suport c++11.
"let g:syntastic_ignore_files=[".*\.py$"]
let g:syntastic_error_symbol = '✗'
let g:syntastic_warning_symbol = '⚠'


" fholgado/minibufexpl.vim
let g:miniBufExplMapWindowNavVim    = 1
let g:miniBufExplMapWindowNavArrows = 1
let g:miniBufExplMapCTabSwitchBufs  = 1
let g:miniBufExplModSelTarget       = 1
let g:miniBufExplForceSyntaxEnable = 1
let g:miniBufExplorerMoreThanOne=2
let g:miniBufExplCycleArround=1
map <Leader>bl :MBEToggle<cr>
map <F2> :MBEbn<cr>
map <F1> :MBEbp<cr>

"" davidhalter/jedi-vim
"let g:jedi#goto_command = "<leader>d"
"let g:jedi#goto_assignments_command = "<leader>g"
"let g:jedi#goto_definitions_command = "<leader>d"
"let g:jedi#documentation_command = "K"
"let g:jedi#usages_command = "<leader>n"
"let g:jedi#completions_command = "<C-Space>"
"let g:jedi#rename_command = "<leader>r"

" kien/rainbow_parentheses.vim
let g:rbpt_colorpairs = [
  \ ['brown',       'RoyalBlue3'],
  \ ['Darkblue',    'SeaGreen3'],
  \ ['darkgray',    'DarkOrchid3'],
  \ ['darkgreen',   'firebrick3'],
  \ ['darkcyan',    'RoyalBlue3'],
  \ ['darkred',     'SeaGreen3'],
  \ ['darkmagenta', 'DarkOrchid3'],
  \ ['brown',       'firebrick3'],
  \ ['gray',        'RoyalBlue3'],
  \ ['black',       'SeaGreen3'],
  \ ['darkmagenta', 'DarkOrchid3'],
  \ ['Darkblue',    'firebrick3'],
  \ ['darkgreen',   'RoyalBlue3'],
  \ ['darkcyan',    'SeaGreen3'],
  \ ['darkred',     'DarkOrchid3'],
  \ ['red',         'firebrick3'],
  \ ]
let g:rbpt_max = 40
let g:rbpt_loadcmd_toggle = 0

" fatih/vim-go
autocmd BufWritePre *.go :GoFmt

" majutsushi/tagbar
nmap <Leader>tl :TagbarToggle<CR>
let g:tagbar_ctags_bin='/usr/bin/ctags'
let g:tagbar_width=32
let g:tagbar_compact=1
"autocmd BufReadPost *.cpp,*.c,*.h,*.hpp,*.cc,*.cxx call tagbar#autoopen() 

let tagbar_left=0
let g:tagbar_type_cpp = {
     \ 'ctagstype' : 'c++',
     \ 'kinds'     : [
         \ 'd:macros:1',
         \ 'g:enums',
         \ 't:typedefs:0:0',
         \ 'e:enumerators:0:0',
         \ 'n:namespaces',
         \ 'c:classes',
         \ 's:structs',
         \ 'u:unions',
         \ 'f:functions',
         \ 'm:members:0:0',
         \ 'v:global:0:0',
         \ 'x:external:0:0',
         \ 'l:local:0:0'
     \ ],
     \ 'sro'        : '::',
     \ 'kind2scope' : {
         \ 'g' : 'enum',
         \ 'n' : 'namespace',
         \ 'c' : 'class',
         \ 's' : 'struct',
         \ 'u' : 'union'
     \ },
     \ 'scope2kind' : {
         \ 'enum'      : 'g',
         \ 'namespace' : 'n',
         \ 'class'     : 'c',
         \ 'struct'    : 's',
         \ 'union'     : 'u'
     \ }
\ }

" Valloric/YouCompleteMe
"0      Black  
"1      DarkBlue  
"2      DarkGreen        
"3      DarkCyan 
"4      DarkRed
"5      DarkMagenta        
"6      Brown, DarkYellow            
"7      LightGray, LightGrey, Gray, Grey                   
"8      DarkGray, DarkGrey   
"9      Blue, LightBlue     
"10     Green, LightGreen          
"11     Cyan, LightCyan                    
"12     Red, LightRed                         
"13     Magenta, LightMagenta 
"14     Yellow, LightYellow   
"15     White     
" white  black  yellow  cyan   magenta   blue   grey   green   red
highlight Pmenu ctermfg=White ctermbg=DarkBlue guifg=#005f87 guibg=#EEE8D5
highlight PmenuSel ctermfg=DarkGrey ctermbg=LightGreen guifg=#AFD700 guibg=#106900

let g:ycm_complete_in_comments=1
let g:ycm_confirm_extra_conf=0
let g:ycm_collect_identifiers_from_tags_files=1
let g:ycm_min_num_of_chars_for_completion=1
let g:ycm_cache_omnifunc=0
let g:ycm_seed_identifiers_with_syntax=1
let g:ycm_global_ycm_extra_conf = '~/.vim/bundle/YouCompleteMe/third_party/ycmd/.ycm_extra_conf.py'

inoremap <leader>; <C-x><C-o>
nnoremap <leader>gd :YcmCompleter GoToDeclaration<CR>
nnoremap <leader>ge :YcmCompleter GoToDefinition<CR>

set completeopt-=preview
"set tags+=/data/misc/software/app/vim/stdcpp.tags

" Lokaltog/vim-powerline
let g:Powerline_colorscheme='solarized256'

" xolox/vim-lua-ftplugin
let g:lua_compiler_name = '/usr/local/bin/luac'
let b:lua_compiler_name = '/usr/local/bin/lualint'
let g:lua_complete_omni = 1

" Yggdroot/indentLine
let g:indentLine_color_term = 239
let g:indentLine_color_gui = '#A4E57E'
let g:indentLine_color_tty_light = 7 " (default: 4)
let g:indentLine_color_dark = 1 " (default: 2)
let g:indentLine_char = '¦' 
"¦,┆,︙,│
let g:indentLine_enabled = 1

"" nathanaelkane/vim-indent-guides
"hi IndentGuidesOdd  guibg=lightblue   ctermbg=3
"hi IndentGuidesEven guibg=lightgreen ctermbg=4
"let g:indent_guides_enable_on_vim_startup=1
"let g:indent_guides_start_level=2
"let g:indent_guides_guide_size=1
"let g:indent_guides_auto_colors = 0
"nmap <silent> <Leader>i <Plug>IndentGuidesToggle

" dyng/ctrlsf.vim
nnoremap <Leader>sp :CtrlSF<CR>

" vim-scripts/a.vim 
nmap <Leader>ch :A<CR>
nmap <Leader>sch :AS<CR>



" derekwyatt/vim-protodef derekwyatt/vim-fswitch
let g:protodefprotogetter='~/.vim/bundle/vim-protodef/pullproto.pl'
let g:disable_protodef_sorting=1

" gcmt/wildfire.vim
map <SPACE> <Plug>(wildfire-fuel)
vmap <S-SPACE> <Plug>(wildfire-water)

let g:wildfire_objects = ["i'", 'i"', "i)", "i]", "i}", "i>", "ip"]


" 代码导航
 
" 基于标签的代码导航

" 设置插件 indexer 调用 ctags 的参数
" 默认 --c++-kinds=+p+l，重新设置为 --c++-kinds=+l+p+x+c+d+e+f+g+m+n+s+t+u+v
" 默认 --fields=+iaS 不满足 YCM 要求，需改为 --fields=+iaSl
let g:indexer_ctagsCommandLineOptions="--c++-kinds=+l+p+x+c+d+e+f+g+m+n+s+t+u+v --fields=+iaSl --extra=+q"

" 正向遍历同名标签
nmap <Leader>tn :tnext<CR>
" 反向遍历同名标签
nmap <Leader>tp :tprevious<CR>

" 设置快捷键实现一键编译及运行
nmap <Leader>m :wa<CR> :cd build/<CR> :!rm -rf main<CR> :!cmake CMakeLists.txt<CR>:make<CR><CR> :cw<CR> :cd ..<CR>
nmap <Leader>g :wa<CR>:cd build/<CR>:!rm -rf main<CR>:!cmake CMakeLists.txt<CR>:make<CR><CR>:cw<CR>:cd ..<CR>:!build/main<CR>




" 调用 gundo 树
nnoremap <Leader>ud :GundoToggle<CR>

" >>
" web 前端

" surrond 添加 <p> 元素的快捷键
nmap <Leader>ap yss<p><CR>

" 对 HTML 元素进行转义：< -> &lt;、> -> &gt;、& -> &amp;、空格 -> &nbsp;、行尾添加 <br />
" 先后顺序敏感
function HtmlEscape()
    retab<CR>
    silent s/&/\&amp;/eg
    silent s/</\&lt;/eg
    silent s/>/\&gt;/eg
    silent s/ /\&nbsp;/eg
    silent s/$/<br \/>/eg
endfunction
vnoremap <Leader>he :call HtmlEscape()<CR>


" Yggdroot/indentLine
let g:indentLine_color_term = 239
let g:indentLine_color_gui = '#A4E57E'
let g:indentLine_color_tty_light = 7 " (default: 4)
let g:indentLine_color_dark = 1 " (default: 2)
let g:indentLine_char = '¦' 
"¦,┆,︙,│
let g:indentLine_enabled = 1
