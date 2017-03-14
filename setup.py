#!/usr/bin/env python

from setuptools import setup

setup(name="torrent-match",
      version="0.0.1",
      description="Match torrent files against a download directory",
      url="https://github.com/pR0Ps/torrent-match",
      license="MIT",
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
      ],
      packages=["torrentmatch"],
      install_requires=["bencodepy >= 0.9.5"],
      entry_points={'console_scripts': ["torrent-match=torrentmatch.torrentmatch:main"]}
)
