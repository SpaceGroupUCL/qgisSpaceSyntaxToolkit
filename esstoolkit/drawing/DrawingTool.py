# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DrawingTool
                                 A QGIS plugin
 Drawing tool for axial lines, segment lines and unlinks.
                              -------------------
        begin                : 2019-06-16
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Space Syntax Limited
        email                : i.kolovou@spaceyntax.com
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


from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from DrawingTool_dockwidget import DrawingToolDockWidget
import os.path


class DrawingTool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.legend = self.iface.legendInterface()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DrawingTool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Drawing Tool')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'DrawingTool')
        self.toolbar.setObjectName(u'DrawingTool')

        #print "** INITIALIZING DrawingTool"

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DrawingTool', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
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

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/DrawingTool/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Draw'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING DrawingTool"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.legend.itemAdded.disconnect(self.pop_layer)
        self.legend.itemRemoved.disconnect(self.rmv_layer)
        self.dockwidget.networkCombo.currentIndexChanged.disconnect(self.dockwidget.update_settings)
        self.dockwidget.unlinksCombo.currentIndexChanged.disconnect(self.dockwidget.update_settings)
        self.dockwidget.toleranceSpin.valueChanged.disconnect(self.dockwidget.update_settings)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD DrawingTool"

        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Drawing Tool'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def get_layers(self, geom_type):
        layers = []
        for layer in self.legend.layers():
            if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
                if layer.hasGeometryType() and (layer.geometryType() == geom_type):
                    layers.append(layer.name())
        return layers

    def pop_layers(self):

        self.dockwidget.networkCombo.clear()
        self.dockwidget.networkCombo.addItems(self.get_layers(1))
        self.dockwidget.unlinksCombo.clear()
        self.dockwidget.unlinksCombo.addItems(['no unlinks'] + self.get_layers(0))

        return

    def pop_layer(self):
        new = list(self.get_layers(1))
        for l in self.networks:
            try:
                new.remove(l)
            except ValueError:
                pass
        if len(new)>0:
            print 'new', new, self.get_layers(1), self.networks
            self.networks += new
            self.dockwidget.networkCombo.addItems(new)
        new = list(self.get_layers(0))
        for l in self.unlinks:
            try:
                new.remove(l)
            except ValueError:
                pass
        if len(new)>0:
            self.unlinks += new
            self.dockwidget.unlinksCombo.addItems(new)
        return

    def rmv_layer(self):
        old = list(self.networks)
        for l in self.get_layers(1):
            print 'old', old
            old.remove(l)
        if len(old) > 0:
            index = self.dockwidget.networkCombo.findText(old[0])
            self.dockwidget.networkCombo.removeItem(index)
            self.networks.remove(old[0])
        old = list(self.unlinks)
        for l in self.get_layers(0):
            print 'old', old
            old.remove(l)
        if len(old) > 0:
            self.unlinks.remove(old[0])
            index = self.dockwidget.unlinksCombo.findText(old[0])
            self.dockwidget.unlinksCombo.removeItem(index)
        return

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING DrawingTool"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = DrawingToolDockWidget(self.iface)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            self.dockwidget.networkCombo.addItems(self.get_layers(1))
            self.dockwidget.unlinksCombo.addItems(['no unlinks'] + self.get_layers(0))
            self.dockwidget.update_network()
            self.dockwidget.update_unlinks()
            self.dockwidget.update_tolerance()
            self.networks = self.get_layers(1)
            self.unlinks = ['no unlinks'] + self.get_layers(0)
            self.legend.itemAdded.connect(self.pop_layer)
            self.legend.itemRemoved.connect(self.rmv_layer)
            self.dockwidget.networkCombo.currentIndexChanged.connect(self.dockwidget.update_network)
            self.dockwidget.unlinksCombo.currentIndexChanged.connect(self.dockwidget.update_unlinks)
            self.dockwidget.toleranceSpin.valueChanged.connect(self.dockwidget.update_tolerance)