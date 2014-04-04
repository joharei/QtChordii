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

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter


def font_format(color, style=''):
    """
    Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': font_format('olive'),
    'argument': font_format('darkcyan'),
    'curlyBrace': font_format('orange'),
    'chord': font_format('firebrick'),
    'chorus': font_format('yellow', 'bold')
}


class ChordProHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for the ChordPro language.
    """
    # ChordPro keywords
    keywords = [
        'new_song', 'ns', 'start_of_chorus', 'soc', 'end_of_chorus', 'eoc', 'start_of_tab', 'sot', 'end_of_tab', 'eot',
        'define', 'no_grid', 'ng', 'grid', 'g', 'new_page', 'np', 'new_physical_page', 'npp', 'column_break', 'colb'
    ]
    argumentKeywords = [
        'title', 't', 'subtitle', 'st', 'comment', 'c', 'comment_italic', 'ci', 'comment_box', 'cb', 'textfont',
        'textsize', 'chordfont', 'chordsize', 'titles', 'columns', 'col', 'pagetype'
    ]
    keywords.extend(argumentKeywords)

    # Braces
    curlyBraces = [
        '\{', '\}',
    ]
    squareBraces = [
        '\[', '\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        self.start_of_chorus = (QRegExp("\{soc\}"), QRegExp("\{eoc\}"), 1, STYLES['chorus'])

        rules = []

        # Rules
        # TODO: make a nice rule for chord definition
        # TODO: make rules for keywords that take special arguments (like numbers)
        rules += [(r'\{%s\:(.)*\}' % w, 0, STYLES['argument']) for w in ChordProHighlighter.argumentKeywords]
        rules += [(r'\{%s\:?' % w, 0, STYLES['keyword']) for w in ChordProHighlighter.keywords]
        rules += [(r'%s' % b, 0, STYLES['curlyBrace']) for b in ChordProHighlighter.curlyBraces]
        rules += [(r'\[[^\]]*\]', 0, STYLES['chord'])]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, fmt in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        # TODO: Stop this from overriding the existing style
        # in_multiline = self.match_multiline(text, *self.start_of_chorus)

    def match_multiline(self, text, starting_delimiter, ending_delimiter, in_state, style):
        """
        Highlight multiline text between starting_delimiter and ending_delimiter
        :param text: text to be highlighted
        :param starting_delimiter: QRegExp for the starting delimiter
        :param ending_delimiter: QRegExp for the ending delimiter
        :param in_state: unique integer defining if text is between delimiters
        :param style: the style to apply
        :return: True if we are still inside the multi-line, False otherwise
        """
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = starting_delimiter.indexIn(text)
            # Move past this match
            add = starting_delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = ending_delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + ending_delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
                # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = starting_delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False