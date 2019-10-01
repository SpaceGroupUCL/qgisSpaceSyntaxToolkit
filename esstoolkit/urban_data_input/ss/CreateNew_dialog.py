# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UrbanDataInputDockWidget
                                 A QGIS plugin
 Urban Data Input Tool for QGIS
                             -------------------
        begin                : 2016-06-03
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Abhimanyu Acharya/(C) 2016 by Space Syntax Limited’.
        email                : a.acharya@spacesyntax.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtCore, QtGui, uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'CreateNew_dialog_base.ui'))


class CreatenewDialog(QtGui.QDialog, FORM_CLASS):
    create_new_layer = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(CreatenewDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # setup signals
        self.closePopUpButton.clicked.connect(self.closePopUp)
        self.pushButtonSelectLocation.clicked.connect(self.selectSaveLocation)
        self.pushButtonNewFileDLG.clicked.connect(self.createLayer)


    # Close create new file pop up dialogue when cancel button is pressed
    def closePopUp(self):
        self.close()

    # Open Save file dialogue and set location in text edit
    def selectSaveLocation(self):
        filename = QtGui.QFileDialog.getSaveFileName(None, "Select Save Location ", "", '*.shp')
        self.lineEditFrontages.setText(filename)

    def createLayer(self):
        self.create_new_layer.emit()

