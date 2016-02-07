# coding: utf-8

# Copyright (C) 2013-2016 Johan Reitan
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

from PyQt5 import uic
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QDialog, QLayout, QFileDialog, QDesktopWidget


class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('gui/qtchordii/welcomedialog.ui', self)

        self.ui.new_project_btn.clicked.connect(self.new_project)
        self.ui.open_project_btn.clicked.connect(self.open_project)

        self.ui.open_project_btn.setFocus()

        self.ui.welcome_label.setText(
                self.tr("Welcome to QtChordii!\nPlease create a new songbook project, or load an existing one."))

        self.ui.layout().setSizeConstraint(QLayout.SetFixedSize)

        self.center()

        self.filename = None
        self.new_file = False

    def center(self):
        center_point = QDesktopWidget().availableGeometry().center()
        geometry = self.frameGeometry()
        geometry.moveCenter(center_point)
        self.move(geometry.topLeft())

    def new_project(self):
        self.filename = QFileDialog.getSaveFileName(self, self.tr("New project"), QDir.homePath(),
                                                    self.tr("Chordii project files (*.chproj)"))[0]
        self.new_file = True
        self.close()

    def open_project(self):
        self.filename = QFileDialog.getOpenFileName(self, self.tr("Open project"), QDir.homePath(),
                                                    self.tr("Chordii project files (*.chproj)"))[0]
        self.close()

    @staticmethod
    def get_project(parent=None):
        dialog = WelcomeDialog(parent)
        dialog.exec_()
        return dialog.filename, dialog.new_file
