# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RoadNetworkCleaner
                                 A QGIS plugin
 This plugin clean a road centre line map.
                              -------------------
        begin                : 2016-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Space SyntaxLtd
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
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from qgis.PyQt.QtCore import Qt, QThread, QSettings

from qgis.core import *
from qgis.gui import *
from qgis.utils import *

#import db_manager.db_plugins.postgis.connector as con
import traceback

# Initialize Qt resources from file resources.py
#from .. import resources
# the dialog modules
from .road_network_cleaner_dialog import RoadNetworkCleanerDialog

# additional modules
from .sGraph.break_tools import *  # better give these a name to make it explicit to which module the methods belong
from .sGraph.merge_tools import *
from .sGraph.utilityFunctions import *

# Import the debug library - required for the cleaning class in separate thread
# set is_debug to False in release version
is_debug = False
try:
    import pydevd_pycharm as pydevd
    has_pydevd = True
except ImportError as e:
    has_pydevd = False
    is_debug = False


class RoadNetworkCleaner(QObject):

    # initialise class with self and iface
    def __init__(self, iface):
        QObject.__init__(self)

        self.iface=iface
        self.legend = QgsProject.instance().mapLayers()

        # load the dialog from the run method otherwise the objects gets created multiple times
        self.dlg = None

        # some globals
        self.cleaning = None
        self.thread = None

    def loadGUI(self):
        # create the dialog objects
        self.dlg = RoadNetworkCleanerDialog(self.getQGISDbs())

        # setup GUI signals
        self.dlg.closingPlugin.connect(self.unloadGUI)
        self.dlg.cleanButton.clicked.connect(self.startCleaning)
        self.dlg.cancelButton.clicked.connect(self.killCleaning)

        # add layers to dialog
        self.updateLayers()

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
            self.dlg.cleanButton.clicked.disconnect(self.startCleaning)
            self.dlg.cancelButton.clicked.disconnect(self.killCleaning)
            self.settings = None
        try:
            QgsProject.instance().layersAdded.disconnect(self.updateLayers)
            QgsProject.instance().layersRemoved.disconnect(self.updateLayers)
        except TypeError:
            pass

        self.dlg = None

    def getQGISDbs(self):
        """Return all PostGIS connection settings stored in QGIS
        :return: connection dict() with name and other settings
        """
        con_settings = []
        settings = QSettings()
        settings.beginGroup('/PostgreSQL/connections')
        for item in settings.childGroups():
            con = dict()
            con['name'] = str(item)
            con['host'] = str(settings.value(u'%s/host' % str(item)))
            con['port'] = str(settings.value(u'%s/port' % str(item)))
            con['database'] = str(settings.value(u'%s/database' % str(item)))
            con['username'] = str(settings.value(u'%s/username' % str(item)))
            con['password'] = str(settings.value(u'%s/password' % str(item)))
            con_settings.append(con)
        settings.endGroup()
        dbs = {}
        if len(con_settings) > 0:
            for conn in con_settings:
                dbs[conn['name']]= conn
        return dbs

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

    # SOURCE: Network Segmenter https://github.com/OpenDigitalWorks/NetworkSegmenter
    # SOURCE: https://snorfalorpagus.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/

    def giveMessage(self, message, level):
        # Gives warning according to message
        self.iface.messageBar().pushMessage("Road network cleaner: ", "%s" % (message), level, duration=5)

    def cleaningError(self, e, exception_string):
        # Gives error according to message
        QgsMessageLog.logMessage('Cleaning thread raised an exception: %s' % exception_string, level=Qgis.Critical)
        self.dlg.close()

    def startCleaning(self):
        self.dlg.cleaningProgress.reset()
        self.settings = self.dlg.get_settings()
        if self.settings['output_type'] == 'postgis':
            db_settings = self.dlg.get_dbsettings()
            self.settings.update(db_settings)

        if self.settings['input']:

            cleaning = self.clean(self.settings, self.iface)
            # start the cleaning in a new thread
            thread = QThread()
            cleaning.moveToThread(thread)
            cleaning.finished.connect(self.cleaningFinished)
            cleaning.error.connect(self.cleaningError)
            cleaning.warning.connect(self.giveMessage)
            cleaning.cl_progress.connect(self.dlg.cleaningProgress.setValue)

            thread.started.connect(cleaning.run)
            # thread.finished.connect(self.cleaningFinished)

            self.thread = thread
            self.cleaning = cleaning

            self.thread.start()

            if is_debug:
                print('started')
        else:
            self.giveMessage('Missing user input!', Qgis.Info)
            return

    def cleaningFinished(self, ret):
        if is_debug:
            print('trying to finish')
        # get cleaning settings
        layer_name = self.settings['input']
        path = self.settings['output']
        output_type = self.settings['output_type']
        #  get settings from layer
        layer = getLayerByName(layer_name)
        crs = layer.dataProvider().crs()
        encoding = layer.dataProvider().encoding()
        geom_type = layer.dataProvider().geometryType()
        # create the cleaning results layers
        try:
            # create clean layer
            if output_type == 'shp':
                final = to_shp(path, ret[0][0], ret[0][1], crs, 'cleaned', encoding, geom_type)
            elif output_type == 'memory':
                final = to_shp(None, ret[0][0], ret[0][1], crs, path, encoding, geom_type)
            else:
                final = to_dblayer(self.settings['dbname'], self.settings['user'], self.settings['host'],
                                   self.settings['port'], self.settings['password'], self.settings['schema'],
                                   self.settings['table_name'], ret[0][1], ret[0][0], crs)
            if final:
                QgsProject.instance().addMapLayer(final)
                final.updateExtents()
            # create errors layer
            if self.settings['errors']:
                errors = to_shp(None, ret[1][0], ret[1][1], crs, 'errors', encoding, geom_type)
                if errors:
                    QgsProject.instance().addMapLayer(errors)
                    errors.updateExtents()
            # create unlinks layer
            if self.settings['unlinks']:
                unlinks = to_shp(None, ret[2][0], ret[2][1], crs, 'unlinks', encoding, 0)
                if unlinks:
                    QgsProject.instance().addMapLayer(unlinks)
                    unlinks.updateExtents()

            self.iface.mapCanvas().refresh()

            self.giveMessage('Process ended successfully!', Qgis.Info)

        except Exception as e:
            # notify the user that sth went wrong
            self.cleaning.error.emit(e, traceback.format_exc())
            self.giveMessage('Something went wrong! See the message log for more information', Qgis.Critical)

        # clean up the worker and thread
        #self.cleaning.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        if is_debug:
            print('thread running ', self.thread.isRunning())
        if is_debug:
            print('has finished ', self.thread.isFinished())

        self.thread = None
        self.cleaning = None

        if self.dlg:
            self.dlg.cleaningProgress.reset()
            self.dlg.close()

    def killCleaning(self):
        if is_debug:
            print('trying to cancel')
        # add emit signal to breakTool or mergeTool only to stop the loop
        if self.cleaning:

            try:
                dummy = self.cleaning.br
                del dummy
                self.cleaning.br.killed = True
            except AttributeError:
                pass
            try:
                dummy = self.cleaning.mrg
                del dummy
                self.cleaning.mrg.killed = True
            except AttributeError:
                pass
            # Disconnect signals
            self.cleaning.finished.disconnect(self.cleaningFinished)
            self.cleaning.error.disconnect(self.cleaningError)
            self.cleaning.warning.disconnect(self.giveMessage)
            self.cleaning.cl_progress.disconnect(self.dlg.cleaningProgress.setValue)
            # Clean up thread and analysis
            self.cleaning.kill()
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
    class clean(QObject):

        # Setup signals
        finished = pyqtSignal(object)
        error = pyqtSignal(Exception, str)
        cl_progress = pyqtSignal(float)
        warning = pyqtSignal(str)
        cl_killed = pyqtSignal(bool)

        def __init__(self, settings, iface):
            QObject.__init__(self)
            self.settings = settings
            self.iface = iface
            self.total =0

        def add_step(self,step):
            self.total += step
            return self.total

        def run(self):
            if has_pydevd and is_debug:
                pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
            ret = None
            if self.settings:
                try:
                    # cleaning settings
                    layer_name = self.settings['input']
                    tolerance = self.settings['tolerance']
                    # project settings
                    layer = getLayerByName(layer_name)

                    self.cl_progress.emit(2)

                    self.br = breakTool(layer, tolerance, None, self.settings['errors'], self.settings['unlinks'])

                    if self.cl_killed is True or self.br.killed is True: return

                    self.br.add_edges()

                    if self.cl_killed is True or self.br.killed is True: return

                    self.cl_progress.emit(5)
                    self.total = 5
                    step = 40/ self.br.feat_count
                    self.br.progress.connect(lambda incr=self.add_step(step): self.cl_progress.emit(incr))

                    broken_features = self.br.break_features()

                    if self.cl_killed is True or self.br.killed is True: return

                    self.cl_progress.emit(45)

                    self.mrg = mergeTool(broken_features, None, True)

                    # TODO test
                    try:
                        step = 40/ len(self.mrg.con_1)
                        self.mrg.progress.connect(lambda incr=self.add_step(step): self.cl_progress.emit(incr))
                    except ZeroDivisionError:
                        pass

                    merged_features = self.mrg.merge()

                    if self.cl_killed is True or self.mrg.killed is True: return

                    fields = self.br.layer_fields

                    # prepare other output data
                    ((errors_list, errors_fields), (unlinks_list, unlinks_fields)) = ((None, None), (None, None))
                    if self.settings['errors']:
                        self.br.updateErrors(self.mrg.errors_features)
                        errors_list = [[k, [[k], [v[0]]], v[1]] for k, v in list(self.br.errors_features.items())]
                        errors_fields = [QgsField('id_input', QVariant.Int), QgsField('errors', QVariant.String)]

                    if self.settings['unlinks']:
                        unlinks_list = self.br.unlinked_features
                        unlinks_fields = [QgsField('id', QVariant.Int), QgsField('line_id1', QVariant.Int), QgsField('line_id2', QVariant.Int), QgsField('x', QVariant.Double), QgsField('y', QVariant.Double)]

                    if is_debug:
                        print("survived!")
                    self.cl_progress.emit(100)
                    # return cleaned data, errors and unlinks
                    ret = ((merged_features, fields), (errors_list, errors_fields), (unlinks_list, unlinks_fields))

                except Exception as e:
                    # forward the exception upstream
                    self.error.emit(e, traceback.format_exc())

            self.finished.emit(ret)

        def kill(self):
            self.cl_killed = True
