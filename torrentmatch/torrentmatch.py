#!/usr/bin/env python3

import os
import subprocess
import shutil
import sys

from bencodepy import decode_from_file, DecodingError

def print_tors(s):
    for x in s:
        print ("  {}".format(x))

def collect_torrents(torrent_dir):
    print ("Getting file/folder names from torrents...")
    tor_tor = set()
    tor_data = set()
    for x in os.scandir(torrent_dir):
        if not x.is_file() or not x.name.endswith(".torrent"):
            continue

        tor_tor.add(x.name)
        path = os.path.join(os.getcwd(), torrent_dir, x.name)

        data = decode_from_file(path)
        try:
            tor_data.add(data[b"info"][b"name"].decode("utf-8"))
        except (OSError, DecodingError, KeyError) as e:
            print ("Couldn't check '{}': {}".format(path, e))

    return tor_tor, tor_data

def collect_rtorrent():
    if not shutil.which("rtcontrol"):
        return None

    print ("Getting a list of file/folder names from rTorrent...")
    try:
        temp = subprocess.check_output(["rtcontrol", "--quiet", "directory={}*".format(data_dir), "-o", "metafile.pathbase"], stderr=subprocess.DEVNULL).decode("utf-8", "surrogateescape")[:-1]
    except Exception as e:
        print ("Couldn't get torrent listing from rTorrent: {}".format(e))
    else:
        return set(temp.split('\n'))

def collect_data_dir(data_dir):
    print("Getting file list from data directory...")
    return set(x.name for x in os.scandir(data_dir))


def main():
    if len(sys.argv) != 3:
        print ("Checks a directory of torrents against a data directory and points out any differences")
        print ("For example, a file in the data folder with no matching torrent or vice versa")
        print ("  Usage: {} <torrent dir> <data dir>".format(os.path.basename(__file__)))
        return

    # Normalize and strip trailing slashes
    torrent_dir = os.path.normpath(sys.argv[1])
    data_dir = os.path.normpath(sys.argv[2])

    tor_tor, tor_data = collect_torrents(torrent_dir)
    rt_tor = collect_rtorrent()
    data_data = collect_data_dir(data_dir)

    print ("Analyzing collected data")
    if rt_tor is not None:
        missing_loaded = tor_tor - rt_tor
        extra_loaded = rt_tor - tor_tor

    extra_data = data_data - tor_data
    missing_data = tor_data - data_data

    print ("Analysis complete")
    print ("-----------------")
    if rt_tor is not None:
        if not missing_loaded and not extra_loaded:
            print("Torrent files are in sync with rTorrent")
        elif missing_loaded:
            print ("The following torrents aren't loaded in rTorrent")
            print_tors(missing_loaded)
        elif extra_loaded:
            print ("The following extra torrents are loaded in rtorrent")
            print_tors(extra_loaded)

    if not missing_data and not extra_data:
        print ("Files/folders are in sync with the torrent files")
    elif extra_data:
        print ("The following folders don't have a matched torrent:")
        print_tors(extra_data)
    elif missing_data:
        print ("The following torrents don't have their matching files (were they renamed?):")
        print_tors(missing_data)


if __name__ == "__main__":
    main()

