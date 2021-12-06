# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2021-12-02
# copyright            : (C) 2021 by Space Syntax Ltd.
# author               : Petros Koutsolampros
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from typing import Dict
from esstoolkit.analysis.engines.AnalysisEngine import AnalysisEngine
from esstoolkit.analysis.engines.DepthmapNet.DepthmapNetEngine import DepthmapNetEngine


class EngineRegistry:
    """ Meant to hold and handle all available analysis engines """

    available_engines: Dict[str, str] = {}

    def __init__(self):
        self.available_engines[DepthmapNetEngine.get_engine_name()] = "DepthmapNetEngine"

    def get_available_engines(self) -> [str]:
        return self.available_engines.keys()

    def get_engine(self, type: str, iface: object) -> AnalysisEngine:
        if type not in self.available_engines:
            return
        return globals()[self.available_engines[type]](iface)
