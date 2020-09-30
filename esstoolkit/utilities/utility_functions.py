# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015, UCL
# author               : Jorge Gil, Petros Koutsolampros
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import print_function

import math
from builtins import range
from builtins import str

import numpy as np


# ------------------------------
# General functions
# ------------------------------

# check if a text string is of numeric type
def isNumeric(txt):
    try:
        int(txt)
        return True
    except ValueError:
        try:
            int(txt)
            return True
        except ValueError:
            try:
                float(txt)
                return True
            except ValueError:
                return False


# convert a text string to a numeric value, if possible
def convertNumeric(txt):
    try:
        value = int(txt)
    except ValueError:
        try:
            value = int(txt)
        except ValueError:
            try:
                value = float(txt)
            except ValueError:
                value = ''
    return value


# round number based on simple rules of thumb
# for suggestion on the best number to round
# some principles found here: http://www.tc3.edu/instruct/sbrown/stat/rounding.htm
def roundNumber(num):
    if isNumeric(num):
        if isinstance(num, str):
            convertNumeric(num)
        rounded = num
        if num > 100 or num < -100:
            rounded = round(num, 1)
        elif (1 < num <= 100) or (-1 > num >= -100):
            rounded = round(num, 2)
        elif (0.01 < num <= 1) or (-0.01 > num >= -1):
            rounded = round(num, 4)
        else:
            rounded = round(num, 6)
        return rounded


def truncateNumberString(num, digits=9):
    if isNumeric(num):
        truncated = str(num)
        if '.' in truncated:
            truncated = truncated[:digits]
            truncated = truncated.rstrip('0').rstrip('.')
        return convertNumeric(truncated)


def truncateNumber(num, digits=9):
    if isNumeric(num):
        truncated = math.floor(num * 10 ** digits) / 10 ** digits
        return truncated


def numSigDigits(num):
    """Returns the number of significant digits in a number.
    based on code by unclej
    see: http://www.power-quant.com/?q=node/85
    """
    numdigits = -1
    decimal = u'.'
    if isNumeric(num):
        # number the digits:
        enumerated_chars = list(enumerate(str(num)))
        # for x in enumerated_chars:
        #    if x[1] in (u'.',u','):
        #        decimal = x[1]
        non_zero_chars = [x for x in enumerated_chars if (x[1] != '0') and (x[1] != decimal)]
        most_sig_digit = non_zero_chars[0]
        least_sig_digit = None
        if decimal in [x[1] for x in enumerated_chars]:
            least_sig_digit = enumerated_chars[-1]
        else:
            least_sig_digit = non_zero_chars[-1]

        enumed_sig_digits = [x for x in enumerated_chars[most_sig_digit[0]:least_sig_digit[0] + 1]]
        numdigits = len(enumed_sig_digits)
        if decimal in [x[1] for x in enumerated_chars]:
            numdigits -= 1

    return numdigits


def roundSigDigits(num, sig_figs):
    """ Round to specified number of significant digits.
    by Ben Hoyt
    see: http://code.activestate.com/recipes/578114-round-number-to-specified-number-of-significant-di/
    """
    if num != 0:
        return round(num, -int(math.floor(math.log10(abs(num))) - (sig_figs - 1)))
    else:
        return 0  # Can't take the log of 0


def calcGini(values):
    """
    Calculate gini coefficient, using transformed formula, like R code in 'ineq'
    :param values: list of numeric values
    :return: gini coefficient
    """
    S = sorted(values)
    N = len(values)
    T = sum(values)
    P = sum(xi * (i + 1) for i, xi in enumerate(S))
    G = 2.0 * P / (N * T)
    gini = G - 1 - (1. / N)
    return gini


def calcBins(values, minbins=3, maxbins=128):
    """Calculates the best number of bins for the given values
    Uses the Freedman-Diaconis modification of Scott's rule.
    """
    nbins = 1
    # prepare data
    if not isinstance(values, np.ndarray):
        values = np.array(values)
    # calculate stats
    range = np.nanmax(values) - np.nanmin(values)
    IQR = np.percentile(values, 75) - np.percentile(values, 25)
    # calculate bin size
    bin_size = 2 * IQR * np.size(values) ** (-1.0 / 3)
    # calculate number of bins
    if bin_size > 0:
        nbins = range / bin_size

    nbins = max(minbins, min(maxbins, int(nbins)))

    return nbins


# fixme: this calculates pearson correlation, not p value!
def calcPvalue(x, y):
    n = len(x)
    if not n == len(y) or not n > 0:
        pearson = None
    else:
        avg_x = float(sum(x)) / n
        avg_y = float(sum(y)) / n
        diffprod = 0
        xdiff2 = 0
        ydiff2 = 0
        for idx in range(n):
            xdiff = x[idx] - avg_x
            ydiff = y[idx] - avg_y
            diffprod += xdiff * ydiff
            xdiff2 += xdiff * xdiff
            ydiff2 += ydiff * ydiff
        pearson = diffprod / math.sqrt(xdiff2 * ydiff2)
    return pearson
