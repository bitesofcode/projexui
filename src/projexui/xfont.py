#!/usr/bin/python

""" Additional font manipulation options. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from projexui.qt import QtGui, QtCore

class XFont(QtGui.QFont):
    def adaptSize(self, text, rect, wordWrap=False, minimum=0.1):
        metrics = QtGui.QFontMetrics(self)
        
        # don't use the word wrap information
        if not wordWrap:
            factor = rect.width() / max(float(metrics.width(text)), 1)
            if factor < 1:
                new_size = self.pointSizeF() * factor
                if new_size < minimum:
                    new_size = minimum
                
                self.setPointSizeF(new_size)
        
        # otherwise, loop through it
        else:
            fit = False
            flags = QtCore.Qt.TextWordWrap | QtCore.Qt.AlignLeft
            for i in range(10):
                bound = metrics.boundingRect(rect, flags, text)
                
                if bound.width() < rect.width() and \
                   bound.height() < rect.height():
                    break
                
                break_it = False
                new_size = self.pointSizeF() - 0.25
                if new_size < minimum:
                    new_size = minimum
                    break_it = True
                
                self.setPointSizeF(new_size)
                if break_it:
                    break

