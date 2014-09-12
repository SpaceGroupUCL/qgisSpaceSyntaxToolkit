# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essTools
                                 A QGIS plugin
 Set of tools for space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2014 by Jorge Gil, UCL
        email                : jorge.gil@ucl.ac.uk
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from ..utility_functions import *

import numpy as np

class AttributeSymbology(QObject):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

    def updateRenderer(self, layer, attribute_vals, settings):
        """
        Creates a renderer for the layer based on this, and applies it
        The renderer uses GradientColourRamp to calculate the symbol colours

        @param idx: the id of the selected attribute in the dialog's attributes list
        """
        geometry = layer.geometryType()
        # create a colour ramp based on colour range type, inverting symbols if required
        ramp_type = int(settings["colour_range"])
        invert = int(settings["invert_colour"])
        ramp = self.getColourRamp(ramp_type, invert)
        line_width = float(settings["line_width"])
        # calculate ranges: EqualInterval = 0; Quantile  = 1; Jenks = 2; StdDev = 3; Pretty = 4; Custom = 5
        intervals = int(settings["intervals"])
        mode = int(settings["interval_type"])
        attribute = attribute_vals["name"]
        renderer = None
        if mode < 3:
            # set symbol type and line width
            symbol = QgsSymbolV2.defaultSymbol(geometry)
            if symbol:
                if symbol.type() == 1:
                    symbol.setWidth(line_width)
                renderer = QgsGraduatedSymbolRendererV2.createRenderer(layer, attribute, intervals, mode, symbol, ramp)
                renderer.setMode(mode)
                renderer.setSourceColorRamp(ramp)
        else:
            # calculate range values individually based on custom settings
            ranges = []
            top_value = float(settings["top_value"])
            bottom_value = float(settings["bottom_value"])
            max_value = attribute_vals["max"]
            min_value = attribute_vals["min"]
            range_steps = np.linspace(bottom_value,top_value,(intervals-1))
            for i in range(0,intervals):
                symbol = QgsSymbolV2.defaultSymbol(geometry)
                if symbol:
                    new_colour = ramp.color(i/(float(intervals)-1)).getRgb()
                    symbol.setColor(QColor(*new_colour))
                    symbol.setWidth(line_width)
                    if i == 0:
                        label = "%s - %s"%(min_value, range_steps[i])
                        this_range = QgsRendererRangeV2(min_value, range_steps[i], symbol, label)
                    elif i == (intervals-1):
                        label = "%s - %s"%(range_steps[i-1], max_value)
                        this_range = QgsRendererRangeV2(range_steps[i-1], max_value, symbol, label)
                    else:
                        label = "%s - %s"%(range_steps[i-1], range_steps[i])
                        this_range = QgsRendererRangeV2(range_steps[i-1], range_steps[i], symbol, label)
                    ranges.append(this_range)
            if ranges:
                renderer = QgsGraduatedSymbolRendererV2(attribute, ranges)
                #renderer.setMode(5)
                renderer.setSourceColorRamp(ramp)
        # configure symbol levels to display in specific order
        # the classic "reds on top" from space syntax, or the reverse
        if renderer:
            display_order = int(settings["display_order"])
            renderer.setUsingSymbolLevels(True)
            render_pass = 0
            if display_order == 0:
                for symbol in renderer.symbols():
                    for i in range(0,symbol.symbolLayerCount()):
                        symbol.symbolLayer(i).setRenderingPass(render_pass)
                        render_pass += 1
            else:
                for symbol in reversed(renderer.symbols()):
                    for i in range(0,symbol.symbolLayerCount()):
                        symbol.symbolLayer(i).setRenderingPass(render_pass)
                        render_pass += 1
        # set the symbols with varying line width in the case of monochrome ramp
        # doesn't use data column because it's not scaled according to line width values
        # the width is calculated linearly between min and given value
        if renderer:
            if ramp_type == 3:
                new_width = np.linspace(0.1,line_width,intervals)
                for i in range(0,intervals):
                    symbol = renderer.symbols()[i]
                    if invert:
                        symbol.setWidth(new_width[(intervals-1)-i])
                    else:
                        symbol.setWidth(new_width[i])
                    renderer.updateRangeSymbol(i,symbol)
        return renderer


    def getColourRamp(self, type, invert):
        ramp = None
        if type == 0: # classic space syntax
            if invert:
                ramp = QgsVectorGradientColorRampV2(QColor(255,0,0,255),QColor(0,0,255,255),False)
                ramp.setStops([QgsGradientStop(0.25,QColor(255,255,0,255)),QgsGradientStop(0.5,QColor(0,255,0,255)),QgsGradientStop(0.75,QColor(0,255,255,255))])
            else:
                ramp = QgsVectorGradientColorRampV2(QColor(0,0,255,255),QColor(255,0,0,255),False)
                ramp.setStops([QgsGradientStop(0.25,QColor(0,255,255,255)),QgsGradientStop(0.5,QColor(0,255,0,255)),QgsGradientStop(0.75,QColor(255,255,0,255))])
        if type == 1: # red - blue
            if invert:
                ramp = QgsVectorGradientColorRampV2(QColor(255,0,0,255),QColor(0,0,255,255),False,[QgsGradientStop(0.5,QColor(255,255,255,255))])
            else:
                ramp = QgsVectorGradientColorRampV2(QColor(0,0,255,255),QColor(255,0,0,255),False,[QgsGradientStop(0.5,QColor(255,255,255,255))])
        if type == 2: # grey scale
            if invert:
                ramp = QgsVectorGradientColorRampV2(QColor(0,0,0,255),QColor(248,248,248,255),False)
            else:
                ramp = QgsVectorGradientColorRampV2(QColor(248,248,248,255),QColor(0,0,0,255),False)
        if type == 3: # monochrome
            #depends on canvas background: if canvas is black, lines are white, and vice versa
            canvas = getCanvasColour(self.iface)
            # newfeature: add threshold to tool settings
            if canvas.value() < 80:
                ramp = QgsVectorGradientColorRampV2(QColor(255,255,255,255),QColor(255,255,255,255),False)
            else:
                ramp = QgsVectorGradientColorRampV2(QColor(0,0,0,255),QColor(0,0,0,255),False)
        return ramp