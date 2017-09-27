#!/usr/bin/env python3

import argparse
import os
import subprocess
import shutil
import sys

from bencodepy import decode_from_file, DecodingError


def run_command(*args, **kwargs):
    p = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         **kwargs)
    out, err = (x.decode("utf-8", errors="replace").strip() for x in p.communicate())
    return p.returncode, out, err


def print_torrents(torrents):
    for t in sorted(torrents):
        print("  {}".format(t))


def collect_torrents(torrent_dirs):
    print("Getting file/folder names from torrents...")
    torrent_files = set()
    target_names = set()
    for d in torrent_dirs:
        for x in os.scandir(d):
            if not x.is_file() or not x.name.endswith(".torrent"):
                continue

            try:
                path = os.path.abspath(os.path.join(os.getcwd(), x.path))
                data = decode_from_file(path)
                name = data[b"info"][b"name"].decode("utf-8", errors="replace")
            except (OSError, DecodingError, KeyError) as e:
                print("Couldn't check '{}': {}".format(path, e))
            else:
                torrent_files.add(path)
                target_names.add(name)

    return torrent_files, target_names


def collect_rtorrent(data_dir):
    if not shutil.which("rtcontrol"):
        print("WARNING: 'rtcontrol' not found, not analyzing rTorrent data")
        return None

    # Remove trailing slash if it exists
    data_dir = os.path.normpath(os.path.abspath(data_dir))

    # directory is different if the torrent data is a single file or a folder
    dir_filter_files="directory={}".format(data_dir)
    dir_filter_folders="directory={}/*".format(data_dir)

    print("Getting a list of file/folder names from rTorrent...")
    code, out, err = run_command(["rtcontrol", "--quiet", "-o", "metafile",
                                  dir_filter_files, "OR", dir_filter_folders])
    if code != 0 and code != 44:
        print("Couldn't get torrent listing from rTorrent (exit code {})"
              "".format(code))
        if err or out:
            print("  {}".format(err or out))

        return None

    # rTorrent seems to return paths with a leading double slash
    return set(x[1:] if x.startswith("//") else x
               for x in out.splitlines())


def collect_data_dir(data_dir):
    print("Getting file list from data directory...")
    return set(x.name for x in os.scandir(data_dir))


def main():
    if sys.version_info < (3, 3):
        print("torrent-match requires Python 3.3+ to run")
        return 2

    parser = argparse.ArgumentParser(
        description="Checks a directory of torrents against a data directory "
                    "and points out any differences.\n"
                    "Can optionally check the torrent files against rTorrent."
    )
    parser.add_argument("data_dir", type=str,
                        help="The directory the torrent data is stored in")
    parser.add_argument("torrent_dirs", nargs="+", type=str,
                        help="The directories to find *.torrent files in")
    parser.add_argument("-r", "--rtorrent", action="store_true",
                        help="Check against rtorrent to see if files are "
                             "properly loaded (requires 'rtcontrol', see "
                             "https://pyrocore.readthedocs.io)")

    config = parser.parse_args()

    rt_torrents = None
    data_dir = collect_data_dir(config.data_dir)
    torrent_files, torrent_data = collect_torrents(config.torrent_dirs)
    if config.rtorrent:
        rt_torrents = collect_rtorrent(config.data_dir)

    ret_code = 0
    print("\nAnalysis complete")
    print("-----------------")
    if rt_torrents is not None:
        missing_loaded = torrent_files - rt_torrents
        extra_loaded = rt_torrents - torrent_files

        if not missing_loaded and not extra_loaded:
            print("Torrent files are in sync with rTorrent")
        else:
            ret_code = 1
            if missing_loaded:
                print("The following torrents from the torrent dir(s) aren't loaded in rTorrent:")
                print_torrents(missing_loaded)
            if extra_loaded:
                print("The following extra torrents downloading into the data directory are loaded in rTorrent:")
                print_torrents(extra_loaded)

    missing_data = torrent_data - data_dir
    all_extra = data_dir - torrent_data
    extra_symlinks = set(x for x in all_extra if os.path.islink(os.path.join(config.data_dir, x)))
    extra_data = all_extra - extra_symlinks

    # Special case for all symlinks
    # - Extra symlinks to data outside the data directory are invalid
    # - Extra symlinks to data inside the data directory are valid
    symlink_data = {x: os.path.relpath(os.path.realpath(os.path.join(config.data_dir, x))) for x in extra_symlinks}
    invalid_symlinks = list("{} -> {}".format(name, path) for name, path in symlink_data.items() if os.path.dirname(path))


    if not missing_data and not extra_data:
        print("Data files/folders are in sync with the torrent files")
    else:
        ret_code = 1
        if extra_data:
            print("The following folders don't have a matching torrent:")
            print_torrents(extra_data)
        if missing_data:
            print("The following torrents don't have their matching files (were they renamed?):")
            print_torrents(missing_data)
        if invalid_symlinks:
            print("The following symlinks to external content don't have a matching torrent:")
            print_torrents(invalid_symlinks)

    return ret_code


if __name__ == "__main__":
    sys.exit(main())
