#!/usr/bin/env python3

import sys
import os
import subprocess

NAME = "torrent-match"
VERSION = "0.1.0"

def main():

    # TODO: argparse
    # TODO: quiet mode
    # TODO: porcelain mode
    num_args = len(sys.argv) - 1
    if num_args:
        if sys.argv[1] in ("-h", "--help"):
            print ("Usage: {} [options] <torrent dir> <data dir>".format(NAME))
            print ()
            print ("{} {}".format(NAME, VERSION))
            print ()
            print ("Checks a directory of torrents against a data directory and points out any differences.")
            print ("Examples:")
            print (" - a file in the data folder with no matching torrent")
            print (" - a torrent in the torrent folder with it's content downloaded to a different folder")
            print (" - a torrent in the torrent folder that hasn't been downloaded")
            print ()
            print ("Options:")
            print ("  --version        Print version information")
            print ("  -h, --help       Print this help text")
            print ()
            print ("Requires the 'lstor' tool (part of the 'pyrocore' package)")
            print ()
            return
        elif sys.argv[1] == "--version":
            print ("{} {}".format(NAME, VERSION))
            return

    if num_args != 2:
        print ("Invalid arguments (\"{} --help\" for help)".format(NAME))
        return

    # TODO: Use the python library instead of going to the system?
    try:
        if subprocess.call(["lstor", "--version"]) != 0:
            raise EnvironmentError()
    except EnvironmentError:
        print ("Error: couldn't find the 'lstor' tool ('pyrocore' installed and in the path?)")
        return

    print ("Getting file/folder names from torrents...")
    data = {}
    for x in os.listdir(sys.argv[1]):
        if not x.endswith(".torrent"):
            continue

        path = os.path.join(os.getcwd(), sys.argv[1], x)

        try:
            temp = subprocess.check_output(["lstor", "-q", "-V", "-o", "info.name", path]).decode("utf-8", "surrogateescape")[:-1]
            if not temp:
                raise ValueError("No file/folder info returned from 'lstor'")
        except (subprocess.CalledProcessError, UnicodeDecodeError, ValueError) as e:
            print ("Couldn't check '{}': {}".format(path, e)) 
            continue

        data[x] = temp

    print ("Checking files/folders against the torrent files...")
    files = set(os.listdir(sys.argv[2]))
    torrents = set(data.values())

    extra = files - torrents
    missing = torrents - files

    def print_tors(s):
        for x in s:
            print ("  {}".format(x.encode("utf-8").decode("utf-8", "replace")))

    print ("Analysis complete")
    if not missing and not extra:
        print ("Files/folders are in sync with the torrent files")
    else:
        if extra:
            print ("The following folders don't have a matched torrent:")
            print_tors(extra)
        if missing:
            print ("The following torrents don't have their matching files:")
            print_tors(missing)
            print (missing)


if __name__ == "__main__":
    main()
