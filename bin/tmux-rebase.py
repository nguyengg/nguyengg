#!/usr/bin/env python3

# This script requires asyncio and libtmux. It can run `git pull --rebase` concurrently in directories that contain a
# Git repo (by existence of .git) to create a tmux session in that directory.
#
# tmux-rebase is a shell version predecessor of this script that does the same thing but sequentially.

import argparse
import asyncio
import os
import sys

import libtmux

svr = libtmux.Server()


async def rebase(root, name):
    sess = svr.sessions.get(session_name=name, default=None)
    if sess is None:
        pane = svr.new_session(session_name=name, start_directory=root).active_pane
    else:
        pane = sess.new_window(start_directory=root).active_pane

    proc = await asyncio.create_subprocess_shell(
        f'git -C {root} pull --rebase',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        txt = stdout.decode().splitlines()[-1] if stdout else 'done with no output'
        print(f'{name}: {txt}')
        pane.send_keys('git pull --rebase')
    else:
        txt = stderr.decode().splitlines()[-1] if stderr else f'exits with code {proc.returncode}'
        print(f'{name}: {txt}', file=sys.stderr)
        pane.send_keys('git pull --rebase')


async def main():
    parser = argparse.ArgumentParser(
        prog="tmux-rebase.py",
        description="Find all Git repos, create a new tmux session (or window if a session with same name already "
                    "exists) for each repo, and then run `git pull --rebase` in the newly active tmux pane."
    )

    parser.add_argument('-d', '--max-depth', default=2, type=int, metavar="depth",
                        help="The max depth to search for Git repos, default to 2")
    parser.add_argument('dirs', default=["."], nargs='+', metavar="dir",
                        help="The root directories to start the search, default to current directory")

    args = parser.parse_args()
    max_depth = args.max_depth - 1

    tasks = list()
    for top in args.dirs:
        for root, dirs, files in os.walk(top):
            # root=./my/repo
            # name=my/repo
            name = os.path.relpath(root, top)
            if name.count(os.path.sep) > max_depth:
                del dirs[:]
            if '.git' not in dirs:
                continue

            tasks.append(asyncio.create_task(rebase(root, name)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
