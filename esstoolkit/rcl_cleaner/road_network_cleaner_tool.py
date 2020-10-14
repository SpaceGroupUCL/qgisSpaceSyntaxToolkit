# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-11-10
# copyright            : (C) 2016 by Space Syntax Ltd
# author               : Ioanna Kolovou
# email                : i.kolovou@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import absolute_import
from __future__ import print_function

from future import standard_library

standard_library.install_aliases()
from builtins import str
import traceback
from qgis.PyQt.QtCore import (QObject, QThread, pyqtSignal)
from qgis.core import (QgsProject, QgsMessageLog, Qgis)
import os

from .road_network_cleaner_dialog import RoadNetworkCleanerDialog
from .sGraph.sGraph import sGraph  # better give these a name to make it explicit to which module the methods belong
from .sGraph import utilityFunctions as utf
from esstoolkit.utilities import db_helpers as dbh, layer_field_helpers as lfh

# Import the debug library - required for the cleaning class in separate thread
# set is_debug to False in release version
is_debug = False
try:
    import pydevd_pycharm

    has_pydevd = True
except ImportError:
    has_pydevd = False
    is_debug = False


# sys.path.append("pydevd-pycharm.egg")

class NetworkCleanerTool(QObject):

    # initialise class with self and iface
    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface
        self.legend = QgsProject.instance().mapLayers()

        # load the dialog from the run method otherwise the objects gets created multiple times
        self.dlg = None

        # some globals
        self.cleaning = None
        self.thread = None
        self.thread_error = ''
        self.settings = None

    def loadGUI(self):
        # create the dialog objects
        self.dlg = RoadNetworkCleanerDialog(dbh.getQGISDbs(portlast=True))

        # setup GUI signals
        self.dlg.closingPlugin.connect(self.unloadGUI)
        self.dlg.cleanButton.clicked.connect(self.startWorker)
        self.dlg.cancelButton.clicked.connect(self.killWorker)

        # add layers to dialog
        self.updateLayers()

        if self.dlg.getNetwork():
            self.dlg.outputCleaned.setText(self.dlg.inputCombo.currentText() + "_cl")
            self.dlg.dbsettings_dlg.nameLineEdit.setText(self.dlg.inputCombo.currentText() + "_cl")
        self.dlg.inputCombo.currentIndexChanged.connect(self.updateOutputName)

        # setup legend interface signals
        QgsProject.instance().layersAdded.connect(self.updateLayers)
        QgsProject.instance().layersRemoved.connect(self.updateLayers)

        self.settings = None

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

    def unloadGUI(self):
        if self.dlg:
            self.dlg.closingPlugin.disconnect(self.unloadGUI)
            self.dlg.cleanButton.clicked.disconnect(self.startWorker)
            self.dlg.cancelButton.clicked.disconnect(self.killWorker)
            self.settings = None
            QgsProject.instance().layersAdded.disconnect(self.updateLayers)
            QgsProject.instance().layersRemoved.disconnect(self.updateLayers)

        self.dlg = None

    def updateLayers(self):
        layers = lfh.getLineLayers()
        if self.dlg:
            self.dlg.popActiveLayers(layers)

    # SOURCE: Network Segmenter https://github.com/OpenDigitalWorks/NetworkSegmenter
    # SOURCE: https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/

    def updateOutputName(self):
        if self.dlg.memoryRadioButton.isChecked():
            self.dlg.outputCleaned.setText(self.dlg.inputCombo.currentText() + "_cl")
        else:
            self.dlg.outputCleaned.clear()
        self.dlg.dbsettings_dlg.nameLineEdit.setText(self.dlg.inputCombo.currentText() + "_cl")

    def giveMessage(self, message, level):
        # Gives warning according to message
        self.iface.messageBar().pushMessage("Road network cleaner: ", "%s" % message, level, duration=5)

    def workerError(self, exception, exception_string):
        # Gives error according to message
        self.thread_error = exception_string
        # the thread will however continue "finishing"

    def startWorker(self):
        self.dlg.cleaningProgress.reset()
        self.settings = self.dlg.get_settings()
        if self.settings['output_type'] == 'postgis':
            db_settings = self.dlg.get_dbsettings()
            self.settings.update(db_settings)

        if lfh.getLayerByName(self.settings['input']).crs().postgisSrid() == 4326:
            self.giveMessage('Re-project the layer. EPSG:4326 not allowed.', Qgis.Info)
            return
        elif self.settings['output'] != '':

            cleaning = self.Worker(self.settings, self.iface)
            # start the cleaning in a new thread
            self.dlg.lockGUI(True)
            self.dlg.lockSettingsGUI(True)
            thread = QThread()
            self.thread_error = ''
            cleaning.moveToThread(thread)
            cleaning.finished.connect(self.workerFinished)
            cleaning.error.connect(self.workerError)
            cleaning.warning.connect(self.giveMessage)
            cleaning.cl_progress.connect(self.dlg.cleaningProgress.setValue)

            thread.started.connect(cleaning.run)

            thread.start()

            self.thread = thread
            self.cleaning = cleaning

            if is_debug:
                print('started')
        else:
            self.giveMessage('Missing user input!', Qgis.Info)
            return

    def workerFinished(self, ret):

        if self.cleaning:
            # clean up the worker and thread
            self.cleaning.finished.disconnect(self.workerFinished)
            self.cleaning.error.disconnect(self.workerError)
            self.cleaning.warning.disconnect(self.giveMessage)
            self.cleaning.cl_progress.disconnect(self.dlg.cleaningProgress.setValue)

        # clean up the worker and thread
        self.thread.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        if ret:
            self.dlg.lockGUI(False)
            # TODO: only if edit default has been pressed before
            self.dlg.lockSettingsGUI(False)
            # get cleaning settings
            layer_name = self.settings['input']
            path, unlinks_path, errors_path = self.settings['output']  # if postgis: connstring, schema, table_name

            output_type = self.settings['output_type']
            #  get settings from layer
            layer = lfh.getLayerByName(layer_name)

            cleaned_features, errors_features, unlinks_features = ret

            if self.settings['errors']:
                if len(errors_features) > 0:
                    errors = utf.to_layer(errors_features, layer.crs(), layer.dataProvider().encoding(), 'Point',
                                          output_type, errors_path)
                    errors.loadNamedStyle(os.path.dirname(__file__) + '/qgis_styles/errors.qml')
                    QgsProject.instance().addMapLayer(errors)
                    node = QgsProject.instance().layerTreeRoot().findLayer(errors.id())
                    self.iface.layerTreeView().layerTreeModel().refreshLayerLegend(node)
                    QgsMessageLog.logMessage('layer name %s' % layer_name, level=Qgis.Critical)
                else:
                    self.giveMessage('No errors detected!', Qgis.Info)

            if self.settings['unlinks']:
                if len(unlinks_features) > 0:
                    unlinks = utf.to_layer(unlinks_features, layer.crs(), layer.dataProvider().encoding(), 'Point',
                                           output_type, unlinks_path)
                    unlinks.loadNamedStyle(os.path.dirname(__file__) + '/qgis_styles/unlinks.qml')
                    QgsProject.instance().addMapLayer(unlinks)
                    node = QgsProject.instance().layerTreeRoot().findLayer(unlinks.id())
                    self.iface.layerTreeView().layerTreeModel().refreshLayerLegend(node)
                else:
                    self.giveMessage('No unlinks detected!', Qgis.Info)

            cleaned = utf.to_layer(cleaned_features, layer.crs(), layer.dataProvider().encoding(), 'Linestring',
                                   output_type, path)
            cleaned.loadNamedStyle(os.path.dirname(__file__) + '/qgis_styles/cleaned.qml')
            QgsProject.instance().addMapLayer(cleaned)
            node = QgsProject.instance().layerTreeRoot().findLayer(cleaned.id())
            self.iface.layerTreeView().layerTreeModel().refreshLayerLegend(node)
            cleaned.updateExtents()

            self.giveMessage('Process ended successfully!', Qgis.Info)
            self.dlg.cleaningProgress.setValue(100)

        elif self.thread_error != '':
            # notify the user that sth went wrong
            self.giveMessage('Something went wrong! See the message log for more information', Qgis.Critical)
            QgsMessageLog.logMessage("Cleaning thread error: %s" % self.thread_error)

        self.thread = None
        self.cleaning = None

        if self.dlg:
            self.dlg.cleaningProgress.reset()
            self.dlg.close()

    def killWorker(self):
        if is_debug:
            print('trying to cancel')
        # add emit signal to breakTool or mergeTool only to stop the loop
        if self.cleaning:
            # Disconnect signals
            self.cleaning.finished.disconnect(self.workerFinished)
            self.cleaning.error.disconnect(self.workerError)
            self.cleaning.warning.disconnect(self.giveMessage)
            self.cleaning.cl_progress.disconnect(self.dlg.cleaningProgress.setValue)
            try:  # it might not have been connected already
                self.cleaning.graph.progress.disconnect(self.dlg.cleaningProgress.setValue)
            except TypeError:
                pass
            # Clean up thread and analysis
            self.cleaning.kill()
            self.cleaning.graph.kill()  # todo
            self.cleaning.deleteLater()
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
            self.cleaning = None
            self.dlg.cleaningProgress.reset()
            self.dlg.close()
        else:
            self.dlg.close()

    # SOURCE: https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/
    class Worker(QObject):

        # Setup signals
        finished = pyqtSignal(object)
        error = pyqtSignal(Exception, str)
        cl_progress = pyqtSignal(float)
        warning = pyqtSignal(str)
        cl_killed = pyqtSignal(bool)

        def __init__(self, settings, iface):
            QObject.__init__(self)
            self.settings = settings
            self.cl_killed = False
            self.iface = iface
            self.pseudo_graph = sGraph({}, {})
            self.graph = None

        def run(self):
            if has_pydevd and is_debug:
                pydevd_pycharm.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True,
                                        suspend=False)
            ret = None
            # if self.settings:
            try:
                # cleaning settings
                layer_name = self.settings['input']
                layer = lfh.getLayerByName(layer_name)
                snap_threshold = self.settings['snap']
                break_at_vertices = self.settings['break']
                merge_type = self.settings['merge']
                collinear_threshold = self.settings['collinear_angle']
                angle_threshold = self.settings['simplification_threshold']
                fix_unlinks = self.settings['fix_unlinks']
                orphans = self.settings['orphans']
                getUnlinks = self.settings['unlinks']
                [load_range, cl1_range, cl2_range, cl3_range, break_range, merge_range, snap_range, unlinks_range,
                 fix_range] = self.settings['progress_ranges']
                QgsMessageLog.logMessage('settings %s' % self.settings, level=Qgis.Critical)

                self.cl_progress.emit(0)

                if break_at_vertices:

                    self.pseudo_graph.step = load_range / float(layer.featureCount())
                    self.pseudo_graph.progress.connect(self.cl_progress.emit)
                    self.graph = sGraph({}, {})
                    self.graph.total_progress = load_range
                    self.pseudo_graph.load_edges_w_o_topology(utf.clean_features_iter(layer.getFeatures()))
                    QgsMessageLog.logMessage('pseudo_graph edges added %s' % load_range, level=Qgis.Critical)
                    self.pseudo_graph.step = break_range / float(len(self.pseudo_graph.sEdges))
                    self.graph.load_edges(
                        self.pseudo_graph.break_features_iter(getUnlinks, angle_threshold, fix_unlinks),
                        angle_threshold)
                    QgsMessageLog.logMessage('pseudo_graph edges broken %s' % break_range, level=Qgis.Critical)
                    self.pseudo_graph.progress.disconnect()
                    self.graph.progress.connect(self.cl_progress.emit)
                    self.graph.total_progress = self.pseudo_graph.total_progress

                else:
                    self.graph = sGraph({}, {})
                    self.graph.progress.connect(self.cl_progress.emit)
                    self.graph.step = load_range / float(layer.featureCount())
                    self.graph.load_edges(utf.clean_features_iter(layer.getFeatures()), angle_threshold)
                    QgsMessageLog.logMessage('graph edges added %s' % load_range, level=Qgis.Critical)

                self.graph.step = cl1_range / (float(len(self.graph.sEdges)) * 2.0)
                if orphans:
                    self.graph.clean(True, False, snap_threshold, True)
                else:
                    self.graph.clean(True, False, snap_threshold, False)
                QgsMessageLog.logMessage('graph clean parallel and closed pl %s' % cl1_range, level=Qgis.Critical)

                if fix_unlinks:
                    self.graph.step = fix_range / float(len(self.graph.sEdges))
                    self.graph.fix_unlinks()
                    QgsMessageLog.logMessage('unlinks added  %s' % fix_range, level=Qgis.Critical)

                # TODO clean iteratively until no error

                if snap_threshold != 0:

                    self.graph.step = snap_range / float(len(self.graph.sNodes))
                    self.graph.snap_endpoints(snap_threshold)
                    QgsMessageLog.logMessage('snap  %s' % snap_range, level=Qgis.Critical)
                    self.graph.step = cl2_range / (float(len(self.graph.sEdges)) * 2.0)

                    if orphans:
                        self.graph.clean(True, False, snap_threshold, True)
                    else:
                        self.graph.clean(True, False, snap_threshold, False)
                    QgsMessageLog.logMessage('clean   %s' % cl2_range, level=Qgis.Critical)

                if merge_type == 'intersections':

                    self.graph.step = merge_range / float(len(self.graph.sNodes))
                    self.graph.merge_b_intersections(angle_threshold)
                    QgsMessageLog.logMessage('merge %s %s angle_threshold ' % (merge_range, angle_threshold),
                                             level=Qgis.Critical)

                elif merge_type == 'collinear':

                    self.graph.step = merge_range / float(len(self.graph.sEdges))
                    self.graph.merge_collinear(collinear_threshold, angle_threshold)
                    QgsMessageLog.logMessage('merge  %s' % merge_range, level=Qgis.Critical)

                # cleaned multiparts so that unlinks are generated properly
                if orphans:
                    self.graph.step = cl3_range / (float(len(self.graph.sEdges)) * 2.0)
                    self.graph.clean(True, orphans, snap_threshold, False, True)
                    QgsMessageLog.logMessage('clean  %s' % cl3_range, level=Qgis.Critical)
                else:
                    self.graph.step = cl3_range / (float(len(self.graph.sEdges)) * 2.0)
                    self.graph.clean(True, False, snap_threshold, False, True)
                    QgsMessageLog.logMessage('clean %s' % cl3_range, level=Qgis.Critical)

                if getUnlinks:
                    self.graph.step = unlinks_range / float(len(self.graph.sEdges))
                    self.graph.generate_unlinks()
                    QgsMessageLog.logMessage('unlinks generated %s' % unlinks_range, level=Qgis.Critical)
                    unlinks = self.graph.unlinks
                else:
                    unlinks = []

                cleaned_features = [e.feature for e in list(self.graph.sEdges.values())]
                # add to errors multiparts and points
                self.graph.errors += utf.multiparts
                self.graph.errors += utf.points

                if is_debug:
                    print("survived!")
                self.graph.progress.disconnect()
                self.cl_progress.emit(95)
                # return cleaned data, errors and unlinks
                ret = cleaned_features, self.graph.errors, unlinks

            except Exception as e:
                # forward the exception upstream
                self.error.emit(e, traceback.format_exc())

            self.finished.emit(ret)

        def kill(self):
            self.cl_killed = True
