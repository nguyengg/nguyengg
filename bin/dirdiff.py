#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path
from tkinter import Tk
from typing import Callable, Iterator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Finds and copies files present in one directory but not the other.",
    )

    generate = object()
    parser.add_argument(
        "-c",
        "--copy-to",
        dest="copy_dir",
        nargs="?",
        const=generate,
        default=None,
        help="if given a directory, the files will be copied into this path. If given an empty string, an empty "
             "directory with a unique name (diff or diff-1 or diff-2 etc.) will be created. If absent, only print the "
             "diff to standard output.",
    )
    parser.add_argument(
        "-e",
        "--ext",
        action="append",
        dest="ext",
        help="one or more file extensions to filter results. If none are given, all file extensions are included in "
             "diff computation. The flag values are implicitly prefixed with '.' if not explicitly prefixed.",
    )
    parser.add_argument(
        "a",
        nargs="?",
        type=str,
        help="the first directory; if not given, open a dialog select an existing directory",
    )
    parser.add_argument(
        "b",
        nargs="?",
        type=str,
        help="the second directory; if not given, open a dialog to select an existing directory",
    )

    args = parser.parse_args()
    if args.a is None:
        a = askdirectory(title="Select first directory")
        if not a:
            exit(1)
        a = Path(a)
    else:
        a = Path(args.a)

    if args.b is None:
        b = askdirectory(initialdir=a.parent, title=f"Select second directory to compare against '{a}'")
        if not b:
            exit(1)
        b = Path(b)
    else:
        b = Path(args.b)

    copy_dir: Path | None = None
    if args.copy_dir is generate:
        try:
            initialdir = os.path.commonpath([a, b])
        except ValueError:
            initialdir = b.parent
        copy_dir = gen_copy_dir(askparentdir=args.a is None or args.b is None, initialdir=initialdir)
    elif args.copy_dir:
        copy_dir = Path(args.copy_dir)
        copy_dir.mkdir(parents=True, exist_ok=True)

    filename_filter = default_filter
    if args.ext:
        import re

        p = re.compile(f"\\.({'|'.join(e.removeprefix(".") for e in args.ext)})")
        filename_filter = p.fullmatch

    if copy_dir:
        for x, y in walk_cmp(a, b, filename_filter):
            if x:
                x = x.relative_to(a)
                print(f"<<< {x}")
                dst = copy_dir / x
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(a / x, dst)
            else:
                y = y.relative_to(b)
                print(f"\t>>> {y}")
                dst = copy_dir / y
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(b / y, dst)
    else:
        for x, y in walk_cmp(a, b, filename_filter):
            if x:
                print(f"<<< {x.relative_to(a)}")
            else:
                print(f"\t>>> {y.relative_to(b)}")

    if os.name == "nt":
        input("Press enter to close console")


tk: Tk | None = None


def askdirectory(initialdir=None, title="Select directory") -> Path | None:
    global tk
    if tk is None:
        tk = Tk()
        tk.withdraw()

    from tkinter.filedialog import askdirectory

    v = askdirectory(initialdir=initialdir, title=title, mustexist=True)
    if v:
        return Path(v)


def gen_copy_dir(askparentdir=False, initialdir=None) -> Path | None:
    if askparentdir:
        v = askdirectory(initialdir=initialdir, title="Select parent directory that will contain the diff-* directory")
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
            p = p.parent / f"diff-{i}"
            i += 1


def default_filter(*_):
    return True


def walk_orderly(root: Path, filename_filter: Callable[[str], bool]) -> Iterator[Path]:
    for root, dirs, files in root.walk():
        dirs.sort()
        files.sort()
        for f in filter(filename_filter, files):
            yield Path(root, f)


def walk_cmp(a: Path, b: Path, filename_filter: Callable[[str], bool]) -> Iterator[tuple[Path | None, Path | None]]:
    a_walker = walk_orderly(a, filename_filter)
    b_walker = walk_orderly(b, filename_filter)

    while True:
        try:
            x = next(a_walker)
            rel_a = str(x.relative_to(a))
        except StopIteration:
            for f in b_walker:
                yield None, f
            return

        try:
            y = next(b_walker)
            rel_b = str(y.relative_to(b))
        except StopIteration:
            if x:
                yield x, None
            for f in a_walker:
                yield f, None
            return

        try:
            while rel_a < rel_b:
                yield x, None
                x = next(a_walker)
                rel_a = str(x.relative_to(a))
        except StopIteration:
            yield None, y
            for f in b_walker:
                yield None, f
            return

        try:
            while rel_a > rel_b:
                yield None, y
                y = next(b_walker)
                rel_b = str(y.relative_to(b))
        except StopIteration:
            yield x, None
            for f in a_walker:
                yield f, None
            return


if __name__ == "__main__":
    main()
