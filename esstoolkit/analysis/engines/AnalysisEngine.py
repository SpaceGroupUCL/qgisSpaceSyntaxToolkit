# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2021-12-02
# copyright            : (C) 2021 by Space Syntax Ltd.
# author               : Petros Koutsolampros
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from qgis.PyQt.QtWidgets import (QWidget, QDockWidget)
from esstoolkit.utilities import layer_field_helpers as lfh


class AnalysisEngine:
    """ Generic Engine Interface Class"""

    @staticmethod
    def get_engine_name() -> str:
        pass

    def create_settings_widget(self, dock_widget: QDockWidget) -> QWidget:
        pass

    @staticmethod
    def is_valid_unlinks_layer(self, unlinks_layer):
        return lfh.fieldExists(unlinks_layer, 'line1') and \
               lfh.fieldExists(unlinks_layer, 'line2') and \
               not lfh.fieldHasNullValues(unlinks_layer, 'line1') and \
               not lfh.fieldHasNullValues(unlinks_layer, 'line2')

    class AnalysisEngineError(Exception):
        """ Generic Exception raised when the engine errors"""
        pass

    class AnalysisResults:
        """ Stores results from the analysis for passing around"""

        def __init__(self, attributes, types, values, coords):
            self.attributes = attributes
            self.types = types
            self.values = values
            self.coords = coords
