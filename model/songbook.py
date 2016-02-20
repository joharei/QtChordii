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
import os

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
        project_dir = os.path.dirname(filename)
        json_object = json.load(open(filename, 'r'))
        self.name = json_object['name']
        self.songs = [
            Song(song_object['title'], song_object['artist'], os.path.join(project_dir, song_object['file_path']))
            for song_object in json_object['songs']]

    def save(self, filename):
        project_dir = os.path.dirname(filename)
        dict_to_serialize = {
            'name': self.name,
            'songs': [{
                          'artist': song.artist,
                          'title': song.title,
                          'file_path': os.path.relpath(song.file_path, project_dir)
                      } for song in self.songs]
        }
        json.dump(dict_to_serialize, open(filename, 'w'), indent=4)
