# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# Import the PyQt and QGIS libraries
from builtins import range

import numpy as np
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsSymbol, QgsFillSymbol, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsRenderContext,
                       QgsGradientColorRamp, QgsGradientStop)

from esstoolkit.utilities import gui_helpers as guih


class AttributeSymbology(QObject):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

    def updateRenderer(self, layer, attribute_vals, settings):
        """
        Creates a renderer for the layer based on this, and applies it
        The renderer uses GradientColourRamp to calculate the symbol colours

        @param layer: the selected QgsVectorLayer object
        """
        geometry = layer.geometryType()
        # create a colour ramp based on colour range type, inverting symbols if required
        ramp_type = int(settings['colour_range'])
        invert = int(settings['invert_colour'])
        ramp = self.getColourRamp(ramp_type, invert)
        line_width = float(settings['line_width'])
        # calculate ranges: EqualInterval = 0; Quantile  = 1; Jenks = 2; StdDev = 3; Pretty = 4; Custom = 5
        intervals = int(settings['intervals'])
        mode = int(settings['interval_type'])
        attribute = attribute_vals['name']
        renderer = None
        if mode < 3:
            # set symbol type and line width
            symbol = QgsSymbol.defaultSymbol(geometry)
            if symbol:
                if symbol.type() == 1:  # line
                    symbol.setWidth(line_width)
                elif symbol.type() == 2:  # line
                    symbol = QgsFillSymbol.createSimple(
                        {'style': 'solid', 'color': 'black', 'width_border': '%s' % line_width})
                elif symbol.type() == 0:  # point
                    symbol.setSize(line_width)
                renderer = QgsGraduatedSymbolRenderer.createRenderer(layer, attribute, intervals, mode, symbol, ramp)
                renderer.setMode(mode)
                renderer.setSourceColorRamp(ramp)
        else:
            # calculate range values individually based on custom settings
            ranges = []
            max_value = float(attribute_vals['max'])
            min_value = float(attribute_vals['min'])
            top_value = float(settings['top_value'])
            bottom_value = float(settings['bottom_value'])
            # calculate number of ranges depending on top/bottom difference from max/min:
            # is there really a range there? Otherwise this will calculate 1 or even 2 ranges less
            calc_intervals = intervals + 1
            if top_value != max_value:
                calc_intervals -= 1
            if bottom_value != min_value:
                calc_intervals -= 1
            range_steps = [r for r in np.linspace(bottom_value, top_value, calc_intervals)]
            if top_value != max_value:
                range_steps.append(max_value)
            if bottom_value != min_value:
                range_steps.insert(0, min_value)
            for i in range(0, len(range_steps) - 1):
                symbol = QgsSymbol.defaultSymbol(geometry)
                if symbol:
                    new_colour = ramp.color(i / (float(len(range_steps)) - 2)).getRgb()
                    symbol.setColor(QColor(*new_colour))
                    symbol.setWidth(line_width)
                    label = "%s - %s" % (range_steps[i], range_steps[i + 1])
                    this_range = QgsRendererRange(range_steps[i], range_steps[i + 1], symbol, label)
                    ranges.append(this_range)
            if ranges:
                renderer = QgsGraduatedSymbolRenderer(attribute, ranges)
                # renderer.setMode(5)
                renderer.setSourceColorRamp(ramp)
        # configure symbol levels to display in specific order
        # the classic "reds on top" from space syntax, or the reverse
        if renderer:
            display_order = int(settings['display_order'])
            renderer.setUsingSymbolLevels(True)
            render_pass = 0
            if display_order == 0:
                for symbol in renderer.symbols(QgsRenderContext()):
                    for i in range(0, symbol.symbolLayerCount()):
                        symbol.symbolLayer(i).setRenderingPass(render_pass)
                        render_pass += 1
            else:
                for symbol in reversed(renderer.symbols(QgsRenderContext())):
                    for i in range(0, symbol.symbolLayerCount()):
                        symbol.symbolLayer(i).setRenderingPass(render_pass)
                        render_pass += 1
        # set the symbols for monochrome ramp
        # varying line width, point size or polygon pattern density
        # doesn't use data column because it's not scaled according to line width values
        # the width is calculated linearly between min and given value
        if renderer:
            if ramp_type == 3:
                new_width = np.linspace(0.1, line_width, intervals)
                step = intervals / 8.0  # this is usd for fill patterns
                # color = QColor(ramp.color(0).getRgb())  # same as above
                for i in range(0, intervals):
                    symbol = renderer.symbols(QgsRenderContext())[i]
                    if invert:
                        if symbol.type() == 1:  # line
                            symbol.setWidth(new_width[(intervals - 1) - i])
                        elif symbol.type() == 0:  # point
                            symbol.setSize(new_width[(intervals - 1) - i])
                        elif symbol.type() == 2:  # polygon
                            dense = int(i / step)
                            if dense == 0:
                                style = 'solid'
                            else:
                                style = 'dense%s' % dense
                            symbol = QgsFillSymbol.createSimple({'style': style, 'color': 'black',
                                                                 'width_border': '%s' % new_width[(intervals - 1) - i]})
                    else:
                        if symbol.type() == 1:  # line
                            symbol.setWidth(new_width[i])
                        elif symbol.type() == 0:  # point
                            symbol.setSize(new_width[i])
                        elif symbol.type() == 2:  # polygon
                            dense = int(i / step)
                            if dense == 7:
                                style = 'solid'
                            else:
                                style = 'dense%s' % (7 - dense)
                            symbol = QgsFillSymbol.createSimple(
                                {'style': style, 'color': 'black', 'width_border': '%s' % new_width[i]})
                    renderer.updateRangeSymbol(i, symbol)
        return renderer

    def getColourRamp(self, colour_type, invert):
        ramp = None
        # grey and monochrome depend on canvas colour: if canvas is black or dark, symbols are white, and vice versa
        canvas = guih.getCanvasColour(self.iface)
        if colour_type == 0:  # classic space syntax
            if invert:
                ramp = QgsGradientColorRamp(QColor(255, 0, 0, 255), QColor(0, 0, 255, 255), False)
                ramp.setStops(
                    [QgsGradientStop(0.25, QColor(255, 255, 0, 255)), QgsGradientStop(0.5, QColor(0, 255, 0, 255)),
                     QgsGradientStop(0.75, QColor(0, 255, 255, 255))])
            else:
                ramp = QgsGradientColorRamp(QColor(0, 0, 255, 255), QColor(255, 0, 0, 255), False)
                ramp.setStops(
                    [QgsGradientStop(0.25, QColor(0, 255, 255, 255)), QgsGradientStop(0.5, QColor(0, 255, 0, 255)),
                     QgsGradientStop(0.75, QColor(255, 255, 0, 255))])
        if colour_type == 1:  # red - blue
            if invert:
                ramp = QgsGradientColorRamp(QColor(255, 0, 0, 255), QColor(0, 0, 255, 255), False,
                                            [QgsGradientStop(0.5, QColor(255, 255, 255, 255))])
            else:
                ramp = QgsGradientColorRamp(QColor(0, 0, 255, 255), QColor(255, 0, 0, 255), False,
                                            [QgsGradientStop(0.5, QColor(255, 255, 255, 255))])
        if colour_type == 2:  # grey scale
            if (invert and canvas.value() >= 80) or (not invert and canvas.value() < 80):
                ramp = QgsGradientColorRamp(QColor(0, 0, 0, 255), QColor(248, 248, 248, 255), False)
            else:
                ramp = QgsGradientColorRamp(QColor(248, 248, 248, 255), QColor(0, 0, 0, 255), False)
        if colour_type == 3:  # monochrome
            if canvas.value() < 80:
                ramp = QgsGradientColorRamp(QColor(255, 255, 255, 255), QColor(255, 255, 255, 255), False)
            else:
                ramp = QgsGradientColorRamp(QColor(0, 0, 0, 255), QColor(0, 0, 0, 255), False)
        if colour_type == 4:  # space syntax ltd
            if invert:
                ramp = QgsGradientColorRamp(QColor(255, 0, 0, 255), QColor(0, 0, 255, 255), False)
                ramp.setStops(
                    [QgsGradientStop(0.15, QColor(255, 170, 0, 255)), QgsGradientStop(0.25, QColor(255, 255, 0, 255)),
                     QgsGradientStop(0.5, QColor(0, 255, 0, 255)), QgsGradientStop(0.75, QColor(85, 255, 255, 255))])
            else:
                ramp = QgsGradientColorRamp(QColor(0, 0, 255, 255), QColor(255, 0, 0, 255), False)
                ramp.setStops(
                    [QgsGradientStop(0.25, QColor(85, 255, 255, 255)), QgsGradientStop(0.5, QColor(0, 255, 0, 255)),
                     QgsGradientStop(0.75, QColor(255, 255, 0, 255)), QgsGradientStop(0.85, QColor(255, 170, 0, 255))])
        return ramp
