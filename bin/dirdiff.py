#!/usr/bin/env python3

import argparse, os, shutil


def generate_path():
    i: int = 0
    name = "diff"
    while True:
        try:
            os.makedirs(name, exist_ok=False)
            return name
        except FileExistsError:
            i += 1
            name = f'diff-{i}'


def main():
    parser = argparse.ArgumentParser(description="Finds and copies files present in one directory but not the other.")

    parser.add_argument("-p", "--path", dest="path", nargs='?', const=generate_path, default=None,
                        help="if given a directory, the files will be copied into this path; if given an empty "
                             "string, an empty directory with a unique name with 'diff' prefix will be created.")
    parser.add_argument("a", type=str, help="the first directory")
    parser.add_argument("b", type=str, help="the second directory")
    parser.add_argument("--with-extension", action='store_false', dest="ignore_extension", default=True, required=False,
                        help="if given, file extension will be used as part of the diff; by default it is ignored")

    args = parser.parse_args()
    a, b, path, ignore_extension = args.a, args.b, args.path, args.ignore_extension

    common_path = os.path.commonpath((a, b))
    a_rel, b_rel = os.path.relpath(a, start=common_path), os.path.relpath(b, start=common_path)

    a_files = {os.path.relpath(os.path.join(dirpath, filename), start=a) for (dirpath, _, filenames) in os.walk(a) for
               filename in filenames}
    b_files = {os.path.relpath(os.path.join(dirpath, filename), start=b) for (dirpath, _, filenames) in os.walk(b) for
               filename in filenames}
    in_a, in_b = (a_files - b_files), (b_files - a_files)
    if ignore_extension:
        noext = lambda rp: os.path.splitext(os.path.basename(rp))[0]
        common_files = {noext(a) for a in in_a}.intersection({noext(b) for b in in_b})
        in_a = {a for a in in_a if noext(a) not in common_files}
        in_b = {b for b in in_b if noext(b) not in common_files}

    print("%s has %d files with %d extra" % (a_rel, len(a_files), len(in_a)))
    print("%s has %d files with %d extra" % (b_rel, len(b_files), len(in_b)))

    if path is generate_path:
        path = generate_path()

    if path:
        os.makedirs(path, exist_ok=True)

        for file_relpath in in_a:
            filepath = os.path.join(path, file_relpath)
            dirpath = os.path.dirname(filepath)
            os.makedirs(dirpath, exist_ok=True)
            shutil.copyfile(os.path.join(a, file_relpath), filepath)

        for file_relpath in in_b:
            filepath = os.path.join(path, file_relpath)
            dirpath = os.path.dirname(filepath)
            os.makedirs(dirpath, exist_ok=True)
            shutil.copyfile(os.path.join(b, file_relpath), filepath)


if __name__ == "__main__":
    main()
