#/bin/sh

# Note: For this to work with QGIS, install sphinx, sphinxExtensions
# and sphinx-rtd-theme (read the docs theme) from within PyCharm.
# As the QGIS python is in the application folder and may thus not be
# writable, installing at the User location should work

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
cd ../docs/
# delete existing autogen directory
rm -rf source/_autogen
# generate the rst files
sphinx-apidoc -f -e -o source/_autogen/modules/ ../esstoolkit/ ../esstoolkit/external/* ../esstoolkit/tests/* ../esstoolkit/*/ui_* ../esstoolkit/ui_*
# generate the html files
pwd
sphinx-build -b html source build