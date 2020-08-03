# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CreateNew_LUDialog
                                 A QGIS plugin
 CreateNew_LU
                             -------------------
        begin                : 2016-10-17
        git sha              : $Format:%H$
        copyright            : (C) 2016 by CreateNew_LU
        email                : CreateNew_LU
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

from qgis.PyQt import QtCore, QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'CreateNew_LU_dialog_base.ui'))


class CreateNew_LUDialog(QtGui.QDialog, FORM_CLASS):
    create_new_layer = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(CreateNew_LUDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # setup signals
        self.pushButtonSelectLocationLU.clicked.connect(self.selectSaveLocationLU)
        self.pushButtonLUNewFileDLG.clicked.connect(self.newLULayer)
        self.closePopUpLUButton.clicked.connect(self.closePopUpLU)

    def closePopUpLU(self):
        self.close()

    # Open Save file dialogue and set location in text edit
    def selectSaveLocationLU(self):
        filename = QtGui.QFileDialog.getSaveFileName(None, "Select Save Location ", "", '*.shp')
        self.lineEditLU.setText(filename)

    def newLULayer(self):
        self.create_new_layer.emit()

    def getSelectedLULayerID(self):
        return self.selectIDbuildingCombo.currentText()