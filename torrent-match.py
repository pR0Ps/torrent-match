#!/usr/bin/env python3

import os
import subprocess
import sys


def has_cmd(cmd):
    try:
        # command is a shell builtin, won't work without shell=True
        subprocess.check_call("command -v '{}'".format(cmd), shell=True, stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def print_tors(s):
    for x in s:
        print ("  {}".format(x.encode("utf-8").decode("utf-8", "replace")))

def collect_torrents(torrent_dir):
    tor_tor = set()
    tor_data = set()
    for x in os.listdir(torrent_dir):
        if not x.endswith(".torrent"):
            continue

        tor_tor.add(x)
        path = os.path.join(os.getcwd(), torrent_dir, x)

        try:
            temp = subprocess.check_output(["lstor", "--skip-validation", "--quiet", "-o", "info.name", path], stderr=subprocess.DEVNULL).decode("utf-8", "surrogateescape")[:-1]
            if not temp:
                raise ValueError("No file/folder name specified")
        except Exception as e:
            print ("Couldn't check '{}': {}".format(path, e))
        else:
            tor_data.add(temp)
    return tor_tor, tor_data

def main():
    if len(sys.argv) != 3:
        print ("Checks a directory of torrents against a data directory and points out any differences")
        print ("For example, a file in the data folder with no matching torrent or vice versa")
        print ("  Usage: {} <torrent dir> <data dir>".format(os.path.basename(__file__)))
        return

    if not has_cmd("lstor"):
        print("This script requires the 'lstor' command")
        print("Install it from https://github.com/pyroscope/pyrocore") 
        return

    # Normalize and strip trailing slashes
    torrent_dir = os.path.normpath(sys.argv[1])
    data_dir = os.path.normpath(sys.argv[2])

    print ("Getting file/folder names from torrents...")
    tor_tor, tor_data = collect_torrents(torrent_dir)

    rt_tor = None
    if has_cmd("rtcontrol"):
        print ("Getting a list of file/folder names from rTorrent...")
        try:
            temp = subprocess.check_output(["rtcontrol", "--quiet", "directory={}*".format(data_dir), "-o", "metafile.pathbase"], stderr=subprocess.DEVNULL).decode("utf-8", "surrogateescape")[:-1]
        except Exception as e:
            print ("Couldn't get torrent listing from rTorrent: {}".format(e))
        else:
            rt_tor = set(temp.split('\n'))

    print("Getting file list from data directory...")
    data_data = set(os.listdir(data_dir))

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

