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

import unittest

from esstoolkit.utilities import utility_functions as uf


class TestUtilityFunctions(unittest.TestCase):

    def test_isNumeric(self):
        self.assertTrue(uf.isNumeric("1"))
        self.assertTrue(uf.isNumeric(u"\u0031"))  # unicode 1
        self.assertTrue(uf.isNumeric("1.2"))
        self.assertTrue(uf.isNumeric("19245"))
        # self.assertTrue(uf.isNumeric("19,241"))
        self.assertTrue(uf.isNumeric("-5"))
        self.assertTrue(uf.isNumeric(1))
        self.assertTrue(uf.isNumeric(1.2))
        self.assertTrue(uf.isNumeric(19245))
        self.assertTrue(uf.isNumeric(-5))
        self.assertFalse(uf.isNumeric("a"))
        self.assertFalse(uf.isNumeric("4a"))
        self.assertFalse(uf.isNumeric("foo4a"))
        self.assertFalse(uf.isNumeric("-t6"))

    def test_convertNumeric(self):
        self.assertEqual(uf.convertNumeric("1"), 1)
        self.assertEqual(uf.convertNumeric("6.4"), 6.4)
        self.assertEqual(uf.convertNumeric("19245"), 19245)
        # self.assertEqual(uf.convertNumeric("19,241"), 19241)
        self.assertEqual(uf.convertNumeric("-144.0"), -144)
        self.assertEqual(uf.convertNumeric("a"), '')

    def test_roundNumber_wrong_type(self):
        self.assertRaises(TypeError, lambda: uf.roundNumber("0.002000"))

    def test_roundNumber_under_001(self):
        self.assertEqual(uf.roundNumber(0.002000), 0.002000)
        self.assertEqual(uf.roundNumber(0.00200045), 0.002000)
        self.assertEqual(uf.roundNumber(0.00200055), 0.002001)
        self.assertEqual(uf.roundNumber(-0.002000), -0.002000)
        self.assertEqual(uf.roundNumber(-0.00200045), -0.002000)
        self.assertEqual(uf.roundNumber(-0.00200055), -0.002001)

    def test_roundNumber_001_1(self):
        self.assertEqual(uf.roundNumber(0.2000), 0.2000)
        self.assertEqual(uf.roundNumber(0.200045), 0.2000)
        self.assertEqual(uf.roundNumber(0.200055), 0.2001)
        self.assertEqual(uf.roundNumber(-0.2000), -0.2000)
        self.assertEqual(uf.roundNumber(-0.200045), -0.2000)
        self.assertEqual(uf.roundNumber(-0.200055), -0.2001)

    def test_roundNumber_1_100(self):
        self.assertEqual(uf.roundNumber(2.00), 2.00)
        self.assertEqual(uf.roundNumber(2.0045), 2.00)
        self.assertEqual(uf.roundNumber(2.0055), 2.01)
        self.assertEqual(uf.roundNumber(-2.00), -2.00)
        self.assertEqual(uf.roundNumber(-2.0045), -2.00)
        self.assertEqual(uf.roundNumber(-2.0055), -2.01)

    def test_roundNumber_over_100(self):
        self.assertEqual(uf.roundNumber(200.0), 200.0)
        self.assertEqual(uf.roundNumber(200.045), 200.0)
        self.assertEqual(uf.roundNumber(200.055), 200.1)
        self.assertEqual(uf.roundNumber(-200.0), -200.0)
        self.assertEqual(uf.roundNumber(-200.045), -200.0)
        self.assertEqual(uf.roundNumber(-200.055), -200.1)

    def test_truncateNumber(self):
        self.assertEqual(uf.truncateNumber(0.0000000045), 0.000000004)
        self.assertEqual(uf.truncateNumber(0.045, 2), 0.04)
        self.assertEqual(uf.truncateNumber(-0.045, 2), -0.05)
        self.assertRaises(TypeError, lambda: uf.truncateNumber("0.045"))

    def test_roundSigDigits(self):
        self.assertEqual(uf.roundSigDigits(0, sig_figs=4), 0)
        self.assertEqual(uf.roundSigDigits(12345, sig_figs=2), 12000)
        self.assertEqual(uf.roundSigDigits(-12345, sig_figs=2), -12000)
        self.assertEqual(uf.roundSigDigits(1, sig_figs=2), 1)
        self.assertEqual(uf.roundSigDigits(3.1415, sig_figs=2), 3.1)
        self.assertEqual(uf.roundSigDigits(-3.1415, sig_figs=2), -3.1)
        self.assertEqual(uf.roundSigDigits(0.00098765, sig_figs=2), 0.00099)
        self.assertEqual(uf.roundSigDigits(0.00098765, sig_figs=3), 0.000988)
        self.assertRaises(TypeError, lambda: uf.roundSigDigits("0.00098765", sig_figs=3))

    def test_calcGini(self):
        self.assertAlmostEqual(uf.calcGini([1, 1, 4, 10, 10]), 0.4153846)
        self.assertAlmostEqual(uf.calcGini([1, 1, 1, 1, 100]), 0.76153846)
        self.assertAlmostEqual(uf.calcGini([1, 1, 1, 1, 1]), 0)
        self.assertAlmostEqual(uf.calcGini([0, 1]), 0.5)
        self.assertAlmostEqual(uf.calcGini([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]), 0.95)

    def test_calcBins(self):
        self.assertEqual(uf.calcBins([1, 1, 4, 10, 10]), 3)
        self.assertEqual(uf.calcBins([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]), 3)
        self.assertEqual(uf.calcBins([1, 1, 4, 100, 10000]), 86)
        self.assertEqual(uf.calcBins([-1000, 1, 1, 4, 100, 10000]), 128)

    def test_calcPvalue(self):
        self.assertAlmostEqual(uf.calcPvalue([1, 1, 4, 10, 10], [1, 1, 4, 10, 10]), 1)
        self.assertAlmostEqual(uf.calcPvalue([0, 5, 10], [10, 5, 0]), -1)
        self.assertAlmostEqual(uf.calcPvalue([2.044, -2.709, 0.192, 0.695], [-0.473, -0.578, 0.222, -0.686]), 0.1011293)


if __name__ == '__main__':
    unittest.main()
