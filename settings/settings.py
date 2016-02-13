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

from PyQt5.QtCore import QSettings, QCoreApplication, QSize, QPoint

APPLICATION_NAME = 'QtChordii'
main_window_group = 'MainWindow'
key_size = 'size'
key_pos = 'pos'
key_is_full_screen = 'is_full_screen'
key_splitter_sizes = 'splitter_sizes'


def set_up_settings():
    QCoreApplication.setOrganizationName(APPLICATION_NAME)
    QCoreApplication.setApplicationName(APPLICATION_NAME)


def save_window_geometry(size, pos, is_full_screen, splitter_sizes):
    settings = QSettings()
    settings.beginGroup(main_window_group)
    settings.setValue(key_size, size)
    settings.setValue(key_pos, pos)
    settings.setValue(key_is_full_screen, is_full_screen)
    settings.setValue(key_splitter_sizes, splitter_sizes)
    settings.endGroup()


def load_window_geometry():
    settings = QSettings()
    settings.beginGroup(main_window_group)
    size = settings.value(key_size, type=QSize)
    pos = settings.value(key_pos, type=QPoint)
    is_full_screen = settings.value(key_is_full_screen, type=bool)
    splitter_sizes = settings.value(key_splitter_sizes, type=int)
    settings.endGroup()
    return {key_size: size, key_pos: pos, key_is_full_screen: is_full_screen, key_splitter_sizes: splitter_sizes}
