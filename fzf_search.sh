#!/bin/bash

cat htmlbody.csv |fzf --multi --height 80% --border --color light --prompt="Query " --inline-info \
--bind 'ctrl-e:execute-silent(echo {} |cut -d "," -f1 | xargs -I[] xdg-open [] )+abort,ctrl-j:execute(echo {} |cut -d "," -f1 | xargs -I[] w3m -no-cookie [])' \
--preview '
echo {} | cut -d "," -f1|
xargs -L1 -I[] echo -e "\033[1;32mURL\033[0;39m" : "\033[1;37m[]\033[0;39m" &&
echo ""&&
echo {} | cut -d "," -f2|
xargs -L1 -I[] echo -e "\033[1;32mBODY\033[0;39m" : "\033[1;37m[]\033[0;39m" |fold -w $COLUMNS
'\
|cut -d "," -f1 | xargs -I[] xdg-open []
