if executable('im-select')
autocmd InsertLeave * :call system('im-select com.google.inputmethod.Japanese.Roman')
autocmd CmdlineLeave * :call system('im-select com.google.inputmethod.Japanese.Roman')
endif
