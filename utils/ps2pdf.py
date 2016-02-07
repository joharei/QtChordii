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

import os
import subprocess


def ps2pdf(file):
    out_file = '{}.pdf'.format(os.path.splitext(file)[0])
    output = subprocess.check_output(['ps2pdf', file, out_file], stderr=subprocess.STDOUT).decode()
    print('ps2pdf returned:', output)
    return out_file
