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

import json

from model.song import Song


class Songbook:
    def __init__(self, name='Songbook'):
        self.name = name
        self.songs = []

    def add_song(self, title, artist, file_path):
        self.songs.append(Song(title, artist, file_path))

    def clear(self):
        self.songs.clear()

    def load(self, filename):
        json_object = json.load(open(filename, 'r'))
        self.name = json_object['name']
        for song_object in json_object['songs']:
            song = Song()
            song.__dict__ = song_object
            self.songs.append(song)

    def save(self, filename):
        dict_to_serialize = {'name': self.name, 'songs': [song.__dict__ for song in self.songs]}
        json.dump(dict_to_serialize, open(filename, 'w'), indent=4)
