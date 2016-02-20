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


def ps2pdf(file_name):
    """
    Converts a file from PostScript to PDF
    :param file_name: Name of the ps file to convert (without extension)
    :rtype: str
    """
    out_file_name = file_name + '.pdf'
    try:
        output = subprocess.check_output(['ps2pdf', file_name + '.ps', out_file_name],
                                         stderr=subprocess.STDOUT).decode()
        print('ps2pdf returned:', output)
    except subprocess.CalledProcessError:
        return None
    finally:
        os.remove(file_name + '.ps')
    return out_file_name
