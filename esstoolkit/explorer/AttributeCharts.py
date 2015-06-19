# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essToolkit
                            Space Syntax Toolkit
 Set of tools for essential space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2015, UCL
        author               : Jorge Gil
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
# Import the PyQt and QGIS libraries, essential libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from math import atan
import time

# try to import installed pyqtgraph, if not available use the one shipped with the esstoolkit
try:
    import pyqtgraph as pg
    has_pyqtgraph = True
except ImportError, e:
    try:
        from ..external import pyqtgraph as pg
        has_pyqtgraph = True
    except ImportError, e:
        has_pyqtgraph = False

import numpy as np
from operator import itemgetter

from .. import utility_functions as uf


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
            self.selected_points = []
            self.regress_line = pg.InfiniteLine()
            #self.roi = None

    #----
    # Histogram functions
    def drawHistogram(self, values, xmin, xmax, bins):
        # compute the histogram
        if bins >= 50:
            bin = 51
        else:
            bin = bins+1
        y, x = np.histogram(values, bins=np.linspace(xmin, xmax, num=bin))
        # plot the chart
        if has_pyqtgraph:
            curve = pg.PlotCurveItem()
            self.plot.clear()
            curve.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 230, 230), pen=pg.mkPen(None))
            self.plot.addItem(curve)
            #self.plot.setLimits(xMin=xmin, xMax=xmax, yMin=0, yMax=max(y))
            # add the selection tool
            self.region = pg.LinearRegionItem([xmax,xmax],bounds=[xmin, xmax])
            self.region.sigRegionChangeFinished.connect(self.changedHistogramSelection)
            if self.show_lines:
                self.plot.addItem(self.region)
            # add the selection plot
            self.hist_selection = pg.PlotCurveItem()
            self.plot.addItem(self.hist_selection)
            self.clearHistogramSelection()
            #self.plot.autoRange()

    # allow selection of items in chart and selecting them on the map
    def changedHistogramSelection(self):
        sel_min, sel_max = self.region.getRegion()
        #self.clearHistogramSelection()
        self.histogramSelected.emit([sel_min, sel_max])

    def setHistogramSelection(self, values, xmin, xmax, bins):
        if has_pyqtgraph:
            self.clearHistogramSelection()
            if len(values) > 0:
                # compute the histogram
                if bins >= 50:
                    bin = 51
                else:
                    bin = bins+1
                y, x = np.histogram(values, bins=np.linspace(xmin, xmax, num=bin))
                # plot the selection chart
                self.hist_selection = pg.PlotCurveItem()
                self.hist_selection.setData(x, y, stepMode=True, fillLevel=0, brush=(230, 0, 0), pen=pg.mkPen(None))
                self.plot.addItem(self.hist_selection)
            else:
                self.region.blockSignals(True)
                self.region.setRegion((xmax,xmax))
                self.region.blockSignals(False)

    def clearHistogramSelection(self):
        if has_pyqtgraph:
            if self.hist_selection:
                self.plot.removeItem(self.hist_selection)
                self.hist_selection = pg.PlotCurveItem()

    def showhideSelectionLines(self, onoff):
        self.show_lines = onoff
        if onoff:
            self.plot.addItem(self.region)
        else:
            self.plot.removeItem(self.region)

    #----
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
                    points.append({'pos': (x,y), 'data': id, 'size': 3, 'pen': pg.mkPen(None), 'brush': symb})
                self.scatter.addPoints(points)
            else:
                self.scatter.addPoints(x=xvalues, y=yvalues, data=ids, size=3, pen=pg.mkPen(None), brush=pg.mkBrush(235, 235, 235, 255))
            # selection by direct click
            self.scatter.sigClicked.connect(self.changedScatterplotSelection)
            self.plot.addItem(self.scatter)
            #self.plot.setLimits(xMin=xmin, xMax=xmax, yMin=ymin, yMax=ymax)
            # add the regression line
            self.regress_line = pg.InfiniteLine()
            self.regress_line.setAngle(atan(slope/1) * 180 / 3.1459)
            self.regress_line.setValue((0,intercept))
            self.regress_line.setPen(color='b', width=1)
            if self.show_lines:
                self.plot.addItem(self.regress_line)
            # newfeature: add the selection tool
            #self.roi = pg.PolyLineROI([[xmin, ymin],[xmax, ymin],[xmax, ymax],[xmin, ymax]], closed=True)
            #self.roi.sigRegionChangeFinished.connect(self.changedScatterPlotSelection)
            #self.plot.addItem(self.roi)
            #self.plot.disableAutoRange('xy')
            #self.plot.autoRange()


    # allow selection of items in chart and selecting them on the map
    def addToScatterplotSelection(self, onoff):
        # switch shift key modifier
        self.add_selection = onoff

    def changedScatterplotSelection(self, plot, points):
        if has_pyqtgraph:
            # get clicked points
            if not self.add_selection:
                self.clearScatterplotSelection()
            # set points for scatter
            for point in points:
                self.selected_points.append(point)
                point.setPen('r',width=3)
                self.scatter_selection.append(point.data())
            # send ids for map
            self.just_selected = True  #is used to block a second update
            self.scatterplotSelected.emit(self.scatter_selection)

    def setScatterplotIdSelection(self, ids):
        if has_pyqtgraph:
            if not self.just_selected:
                self.clearScatterplotSelection()
                if len(ids) > 0:
                    for id in ids:
                        point = self.scatter.points()[id]
                        point.setPen('r',width=3)
                        self.selected_points.append(point)
                        self.scatter_selection.append(id)
            self.just_selected = False

    def clearScatterplotSelection(self):
        if has_pyqtgraph:
            for point in self.selected_points:
                point.resetPen()
            self.selected_points = []
            self.scatter_selection = []

    def showhideRegressionLine(self, onoff):
        self.show_lines = onoff
        if onoff:
            self.plot.addItem(self.regress_line)
        else:
            self.plot.removeItem(self.regress_line)