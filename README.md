QtChordii
=========

"Chordii's purpose is to provide guitar players with a tool to produce
good looking, self-descriptive music sheets from text files." - [Chordii's README](https://github.com/meonkeys/chordii)

QtCordii utilizes the command line tool Chordii, and aims to provide an easy-to-use GUI making it easier to manage 
songbook projects with multiple songs.

For more information about Chordii, check out their website: http://chordii.sourceforge.net/

To run, execute main.py with Python 3:

    $ python3 main.py

Features
--------

Currently, QtChordii lists a directory of .cho/.crd files (ChordPro files, see Chordii's 
[documentation](http://www.vromans.org/johan/projects/Chordii/documentation/index.html) for more), and lets you edit
these files. It provides syntax highlighting, and uses Chordii to produce output as PostScript.

Since this software is written in Python and Qt, it should be platform independent, though it is only tested on linux
as of yet. The plan is to have it run on Windows and MacOS as well.

QtChordii is still in the early stages of development, and does for the moment offer few features beyond the ones 
mentioned.

In the future, the intention is to support all the options Chordii has to offer, as well as output preview and PDF 
export.

Dependencies
------------

*   Python 3
*   PyQt4
*   popplerqt4
*   chordii
*   ps2pdf

Copyright
---------

Copyright (C) 2013, 2014 Johan Reitan.

QtChordii is licensed following the conditions of the GNU Public License version 3 or later. See COPYING for the full
license text.
