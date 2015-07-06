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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# Import the debug library
# can set is_debug to False in release version
is_debug = False
try:
    import pydevd
    has_pydevd = True
except ImportError, e:
    has_pydevd = False
    is_debug = False

import os.path
#change sys path to networkx package if not installed
import sys
import inspect
try:
    import networkx as nx
except ImportError, e:
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0],"external")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)

# Initialize Qt resources from file resources.py
from resources_rc import *

# Import general esstoolkit modules
from ui_About import Ui_AboutDialog
from SettingsManager import SettingsManager
from ProjectManager import ProjectManager

# Import esstoolkit tool modules
from analysis import AnalysisTool
from explorer import ExplorerTool

from . import utility_functions as uf


# todo: add documentation notes to all functions
# todo edit Makefile
# todo edit plugin_upload.py

class EssToolkit:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.esst_toolbar = self.iface.addToolBar(u"Space Syntax Toolkit")

        # initialise plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QtCore.QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'essTools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QtCore.QTranslator()
            self.translator.load(locale_path)

            if QtCore.qVersion() > '4.3.3':
                QtCore.QCoreApplication.installTranslator(self.translator)

        # initialise base modules and interface actions
        self.settings = SettingsManager(self.iface)
        self.settings_action = None
        self.project = ProjectManager(self.iface, self.settings)
        self.project_action = None
        self.about_action = None
        self.help_action = None

        # initialise the tool modules and interface actions
        self.analysis = AnalysisTool.AnalysisTool(self.iface, self.settings, self.project)
        self.analysis_action = None
        self.explorer = ExplorerTool.ExplorerTool(self.iface, self.settings, self.project)
        self.explorer_action = None
        # Create other dialogs
        self.about = AboutDialog()

        # initialise default events
        #self.project.loadSettings()

        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)

    def initGui(self):
        # Create action to start the modules
        icon = QIcon(os.path.dirname(__file__) + "/icons/project.png")
        self.project_action = QAction(icon, u"Project", self.iface.mainWindow())
        self.project_action.triggered.connect(self.project.showDialog)
        icon = QIcon(os.path.dirname(__file__) + "/icons/esst_graph.png")
        self.analysis_action = QAction(icon, u"Graph Analysis", self.iface.mainWindow())
        self.analysis_action.triggered.connect(self.showAnalysis)
        icon = QIcon(os.path.dirname(__file__) + "/icons/esst_explorer.png")
        self.explorer_action = QAction(icon, u"Attributes Explorer", self.iface.mainWindow())
        self.explorer_action.triggered.connect(self.showExplorer)
        #icon = QIcon(os.path.dirname(__file__) + "/icons/settings.png")
        #self.settings_action = QAction(icon, u"Settings", self.iface.mainWindow())
        #self.settings_action.triggered.connect(self.settings.showDialog)
        #icon = QIcon(os.path.dirname(__file__) + "/icons/help.png")
        #self.help_action = QAction(icon, u"Help", self.iface.mainWindow())
        #self.help_action.triggered.connect(self.showHelp)
        #icon = QIcon(os.path.dirname(__file__) + "/icons/about.png")
        #self.about_action = QAction(icon, u"About", self.iface.mainWindow())
        #self.about_action.triggered.connect(self.about.show)

        # Add toolbar button and menu items
        self.esst_toolbar.addAction(self.analysis_action)
        self.esst_toolbar.addAction(self.explorer_action)
        self.iface.addPluginToVectorMenu(u"&Space Syntax Toolkit", self.analysis_action)
        self.iface.addPluginToVectorMenu(u"&Space Syntax Toolkit", self.explorer_action)
        self.iface.addPluginToVectorMenu(u"&Space Syntax Toolkit", self.project_action)
        #self.iface.addPluginToVectorMenu(u"&Space Syntax Toolkit", self.settings_action)
        #self.iface.addPluginToVectorMenu(u"&Space Syntax Toolkit", self.help_action)
        #self.iface.addPluginToVectorMenu(u"&Space Syntax Toolkit", self.about_action)

    def showAnalysis(self):
        #self.iface.removeDockWidget(self.explorer.dlg)
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.analysis.dlg)

    def showExplorer(self):
        #self.iface.removeDockWidget(self.analysis.dlg)
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.explorer.dlg)

    def showHelp(self):
        # todo: decide what to do for help documentation
        pass

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginVectorMenu(u"&Space Syntax Toolkit", self.analysis_action)
        self.iface.removePluginVectorMenu(u"&Space Syntax Toolkit", self.explorer_action)
        self.iface.removePluginVectorMenu(u"&Space Syntax Toolkit", self.project_action)
        #self.iface.removePluginVectorMenu(u"&Space Syntax Toolkit", self.settings_action)
        #self.iface.removePluginVectorMenu(u"&Space Syntax Toolkit", self.help_action)
        #self.iface.removePluginVectorMenu(u"&Space Syntax Toolkit", self.about_action)

        # Remove the toolbar buttons
        self.iface.removeToolBarIcon(self.analysis_action)
        self.iface.removeToolBarIcon(self.explorer_action)

        # Remove the dialogs
        self.iface.removeDockWidget(self.analysis.dlg)
        self.iface.removeDockWidget(self.explorer.dlg)

    def showMessage(self, msg, lev, dur, type):
        self.iface.messageBar().pushMessage("Info",msg,level=lev,duration=dur)

#
class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self):

        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        # set up internal GUI signals
        QtCore.QObject.connect(self.closeButton,QtCore.SIGNAL("clicked()"),self.close)