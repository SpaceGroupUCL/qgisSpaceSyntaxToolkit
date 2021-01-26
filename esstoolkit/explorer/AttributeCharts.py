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

from math import atan

# Import the PyQt and QGIS libraries, essential libraries
from qgis.PyQt.QtCore import (QObject, pyqtSignal)

# try to import installed pyqtgraph, if not available use the one shipped with the esstoolkit
try:
    import pyqtgraph as pg

    has_pyqtgraph = True
except ImportError:
    try:
        from ..external import pyqtgraph as pg

        has_pyqtgraph = True
    except ImportError:
        has_pyqtgraph = False

import numpy as np


class AttributeCharts(QObject):
    histogramSelected = pyqtSignal(list)
    scatterplotSelected = pyqtSignal(list)

    def __init__(self, iface, plot):
        QObject.__init__(self)

        self.iface = iface
        self.plot = plot
        self.add_selection = False
        self.just_selected = False
        self.show_lines = True

        if has_pyqtgraph:
            self.plot.setClipToView(True)
            self.plot.enableAutoRange(enable=True)
            self.hist_selection = pg.PlotCurveItem()
            self.scatter_selection = []
            self.scatter = pg.ScatterPlotItem()
            self.scatter_points = {}
            self.region = pg.LinearRegionItem()
            # self.selected_points = []
            self.selected_points = pg.ScatterPlotItem()
            self.regress_line = pg.InfiniteLine()
            # self.roi = None

    # ----
    # Histogram functions
    def drawHistogram(self, values, xmin, xmax, bins):
        # compute the histogram
        if bins >= 50:
            bin = 51
        else:
            bin = bins + 1
        y, x = np.histogram(values, bins=np.linspace(xmin, xmax, num=bin))
        # plot the chart
        if has_pyqtgraph:
            curve = pg.PlotCurveItem()
            self.plot.clear()
            curve.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 230, 230), pen=pg.mkPen(None))
            self.plot.addItem(curve)
            # add the selection tool
            self.region = pg.LinearRegionItem([xmax, xmax], bounds=[xmin, xmax])
            self.region.sigRegionChangeFinished.connect(self.changedHistogramSelection)
            if self.show_lines:
                self.plot.addItem(self.region)
            # add the selection plot
            self.clearHistogramSelection()
            self.hist_selection = pg.PlotCurveItem()
            self.plot.addItem(self.hist_selection)

    # allow selection of items in chart and selecting them on the map
    def changedHistogramSelection(self):
        sel_min, sel_max = self.region.getRegion()
        # use to indicate the selection comes from the chart
        self.just_selected = True
        self.histogramSelected.emit([sel_min, sel_max])

    def setHistogramSelection(self, values, xmin, xmax, bins):
        if has_pyqtgraph:
            self.clearHistogramSelection()
            if len(values) > 0:
                # compute the histogram
                if bins >= 50:
                    bin = 51
                else:
                    bin = bins + 1
                y, x = np.histogram(values, bins=np.linspace(xmin, xmax, num=bin))
                # plot the selection chart
                self.hist_selection = pg.PlotCurveItem()
                self.hist_selection.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 0, 0), pen=pg.mkPen(None))
                self.plot.addItem(self.hist_selection)
                if self.just_selected:
                    # if the selection comes from the chart leave the selection region in place
                    self.just_selected = False
                else:
                    # if the selection comes from the map the values are not continuous: reset selection region
                    self.region.blockSignals(True)
                    self.region.setRegion((xmax, xmax))
                    self.region.blockSignals(False)
            else:
                # reset selection region
                self.region.blockSignals(True)
                self.region.setRegion((xmax, xmax))
                self.region.blockSignals(False)

    def clearHistogramSelection(self):
        if has_pyqtgraph:
            if self.hist_selection:
                self.plot.removeItem(self.hist_selection)

    def showhideSelectionLines(self, onoff):
        self.show_lines = onoff
        if onoff:
            self.plot.addItem(self.region)
        else:
            self.plot.removeItem(self.region)

    # ----
    # Scatterplot functions
    def drawScatterplot(self, xvalues, xmin, xmax, yvalues, ymin, ymax, slope, intercept, ids, symbols=None):
        # plot the chart
        if has_pyqtgraph:
            self.scatter = pg.ScatterPlotItem()
            self.plot.clear()
            # each point takes the colour of the map
            if symbols:
                points = []
                for i, id in enumerate(ids):
                    x = xvalues[i]
                    y = yvalues[i]
                    symb = symbols[i]
                    points.append({'pos': (x, y), 'data': id, 'size': 3, 'pen': pg.mkPen(None), 'brush': symb})
                self.scatter.addPoints(points)
            else:
                self.scatter.addPoints(x=xvalues, y=yvalues, data=ids, size=3, pen=pg.mkPen(None),
                                       brush=pg.mkBrush(235, 235, 235, 255))
            # selection by direct click
            self.scatter.sigClicked.connect(self.changedScatterplotSelection)
            self.plot.addItem(self.scatter)
            # add the regression line
            self.regress_line = pg.InfiniteLine()
            self.regress_line.setAngle(atan(slope / 1) * 180 / 3.1459)
            self.regress_line.setValue((0, intercept))
            self.regress_line.setPen(color='b', width=1)
            if self.show_lines:
                self.plot.addItem(self.regress_line)
            # newfeature: add the selection tool
            # self.roi = pg.PolyLineROI([[xmin, ymin],[xmax, ymin],[xmax, ymax],[xmin, ymax]], closed=True)
            # self.roi.sigRegionChangeFinished.connect(self.changedScatterPlotSelection)
            # self.plot.addItem(self.roi)
            # self.plot.disableAutoRange('xy')

    # allow selection of items in chart and selecting them on the map
    def addToScatterplotSelection(self, onoff):
        # switch shift key modifier
        self.add_selection = onoff

    def changedScatterplotSelection(self, plot, points):
        if has_pyqtgraph:
            # set points for scatter
            ids = [point.data() for point in points]
            # get clicked points
            if not self.add_selection:
                self.clearScatterplotSelection()
                self.scatter_selection = ids
            else:
                self.scatter_selection.extend(ids)
            # indicate that selection was made on the chart
            self.just_selected = True
            # send ids for map
            self.scatterplotSelected.emit(self.scatter_selection)

    def setScatterplotSelection(self, xvalues, yvalues, ids):
        if has_pyqtgraph:
            # if not self.just_selected:
            self.clearScatterplotSelection()
            if len(ids) > 0:
                self.scatter_selection = [fid for fid in ids]
                self.selected_points = pg.ScatterPlotItem()
                self.selected_points.addPoints(x=xvalues, y=yvalues, data=ids, size=3, pen=pg.mkPen('r', width=1),
                                               brush=pg.mkBrush(235, 0, 0, 255))
                self.plot.addItem(self.selected_points)
            self.just_selected = False

    def clearScatterplotSelection(self):
        if has_pyqtgraph:
            if self.selected_points:
                self.plot.removeItem(self.selected_points)
                self.selected_points = pg.ScatterPlotItem()
                self.scatter_selection = []

    def showhideRegressionLine(self, onoff):
        self.show_lines = onoff
        if onoff:
            self.plot.addItem(self.regress_line)
        else:
            self.plot.removeItem(self.regress_line)
