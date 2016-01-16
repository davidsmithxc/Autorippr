"""
Gui Helper Functions and Classes
"""

from PyQt4 import QtCore, QtGui


class ValidTvTitle(QtGui.QValidator):
    def __init__(self, parent):
        QtGui.QValidator.__init__(self, parent)

    def validate(self, s, pos):
    	containsLine = ('\n' in s) or ('\r' in s)

        if containsLine:
            return (QtGui.QValidator.Invalid, pos)

        elif containsLine is False:
        	return (QtGui.QValidator.Acceptable, pos)
            
    	else:
            return (QtGui.QValidator.Intermediate, pos)


    def fixup(self, s):
        s = s.replace('\r','')
        s = s.replace('\n','')

        return s