# Copyright (C) 2013, 2014 Johan Reitan
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

from PyQt4.QtGui import *


class WarningMessageBox(QMessageBox):

    def __init__(self, *args, **kwargs):
        super(WarningMessageBox, self).__init__(*args, **kwargs)
        self.detail_box_size = None

    def resizeEvent(self, event):

        result = super(WarningMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QTextEdit)
        if self.detail_box_size is None:
            self.detail_box_size = details_box.viewport().size()
        if details_box is not None:
            details_box.setFixedSize(self.detail_box_size)

        return result