# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-02-29
# copyright            : (C) 2016 by Space Syntax Limited
# author               : Stephen Law
# email                : s.law@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" This plugin performs basic transformation on a line in qgis.
"""

import os.path

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'network_transformer_dialog_base.ui'))


class NetworkTransformerDialog(QDialog, FORM_CLASS):

    ############################ initialisation ############################

    def __init__(self, parent=None):
        """Constructor."""
        super(NetworkTransformerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # this turns on rotate,resize,rescale signals
        self.rotate_radio.toggled.connect(self.disable_button)
        self.resize_radio.toggled.connect(self.disable_button)
        self.rescale_radio.toggled.connect(self.disable_button)

        # rotate_button is checked for default
        self.rotate_radio.click()

    # define a series of get/set/update/disable function

    # update layer - fill combo with layer lists
    def update_layer(self, layer_objects):
        self.comboBox.clear()
        if layer_objects:
            for layer in layer_objects:
                self.comboBox.addItem(layer[0], layer[1])
            self.disable_all(False)
            self.disable_button()
        else:
            self.comboBox.addItem('No vector layer found.')
            self.disable_all(True)

    # get layer - retrieving the value of the current selected layer
    def get_layer(self):
        index = self.comboBox.currentIndex()
        layer = self.comboBox.itemData(index)
        return layer

    # get transformation - this will retrieve which transformation and value of transformation
    def get_transformation(self):
        transformation = 0
        value = 0
        if self.rotate_radio.isChecked():
            transformation = 1
            value = self.rotate_spinBox.value()
        elif self.resize_radio.isChecked():
            transformation = 2
            value = self.resize_spinBox.value()
        elif self.rescale_radio.isChecked():
            transformation = 3
            value = self.rescale_spinBox.value()
        return transformation, value

    # disable buttons - this disables the other transformation when one is checked.
    def disable_button(self):
        if self.rotate_radio.isChecked():
            self.rotate_spinBox.setEnabled(True)
            self.resize_spinBox.setEnabled(False)
            self.rescale_spinBox.setEnabled(False)
        elif self.resize_radio.isChecked():
            self.resize_spinBox.setEnabled(True)
            self.rotate_spinBox.setEnabled(False)
            self.rescale_spinBox.setEnabled(False)
        elif self.rescale_radio.isChecked():
            self.rescale_spinBox.setEnabled(True)
            self.rotate_spinBox.setEnabled(False)
            self.resize_spinBox.setEnabled(False)

    # disable all buttons if no layer is available
    def disable_all(self, onoff):
        self.rotate_radio.setDisabled(onoff)
        self.rotate_spinBox.setDisabled(onoff)
        self.resize_radio.setDisabled(onoff)
        self.resize_spinBox.setDisabled(onoff)
        self.rescale_radio.setDisabled(onoff)
        self.rescale_spinBox.setDisabled(onoff)
        self.run_button.setDisabled(onoff)
