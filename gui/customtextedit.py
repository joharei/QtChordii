# Copyright 2013 Johan Reitan
#
# This file is part of QtChordii.
#
# QtChordii is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# QtChordii is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with QtChordii.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4 import QtGui
from PyQt4.QtGui import QTextEdit
from syntax import ChordProHighlighter


class CustomTextEdit(QTextEdit):
    def __init__(self, parent):
        super(CustomTextEdit, self).__init__(parent)
        self.main = None

        font = QtGui.QFont()
        font.setFamily("Courier")
        font.setFixedPitch(True)
        font.setPointSize(10)

        self.setFont(font)
        self.highlighter = ChordProHighlighter(self.document())

        self.setReadOnly(True)

        self.setAcceptRichText(False)

    def set_main(self, main):
        self.main = main

    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())
        if not self.main is None:
            self.main.tab2chordpro()