#!/usr/bin/env python3

import argparse
from pynput.keyboard import Key, Controller
from time import sleep


def main():
    parser = argparse.ArgumentParser(
        prog="no-sleep.py",
        description="Prevents the machine from going to sleep by emitting a key press and release periodically."
    )
    parser.add_argument("-k", "--key",
                        default="print_screen",
                        help="Sets the key to use",
                        type=key_type)
    parser.add_argument("-s", "--sleep-seconds",
                        default=5 * 60,
                        help="Sets the number of seconds to sleep in-between key presses")
    args = parser.parse_args()
    key = args.key
    seconds = args.sleep_seconds

    kb = Controller()

    while True:
        print('print_screen')
        kb.press(key)
        kb.release(key)
        sleep(seconds)


def key_type(v: str):
    try:
        return Key[v]
    except KeyError:
        raise argparse.ArgumentTypeError(f"{v} is not a valid option; choose from: {[e.name for e in Key]}")


if __name__ == "__main__":
    main()
