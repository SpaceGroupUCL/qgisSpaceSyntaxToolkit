from qgis.PyQt.QtWidgets import QWidget


class SettingsWidget(QWidget):
    def __init__(self, dock_widget):
        QWidget.__init__(self)
        self.dockWidget = dock_widget

    def dock_widget_settings_changed(self):
        """
        Meant to be triggered by the analysis dock widget to allow the engine
        widget to synchronise its settings accordingly
        """
        pass
