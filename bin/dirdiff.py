#!/usr/bin/env python3

import argparse
import os
import platform
import shutil

from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Finds and copies files present in one directory but not the other.",
    )

    generate = object()
    parser.add_argument(
        "-c",
        "--copy-to",
        dest="copy_dir",
        nargs='?',
        const=generate,
        default=None,
        help="If given a directory, the files will be copied into this path. If given an empty string, an empty "
             "directory with a unique name (diff or diff-1 or diff-2 etc.) will be created. If absent, only print the "
             "diff.",
    )
    parser.add_argument(
        "-e",
        "--ext",
        action="append",
        dest="ext",
        help="One or more file extensions to filter results. If none are given, all file extensions are included in "
             "diff computation. The values are implicitly prefixed with '.' if not explicitly specified.",
    )
    parser.add_argument(
        "a",
        nargs='?',
        type=str,
        help="the first directory; if not given, a dialog will be opened to select an existing directory",
    )
    parser.add_argument(
        "b",
        nargs='?',
        type=str,
        help="the second directory; if not given, a dialog will be opened to select an existing directory",
    )

    args = parser.parse_args()
    if args.a is None:
        a = askdirectory(title="Select first directory")
        if not a:
            return
        a = Path(a)
    else:
        a = Path(args.a)

    if args.b is None:
        b = askdirectory(initialdir=a.parent, title="Select second directory")
        if not b:
            return
        b = Path(b)
    else:
        b = Path(args.b)

    filename_filter = lambda: True
    if args.ext:
        import re
        p = re.compile(f"\\.({'|'.join(e.removeprefix(".") for e in args.ext)})")
        filename_filter = p.fullmatch

    common_path = os.path.commonpath((a, b))
    a_rel = a.relative_to(common_path)
    b_rel = b.relative_to(common_path)
    a_files = {
        Path(root, filename).relative_to(a)
        for (root, _, filenames) in a.walk()
        for filename in filenames
        if filename_filter(filename)
    }
    b_files = {
        Path(root, filename).relative_to(b)
        for (root, _, filenames) in b.walk()
        for filename in filenames
        if filename_filter(filename)
    }
    in_a_only, in_b_only = (a_files - b_files), (b_files - a_files)

    if args.copy_dir is generate:
        copy_dir = gen_copy_dir(askparentdir=args.a is None or args.b is None, initialdir=b.parent)
    elif args.copy_dir:
        copy_dir = Path(args.copy_dir)
        copy_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f'"{a_rel}" has {len(in_a_only)}/{len(a_files)} exclusive files')
        print(f'"{b_rel}" has {len(in_b_only)}/{len(b_files)} exclusive files')
        return

    m = len(in_a_only)
    n = m + len(in_b_only)

    for i, src in enumerate(in_a_only):
        dst = copy_dir / src
        print(f'{i + 1}/{n} "{a_rel / src}"')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a / src, dst)

    for i, src in enumerate(in_b_only):
        dst = copy_dir / src
        print(f'{i + 1 + m}/{n} "{b_rel / src}"')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(b / src, dst)


def askdirectory(initialdir=None, title="Select directory"):
    from tkinter import Tk
    from tkinter.filedialog import askdirectory
    Tk().withdraw()
    return askdirectory(initialdir=initialdir, title=title, mustexist=True)


def gen_copy_dir(askparentdir=False, initialdir=None):
    if askparentdir:
        v = askdirectory(initialdir=initialdir, title="Select parent directory to create directory to copy diff to")
        if not v:
            return None
        p = Path(v) / "diff"
    else:
        p = Path("diff")

    i = 1
    while True:
        try:
            p.mkdir(parents=True, exist_ok=False)
            return p
        except FileExistsError:
            p = p.parent / f'diff-{i}'
            i += 1


if __name__ == "__main__":
    try:
        main()
    finally:
        if platform.system() == "Windows":
            input("Press enter to close console")
