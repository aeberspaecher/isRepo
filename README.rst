About
-----

Git/svn repository detection used for awesome shell prompts. The code is
completely borrowed from Stefan Majewsky:

http://majewsky.wordpress.com/2011/09/13/a-clear-sign-of-madness/

Usage
-----

Place ``isrepo.py`` somewhere where your shell can find it (i.e., somewhere
where ``$PATH`` points to). Create an alias ``isrepo``.

Using the amazing `fish shell <http://ridiculousfish.com/shell/>`_, add a
``fish_prompt`` function to your ``~/.config/fish/config.fish``::

    function fish_prompt -d "Write out the prompt"
        printf '%s%s@%s %s%s%s> ' (isrepo $PWD) (whoami) (hostname|cut -d . -f 1) (set_color $fish_color_cwd) (prompt_pwd) (set_color normal)
    end

This will give you this amazing prompt (with colors, of course)::

  [master@94b08c] eberspaecher@computer ~/s/isRepo>


