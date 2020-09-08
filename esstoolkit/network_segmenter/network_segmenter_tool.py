# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkSegmenter
                                 A QGIS plugin
 This plugin clean a road centre line map.
                              -------------------
        begin                : 2016-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Space SyntaxLtd
        email                : i.kolovou@spacesyntax.com
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
from __future__ import absolute_import
from __future__ import print_function

from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import zip
from builtins import range
import traceback

from qgis.PyQt.QtCore import (QThread, QObject, pyqtSignal)
from qgis.core import (QgsMapLayer, Qgis, QgsProject, QgsGeometry, QgsMessageLog)
import os
import itertools

from .network_segmenter_dialog import NetworkSegmenterDialog
from .segment_tools import segmentor
from . import utilityFunctions as uf
from esstoolkit.utilities import db_helpers as dbh, layer_field_helpers as lfh

# Import the debug library - required for the cleaning class in separate thread
# set is_debug to False in release version
is_debug = False
try:
    import pydevd

    has_pydevd = True
except ImportError as e:
    has_pydevd = False
    is_debug = False


class NetworkSegmenterTool(QObject):
    closingPlugin = pyqtSignal()
    setDbOutput = pyqtSignal()

    # initialise class with self and iface
    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface
        self.legend = QgsProject.instance().mapLayers()

        # load the dialog from the run method otherwise the objects gets created multiple times
        self.dlg = None

        # some globals
        self.segmenting = None
        self.thread = None

    def loadGUI(self):
        # create the dialog objects
        self.dlg = NetworkSegmenterDialog(dbh.getQGISDbs())

        # setup GUI signals
        self.dlg.closingPlugin.connect(self.unloadGUI)
        self.dlg.runButton.clicked.connect(self.startWorker)
        self.dlg.cancelButton.clicked.connect(self.killWorker)

        # add layers to dialog
        self.updateLayers()
        self.updateUnlinksLayers()

        if self.dlg.getNetwork():
            self.dlg.outputCleaned.setText(self.dlg.inputCombo.currentText() + "_seg")
            self.dlg.dbsettings_dlg.nameLineEdit.setText(self.dlg.inputCombo.currentText() + "_seg")
        self.dlg.inputCombo.currentIndexChanged.connect(self.updateOutputName)

        # setup legend interface signals
        QgsProject.instance().layersAdded.connect(self.updateLayers)
        QgsProject.instance().layersRemoved.connect(self.updateLayers)
        QgsProject.instance().layersAdded.connect(self.updateUnlinksLayers)
        QgsProject.instance().layersRemoved.connect(self.updateUnlinksLayers)

        self.settings = None

        print('settings', self.settings)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

    def unloadGUI(self):
        if self.dlg:
            self.dlg.closingPlugin.disconnect(self.unloadGUI)
            self.dlg.runButton.clicked.disconnect(self.startWorker)
            self.dlg.cancelButton.clicked.disconnect(self.killWorker)
            self.settings = None
        try:
            QgsProject.instance().layersAdded.disconnect(self.updateLayers)
        except TypeError:
            pass
        try:
            QgsProject.instance().layersRemoved.disconnect(self.updateLayers)
        except TypeError:
            pass
        try:
            QgsProject.instance().layersAdded.disconnect(self.updateUnlinksLayers)
        except TypeError:
            pass
        try:
            QgsProject.instance().layersRemoved.disconnect(self.updateUnlinksLayers)
        except TypeError:
            pass

        self.dlg = None

    def getActiveLayers(self):
        layers_list = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
                if layer.isSpatial() and (layer.geometryType() == 1):
                    layers_list.append(layer.name())
        return layers_list

    def updateLayers(self):
        layers = self.getActiveLayers()
        self.dlg.popActiveLayers(layers)

    def updateOutputName(self):
        if self.dlg.memoryRadioButton.isChecked():
            self.dlg.outputCleaned.setText(self.dlg.inputCombo.currentText() + "_seg")
        else:
            self.dlg.outputCleaned.clear()
        self.dlg.dbsettings_dlg.nameLineEdit.setText(self.dlg.inputCombo.currentText() + "_seg")

    def getpntplgLayers(self):
        layers_list = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
                if layer.isSpatial() and (layer.geometryType() in [0, 2]):
                    layers_list.append(layer.name())
        return layers_list

    def updateUnlinksLayers(self):
        layers = self.getpntplgLayers()
        self.dlg.popUnlinksLayers(layers)

    def giveMessage(self, message, level):
        # Gives warning according to message
        self.iface.messageBar().pushMessage("Network segmenter: ", "%s" % message, level, duration=5)

    def workerError(self, e, exception_string):
        # Gives error according to message
        QgsMessageLog.logMessage('Segmenting thread raised an exception: %s' % exception_string, level=Qgis.Critical)
        self.dlg.close()

    def startWorker(self):
        print('before started')
        self.dlg.segmentingProgress.reset()
        self.settings = self.dlg.get_settings()
        print('settings', self.settings)
        if self.settings['output_type'] == 'postgis':
            db_settings = self.dlg.get_dbsettings()
            self.settings.update(db_settings)

        if lfh.getLayerByName(self.settings['input']).crs().postgisSrid() == 4326:
            self.giveMessage('Re-project the layer. EPSG:4326 not allowed.', Qgis.Info)
        elif self.settings['output'] != '':
            segmenting = self.Worker(self.settings, self.iface)
            self.dlg.lockGUI(True)
            # start the segmenting in a new thread
            thread = QThread()
            segmenting.moveToThread(thread)
            segmenting.finished.connect(self.workerFinished)
            segmenting.error.connect(self.workerError)
            segmenting.warning.connect(self.giveMessage)
            segmenting.segm_progress.connect(self.dlg.segmentingProgress.setValue)

            thread.started.connect(segmenting.run)

            thread.start()

            self.thread = thread
            self.segmenting = segmenting

            # if is_debug:
            print('has started')
        else:
            self.giveMessage('Missing user input!', Qgis.Info)
            return

    def workerFinished(self, ret):
        # if is_debug:
        print('trying to finish')
        # get segmenting settings
        self.dlg.lockGUI(False)
        layer_name = self.settings['input']
        output_path, errors_path = self.settings['output']
        output_type = self.settings['output_type']
        #  get settings from layer
        layer = lfh.getLayerByName(layer_name)
        # create the segmenting results layers
        if self.segmenting:
            # clean up the worker and thread
            self.segmenting.finished.disconnect(self.workerFinished)
            self.segmenting.error.disconnect(self.workerError)
            self.segmenting.warning.disconnect(self.giveMessage)
            self.segmenting.segm_progress.disconnect(self.dlg.segmentingProgress.setValue)
            # self.segmenting.my_segmentor.progress.disconnect(self.segm_progress.emit)

        self.thread.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        if ret:

            break_lines, break_points = ret
            print(len(break_lines), 'ret')

            segmented = uf.to_layer(break_lines, layer.crs(), layer.dataProvider().encoding(),
                                    'Linestring', output_type, output_path)
            QgsProject.instance().addMapLayer(segmented)
            segmented.updateExtents()

            if self.settings['errors']:
                if len(break_points) == 0:
                    self.giveMessage('No points detected!', Qgis.Info)
                else:
                    errors = uf.to_layer(break_points, layer.crs(), layer.dataProvider().encoding(), 'Point',
                                         output_type,
                                         errors_path)
                    errors.loadNamedStyle(os.path.dirname(__file__) + '/errors_style.qml')
                    QgsProject.instance().addMapLayer(errors)
                    QgsProject.instance().mapLayers().refreshLayerLegend(errors)

            self.giveMessage('Process ended successfully!', Qgis.Info)

        else:
            # notify the user that sth went wrong
            self.giveMessage('Something went wrong! See the message log for more information', Qgis.Critical)

        if is_debug:
            print('thread running ', self.thread.isRunning())
        if is_debug:
            print('has finished ', self.thread.isFinished())

        self.thread = None
        self.segmenting = None

        if self.dlg:
            self.dlg.segmentingProgress.reset()
            self.dlg.close()

    def killWorker(self):
        # if is_debug:
        print('trying to cancel')
        # add emit signal to segmenttool or mergeTool only to stop the loop
        if self.segmenting:
            self.segmenting.finished.disconnect(self.workerFinished)
            self.segmenting.error.disconnect(self.workerError)
            self.segmenting.warning.disconnect(self.giveMessage)
            try:  # it might not have been connected already
                self.segmenting.segm_progress.disconnect(self.dlg.segmentingProgress.setValue)
            except TypeError:
                pass
            # Clean up thread and analysis
            self.segmenting.kill()
            self.segmenting.my_segmentor.kill()
            self.segmenting.deleteLater()
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
            self.segmenting = None
            self.dlg.segmentingProgress.reset()
            self.dlg.close()
        else:
            self.dlg.close()

    class Worker(QObject):

        # Setup signals
        finished = pyqtSignal(object)
        error = pyqtSignal(Exception, str)
        segm_progress = pyqtSignal(float)
        warning = pyqtSignal(str)
        segm_killed = pyqtSignal(bool)

        def __init__(self, settings, iface):
            QObject.__init__(self)
            self.settings = settings
            self.segm_killed = False
            self.iface = iface
            self.totalpr = 0
            self.my_segmentor = None
            # print ' class initiated'

        def run(self):
            if has_pydevd and is_debug:
                pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
            ret = None
            # if self.settings:
            try:
                # segmenting settings
                layer_name = self.settings['input']
                unlinks_layer_name = self.settings['unlinks']
                layer = lfh.getLayerByName(layer_name)
                unlinks = lfh.getLayerByName(unlinks_layer_name)
                stub_ratio = self.settings['stub_ratio']
                buffer = self.settings['buffer']
                errors = self.settings['errors']

                # print layer, unlinks, stub_ratio, buffer

                self.my_segmentor = segmentor(layer, unlinks, stub_ratio, buffer, errors)

                self.my_segmentor.progress.connect(self.segm_progress.emit)

                break_point_feats, invalid_unlink_point_feats, stubs_point_feats, segmented_feats = [], [], [], []

                # TODO: if postgis - run function
                self.my_segmentor.step = 10 / float(self.my_segmentor.layer.featureCount())
                self.my_segmentor.load_graph()
                # self.step specified in load_graph
                # progress emitted by break_segm & break_feats_iter
                cross_p_list = [self.my_segmentor.break_segm(feat) for feat in
                                self.my_segmentor.list_iter(list(self.my_segmentor.feats.values()))]
                self.my_segmentor.step = 20 / float(len(cross_p_list))
                segmented_feats = [self.my_segmentor.copy_feat(feat_geom_fid[0], feat_geom_fid[1], feat_geom_fid[2]) for
                                   feat_geom_fid in self.my_segmentor.break_feats_iter(cross_p_list)]

                if errors:
                    cross_p_list = set(list(itertools.chain.from_iterable(cross_p_list)))

                    ids1 = [i for i in range(0, len(cross_p_list))]
                    break_point_feats = [
                        self.my_segmentor.copy_feat(self.my_segmentor.break_f, QgsGeometry.fromPointXY(p_fid[0]),
                                                    p_fid[1]) for p_fid in (list(zip(cross_p_list, ids1)))]
                    ids2 = [i for i in range(max(ids1) + 1, max(ids1) + 1 + len(self.my_segmentor.invalid_unlinks))]
                    invalid_unlink_point_feats = [self.my_segmentor.copy_feat(self.my_segmentor.invalid_unlink_f,
                                                                              QgsGeometry.fromPointXY(p_fid1[0]),
                                                                              p_fid1[1]) for p_fid1 in
                                                  (list(zip(self.my_segmentor.invalid_unlinks, ids2)))]
                    ids = [i for i in
                           range(max(ids1 + ids2) + 1, max(ids1 + ids2) + 1 + len(self.my_segmentor.stubs_points))]
                    stubs_point_feats = [
                        self.my_segmentor.copy_feat(self.my_segmentor.stub_f, QgsGeometry.fromPointXY(p_fid2[0]),
                                                    p_fid2[1]) for p_fid2 in
                        (list(zip(self.my_segmentor.stubs_points, ids)))]

                ret = segmented_feats, break_point_feats + invalid_unlink_point_feats + stubs_point_feats

                self.my_segmentor.progress.disconnect()

            except Exception as e:
                print(e)
                self.error.emit(e, traceback.format_exc())

            # print "survived!"

            self.finished.emit(ret)

        def kill(self):
            print('killed')
            self.segm_killed = True
