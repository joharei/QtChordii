import sys

from cx_Freeze import setup, Executable
from gui.warningmessagebox import WarningMessageBox

includes = ['syntax']
includefiles = ['gui\warningmessagebox.py',
                'gui\mainwindow.py',
                'gui\customtextedit.py',
                'gui\customtreeview.py',
                'tab2chordpro\Transpose.py']
#includes = []

build_exe_options = {"packages": ["re"],
                     "includes": includes,
                     "include_files": includefiles}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name='QtChordii',
    version='0.1',
    packages=[''],
    url='',
    license='GPLv3',
    author='Johan Reitan',
    author_email='johan.reitan@gmail.com',
    description='A simple GUI for Chordii making organizing of songbooks easier.',
    options = {"build_exe" : build_exe_options},
    executables = [Executable("main.py", base = base)]
)