# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2017 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import absolute_import

# Import the PyQt and QGIS libraries
from builtins import object

from qgis.PyQt.QtCore import (QSettings, QTranslator, QCoreApplication, qVersion, Qt)
from qgis.PyQt.QtGui import (QIcon, QPixmap)
from qgis.PyQt.QtWidgets import (QAction, QDialog)

# Import the debug library
is_debug = False
try:
    import pydevd_pycharm as pydevd

    has_pydevd = True
except ImportError:
    has_pydevd = False

import os.path
# change sys path to networkx package if not installed
import sys
import inspect

try:
    import networkx as nx
except ImportError:
    cmd_subfolder = os.path.realpath(
        os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "external")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)

# Import general esstoolkit modules
from .ui_About import Ui_AboutDialog
from .SettingsManager import SettingsManager
from .ProjectManager import ProjectManager

###########
###########
# Import esstoolkit tool modules
from esstoolkit.analysis import AnalysisTool
from esstoolkit.explorer import ExplorerTool
from esstoolkit.gate_transformer import TransformerAnalysis
from esstoolkit.rcl_cleaner import road_network_cleaner_tool
from esstoolkit.catchment_analyser import CatchmentAnalyser
from esstoolkit.urban_data_input import urban_data_input_tool
from esstoolkit.network_segmenter import network_segmenter_tool
from esstoolkit.drawing import DrawingTool


# import additional modules here
###########
###########

# todo: add documentation notes to all functions


class EssToolkit(object):

    def __init__(self, iface):
        # initialise plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'essTools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Save reference to the QGIS interface
        self.iface = iface
        self.toolbar = self.iface.addToolBar(u"Space Syntax Toolkit")
        self.menu = self.tr(u"&Space Syntax Toolkit")
        self.actions = []

        # Create toolkit components
        self.settings = SettingsManager(self.iface)
        self.settings_action = None
        self.project = ProjectManager(self.iface, self.settings)
        self.project_action = None
        self.about = AboutDialog()
        self.about_action = None

        # for remote debugging
        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)

        ###########
        ###########
        # initialise the different modules
        self.analysis = AnalysisTool.AnalysisTool(self.iface, self.settings, self.project)
        self.explorer = ExplorerTool.ExplorerTool(self.iface, self.settings, self.project)
        self.gate_transformer = TransformerAnalysis.GateTransformer(self.iface)
        self.rcl_cleaner = road_network_cleaner_tool.NetworkCleanerTool(self.iface)
        self.catchment_tool = CatchmentAnalyser.CatchmentTool(self.iface)
        self.udi_tool = urban_data_input_tool.UrbanDataInputTool(self.iface)
        self.drawing_tool = DrawingTool.DrawingTool(self.iface)
        self.network_segmenter = network_segmenter_tool.NetworkSegmenterTool(self.iface)
        # add additional modules here
        ###########
        ###########

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('EssToolkit', message)

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icons')

        ###########
        ###########
        # Create actions to start the different modules
        # graph analysis module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'esst_graph.png'),
                text=self.tr(u'Graph Analysis'),
                callback=self.showAnalysis,
                parent=self.iface.mainWindow(),
                status_tip='Graph Analysis'
            )
        )
        # pre-load setting of dockwidget
        self.analysis.load()
        self.analysis.dlg.close()
        # attribute explorer module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'esst_explorer.png'),
                text=self.tr(u'Attributes Explorer'),
                callback=self.showExplorer,
                parent=self.iface.mainWindow(),
                status_tip='Attributes Explorer'
            )
        )
        # pre-load setting of dockwidget
        self.explorer.load()
        self.explorer.dlg.close()
        # drawing module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'drawing.png'),
                text=self.tr(u'Drawing Tool'),
                callback=self.showDrawingTool,
                parent=self.iface.mainWindow(),
                status_tip='Drawing Tool'
            )
        )
        # rcl cleaner module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'rcl_cleaner.png'),
                text=self.tr(u'Road Network Cleaner'),
                callback=self.showRCLCleaner,
                parent=self.iface.mainWindow(),
                status_tip='Road Network Cleaner'
            )
        )
        # network segmenter module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'network_segmenter.png'),
                text=self.tr(u'Network Segmenter'),
                callback=self.showNetworkSegmenter,
                parent=self.iface.mainWindow(),
                status_tip='Network Segmenter'
            )
        )
        # catchment analyser module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'catchment_analyser.png'),
                text=self.tr(u'Catchment Analyser'),
                callback=self.showCatchmentAnalyser,
                parent=self.iface.mainWindow(),
                status_tip='Catchment Analyser'
            )
        )
        # urban data input module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'urban_data_input.png'),
                text=self.tr(u'Urban Data Input'),
                callback=self.showUrbanDataInput,
                parent=self.iface.mainWindow(),
                status_tip='Urban Data Input'
            )
        )
        # gate transformer module
        self.actions.append(
            self.add_action(
                os.path.join(icon_path, 'gate_transformer.png'),
                text=self.tr(u'Gate Transformer'),
                callback=self.showGateTransformer,
                parent=self.iface.mainWindow(),
                status_tip='Gate Transformer'
            )
        )

        # add additional modules here in the desired order
        ###########
        ###########

        # Create menu only toolkit components actions
        self.project_action = self.add_action(
            os.path.join(icon_path, 'project.png'),
            text=self.tr(u'Project'),
            callback=self.project.showDialog,
            parent=self.iface.mainWindow(),
            status_tip='Project',
            add_to_toolbar=False
        )
        self.settings_action = self.add_action(
            os.path.join(icon_path, 'settings.png'),
            text=self.tr(u'Settings'),
            callback=self.settings.showDialog,
            parent=self.iface.mainWindow(),
            status_tip='Settings',
            add_to_toolbar=False
        )
        self.about_action = self.add_action(
            os.path.join(icon_path, 'about.png'),
            text=self.tr(u'About'),
            callback=self.about.show,
            parent=self.iface.mainWindow(),
            status_tip='About',
            add_to_toolbar=False
        )

    ###########
    ###########
    def showAnalysis(self):
        self.iface.removeDockWidget(self.explorer.dlg)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.analysis.dlg)

    def showExplorer(self):
        self.iface.removeDockWidget(self.analysis.dlg)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.explorer.dlg)

    def showGateTransformer(self):
        self.gate_transformer.load_gui()

    def showRCLCleaner(self):
        self.rcl_cleaner.loadGUI()

    def showCatchmentAnalyser(self):
        self.catchment_tool.load_gui()

    def showUrbanDataInput(self):
        self.udi_tool.load_gui()

    def showNetworkSegmenter(self):
        self.network_segmenter.loadGUI()

    def showDrawingTool(self):
        self.drawing_tool.run()

    # add additional modules here
    ###########
    ###########

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        # remove the toolkit menu items
        self.iface.removePluginVectorMenu(self.menu, self.project_action)
        self.iface.removePluginVectorMenu(self.menu, self.settings_action)
        self.iface.removePluginVectorMenu(self.menu, self.about_action)
        # remove the actions on the toolbar
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.menu,
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        try:
            del self.toolbar
        except:
            pass

        ###########
        ###########
        # Remove dockwidget based modules
        self.iface.removeDockWidget(self.analysis.dlg)
        self.iface.removeDockWidget(self.explorer.dlg)
        # Unload the modules
        self.analysis.unload()
        self.explorer.unload()
        self.gate_transformer.unload_gui()
        self.rcl_cleaner.unloadGUI()
        self.catchment_tool.unload_gui()
        self.udi_tool.unload_gui()
        self.drawing_tool.unload()
        self.network_segmenter.unloadGUI()
        # add additional modules here
        ###########
        ###########

    def showMessage(self, msg, lev, dur, type):
        self.iface.messageBar().pushMessage("Info", msg, level=lev, duration=dur)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):

        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        return action


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        # set up internal GUI signals
        self.closeButton.clicked.connect(self.close)

        # load text
        about_msg = (
            'The "Space Syntax Toolkit" is a collection of tools for space syntax analysis workflows in the QGIS environment.\n'
            'It was originally developed at the Space Syntax Laboratory, the Bartlett, University College London (UCL).\n\n'
            'Mailing list: spacesyntax-toolkit@jiscmail.ac.uk\n\n'
            'Author: Jorge Gil\n\n'
            'It includes contributions from:\n\n'
            '- Space Syntax Limited:\n'
            'Ioanna Kovolou, Abhimanyu Acharya, Stephen Law, Laurens Versluis\n\n'
            '\nReleased under GNU Licence version 3')

        self.messageText.setText(about_msg)

        # load logos
        self.logoLabel.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'contrib_logos.png')))
