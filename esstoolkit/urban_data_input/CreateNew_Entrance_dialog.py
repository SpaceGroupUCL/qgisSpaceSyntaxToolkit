# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CreateNew_EntranceDialog
                                 A QGIS plugin
 CreateNew_Entrance
                             -------------------
        begin                : 2016-08-16
        git sha              : $Format:%H$
        copyright            : (C) 2016 by AA
        email                : AA
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
    os.path.dirname(__file__), 'CreateNew_Entrance_dialog_base.ui'))


class CreateNew_EntranceDialog(QtGui.QDialog, FORM_CLASS):
    create_new_layer = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(CreateNew_EntranceDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # setup signals
        self.pushButtonSelectLocationEntrance.clicked.connect(self.selectSaveLocationEntrance)
        self.pushButtonEntrancesNewFileDLG.clicked.connect(self.newEntranceLayer)
        self.closePopUpEntrancesButton.clicked.connect(self.closePopUpEntrances)

    def closePopUpEntrances(self):
        self.close()

    # Open Save file dialogue and set location in text edit
    def selectSaveLocationEntrance(self):
        filename = QtGui.QFileDialog.getSaveFileName(None, "Select Save Location ", "", '*.shp')
        self.lineEditEntrances.setText(filename)

    def newEntranceLayer(self):
        self.create_new_layer.emit()
