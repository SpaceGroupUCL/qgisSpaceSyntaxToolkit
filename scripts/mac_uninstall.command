# Script for uninstalling Space Syntax Toolkit plugin for QGIS on Mac OS/X

# Path variables
rcl_plugin_dir=~/.qgis2/python/plugins/esstoolkit

# Make sure QGIS is installed
if [ ! -d "$rcl_plugin_dir" ]; then
	echo "Space Syntax Toolkit QGIS plugin not found."
	exit 1
fi

rm -rf "$rcl_plugin_dir"
if [ $? -ne 0 ]; then
	echo "ERROR: Couldn't remove currently installed Space Syntax Toolkit QGIS plugin."
	echo "Please close QGIS if it is running, and then try again."
	exit 1
fi

echo "Space Syntax Toolkit QGIS plugin was successfully uninstalled."
