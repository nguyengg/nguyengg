#!/usr/bin/env python3

import argparse
import os
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
        "a",
        type=str,
        help="the first directory",
    )
    parser.add_argument(
        "b",
        type=str,
        help="the second directory",
    )

    args = parser.parse_args()

    a = Path(args.a)
    b = Path(args.b)
    copy_dir = args.copy_dir

    common_path = os.path.commonpath((a, b))
    a_rel = a.relative_to(common_path)
    b_rel = b.relative_to(common_path)
    a_files = {
        Path(root, filename).relative_to(a)
        for (root, _, filenames) in a.walk()
        for filename in filenames
    }
    b_files = {
        Path(root, filename).relative_to(b)
        for (root, _, filenames) in b.walk()
        for filename in filenames
    }
    in_a_only, in_b_only = (a_files - b_files), (b_files - a_files)

    if copy_dir is generate:
        i = 1
        copy_dir = "diff"
        while True:
            try:
                os.makedirs(copy_dir, exist_ok=False)
                copy_dir = Path(copy_dir)
                break
            except FileExistsError:
                copy_dir = f'diff-{i}'
                i += 1
    elif copy_dir:
        copy_dir = Path(copy_dir)
        copy_dir.mkdir(exist_ok=True)
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


if __name__ == "__main__":
    main()
