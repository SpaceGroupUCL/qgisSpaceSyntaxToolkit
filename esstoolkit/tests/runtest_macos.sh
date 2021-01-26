#!/bin/sh
# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2020-08-01
# copyright            : (C) 2020 by Petros Koutsolampros / Space Syntax Ltd.
# author               : Petros Koutsolampros
# email                : p.koutsolampros@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This script is provided as a helper to run the tests. While it is placed in the tests directory,
# it should be called from the esstoolkit directory and a test provided as a module argument:
# ./tests/runtest_macos.sh tests.test_utility_functions

QGISPATH="/Applications/QGIS3.10.app"
export PYTHONPATH="${PYTHONPATH}:${QGISPATH}/Contents/Resources/python/"
export QT_QPA_PLATFORM_PLUGIN_PATH="${QGISPATH}/Contents/PlugIns"
${QGISPATH}/Contents/MacOS/bin/python3 -m $1
