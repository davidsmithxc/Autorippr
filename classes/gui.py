#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode PyQt4 tutorial 

In this example, we create a bit
more complicated window layout using
the QtGui.QGridLayout manager. 

author: Jan Bodnar
website: zetcode.com 
last edited: October 2011
"""

import sys
from PyQt4 import QtGui


class Ui_MainWindow(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def setupUi(self, junk):
        
        # Demo
        if False:
            title = QtGui.QLabel('Title')
            author = QtGui.QLabel('Author')
            review = QtGui.QLabel('Review')

            titleEdit = QtGui.QLineEdit()
            authorEdit = QtGui.QLineEdit()
            reviewEdit = QtGui.QTextEdit()

            grid = QtGui.QGridLayout()
            grid.setSpacing(10)

            grid.addWidget(title, 1, 0)
            grid.addWidget(titleEdit, 1, 1)

            grid.addWidget(author, 2, 0)
            grid.addWidget(authorEdit, 2, 1)

            grid.addWidget(review, 3, 0)
            grid.addWidget(reviewEdit, 3, 1, 5, 1)
            
            self.setLayout(grid) 
            
            self.setGeometry(300, 300, 350, 300)
            self.setWindowTitle('Review')    
            self.show()

        # Autorippr
        else:
            grid = QtGui.QGridLayout()
            grid.setSpacing(5)

            # buttons
            self.buttonDiscInfo = QtGui.QPushButton()
            self.buttonDiscInfo.setText('Disk Info')

            self.buttonRip = QtGui.QPushButton()
            self.buttonRip.setText('Rip')

            self.buttonCompress = QtGui.QPushButton()
            self.buttonCompress.setText('Compress')

            self.buttonTvInfo = QtGui.QPushButton()
            self.buttonTvInfo.setText('TV Info')

            self.buttonFB = QtGui.QPushButton()
            self.buttonFB.setText('Filebot')

            # check boxes
            self.checkTV = QtGui.QCheckBox()
            self.checkTV.setText('TV Show')

            # combo boxes
            self.comboSeasons = QtGui.QComboBox()

            # line edit
            self.textEditShowTitle = QtGui.QLineEdit()
            self.lineEditNumbers = QtGui.QLineEdit()

            # tables
            self.tableWidget = QtGui.QTableWidget()
            self.listView = QtGui.QListView()

            # create some spacers
            self.spacer = QtGui.QSpacerItem(20, 20)

            # Add buttons to layout
            grid.addWidget(self.buttonDiscInfo, 0, 0)
            grid.addWidget(self.buttonRip, 1, 0)
            grid.addWidget(self.buttonCompress, 2, 0)

            grid.addWidget(self.checkTV, 0, 1)
            grid.addWidget(self.buttonTvInfo, 1, 1)
            grid.addWidget(self.buttonFB, 2, 1)


            # add other items
            self.groupBox = QtGui.QGroupBox()
            self.groupBox.setTitle('Show/Ep Info')
            grid.addWidget(self.groupBox, 0, 2, 3, 5)

            grid.addItem(self.spacer, 1, 2)
            grid.addWidget(self.textEditShowTitle, 1, 3)
            grid.addWidget(self.comboSeasons, 1, 4)
            grid.addWidget(self.lineEditNumbers, 1, 5)
            grid.addItem(self.spacer, 1, 6)

            # add tables
            grid.addWidget(self.tableWidget, 3, 0, 4, 7)
            grid.addWidget(self.listView, 7, 0, 4, 7)

            # set lay out and show
            self.setLayout(grid) 
            
            self.setGeometry(300, 300, 350, 300)
            self.setWindowTitle('Review')    
            self.show()



        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
