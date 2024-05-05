#!/bin/bash

# Script to find all Git repos, create a new tmux session (or window if a session with same name already exists) for
# each repo, and then run `git pull --rebase` in the newly created tmux window.
#
# Prefer tmux-rebase.py which is an interation over this script.

if [[ "$#" -ne 1 ]]; then
  echo must be given a single positional argument as the root directory to search for Git repos
  exit 1
fi

function setup() {
  # $1=./my/repo/.git
  # d=./my/repo
  # n=my/repo
  d=${1%"/.git"}
  n=${d#"./"}

  if tmux has-session -t "${n}" 2>/dev/null; then
    tmux new-window -t "${n}:" -c "${d}" \; send-keys 'git pull --rebase' Enter
  else
    tmux new-session -d -s "${n}" -c "${d}" \; send-keys 'git pull --rebase' Enter
  fi
}

export -f setup

# Modify -maxdepth if you need to find files at larger depths.
find $1 -mindepth 2 -maxdepth 3 -name ".git" -type d -print0 | xargs -0 -I {} bash -c 'setup "{}"'
