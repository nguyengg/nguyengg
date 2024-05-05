#!/usr/bin/env python3

import argparse
import libtmux
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="tmux-rebase.py",
        description="""Find all Git repos, create a new tmux session (or window if a session with same name already 
        exists) for each repo, and then run `git pull --rebase` in the newly created tmux window."""
    )

    parser.add_argument('-d', '--max-depth', default=2, type=int, metavar="depth",
                        help="The max depth to search for Git repos, default to 2")
    parser.add_argument('dirs', default=["."], nargs='+', metavar="dir",
                        help="The root directories to start the search, default to current directory")

    svr = libtmux.Server()

    args = parser.parse_args()
    max_depth = args.max_depth - 1
    for dir in args.dirs:
        for root, dirs, files in os.walk(dir):
            # root=./my/repo
            # name=my/repo
            name = os.path.relpath(root, dir)
            if name.count(os.path.sep) > max_depth:
                del dirs[:]
            if '.git' not in dirs:
                continue

            sess = svr.sessions.get(session_name=name, default=None)
            if sess is None:
                sess = svr.new_session(session_name=name, start_directory=root, window_name=name)
                win = sess.windows.get(window_name=name)
            else:
                win = sess.new_window(window_name=name, start_directory=root)
            win.active_pane.send_keys('git pull --rebase')
