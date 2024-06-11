#! /usr/bin/env python3
#
# Copyright (C) 2024  Michael Gale
# This file is part of the pyldraw python module.
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Helper functions

import decimal
from .geometry import Vector


def quantize(x, tol=-6):
    """Quantizes an string LDraw value to 4 decimal places"""
    v = decimal.Decimal(x.strip()).quantize(decimal.Decimal(10) ** tol)
    return float(v)


def val_units(value):
    """
    Writes a floating point value in units of either mm or ldu.
    It restricts the number of decimal places to 4 and minimizes
    redundant trailing zeros (as recommended by ldraw.org)
    """
    xs = "%.5f" % (value)
    ns = str(quantize(xs, tol=-4)).replace("0E-4", "0.")
    if "E" not in ns:
        ns = ns.rstrip("0")
    ns = ns.rstrip(".")
    if ns == "-0":
        return "0"
    return ns


def mat_str(m):
    """
    Writes the values of a matrix
    """
    return " ".join([val_units(v) for v in m])


def vector_str(p):
    return " ".join([val_units(p.x), val_units(p.y), val_units(p.z)])


def quant_vector(v):
    if isinstance(v, Vector):
        return (val_units(v.x), val_units(v.y), val_units(v.z))
    return (val_units(v[0]), val_units(v[1]), val_units(v[2]))


def rich_vector_str(v, colour="white"):
    return "[not bold][%s]%s %s %s" % (colour, *quant_vector(v))


def listify(v):
    if not isinstance(v, (list, tuple)):
        return [v]
    return v
