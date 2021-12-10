from qgis.PyQt.QtWidgets import QWidget
from esstoolkit.utilities.utility_functions import isNumeric


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

    @staticmethod
    def parse_radii(txt, nAs0):
        radii = txt
        radii.lower()
        radii = radii.replace(' ', '')
        radii = radii.split(',')
        radii.sort()
        radii = list(set(radii))
        if nAs0:
            radii = ['0' if x == 'n' else x for x in radii]
        for r in radii:
            if r == 'n':
                if nAs0:
                    return ''
            elif not isNumeric(r):
                return ''
        radii = ','.join(radii)
        return radii
