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

import os
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


def strip_part_ext(name):
    for e in (".dat", ".DAT", ".ldr", ".LDR", ".mpd", ".MPD"):
        name = name.replace(e, "")
    return name


def normalize_filename(filename, filepath):
    """Ensures filename is formatted to include the path whether or not it is included."""
    if filepath is not None:
        path, _ = os.path.split(filename)
        oppath = os.path.normpath(filepath)
        if not oppath in path:
            fn = os.path.normpath(filepath + os.sep + filename)
        else:
            fn = filename
    else:
        fn = os.path.normpath(filename)
    return fn


def strip_punc(s, chars=None):
    char_list = chars if chars is not None else "< > ( ) | , [ ]"
    for c in char_list.split():
        s = s.replace(c, "")
    return s


def strip_flag_tokens(specs, vals):
    """Strips tokens from vals which are specified in specs.
    flags are enclosed in parentheses () and separated by pipes |
    new specs and vals strings are returned with tokens extracted."""

    start_count = specs.count("(")
    end_count = specs.count(")")
    if start_count == 0 or end_count == 0 or not start_count == end_count:
        return specs, vals, []
    token_groups = []
    token_group = []
    capture_depth = 0
    for c in specs:
        if c == "(":
            capture_depth += 1
        elif c == ")" and capture_depth > 0:
            capture_depth -= 1
            if capture_depth == 0:
                token_groups.append("".join(token_group))
                token_group = []
        else:
            if capture_depth > 0:
                token_group.append(c)

    tokens = []
    for token_group in token_groups:
        tg = strip_punc(token_group)
        ts = tg.split()
        for t in ts:
            tokens.append(t.lstrip().rstrip())

    new_specs = strip_punc(specs, chars="( ) |")
    ns = new_specs.split()
    new_specs = []
    for e in ns:
        if not e in tokens:
            new_specs.append(e)
    new_specs = " ".join(new_specs)

    found_tokens = []
    for v in vals.split():
        if v in tokens:
            found_tokens.append(v)
    vs = vals.split()
    nv = []
    for v in vs:
        if v not in found_tokens:
            nv.append(v)
    vals = " ".join(nv)
    return new_specs, vals, found_tokens


def parse_params(specs, vals):
    """Parse string describing parameters.
    named values are contained in angle brackets: <value>
    optional named values are contained in square brackets [value]
    named flags are contained in parentheses: (FLAG | FLAG2)"""
    param_dict = {}

    specs, vals, tokens = strip_flag_tokens(specs, vals)
    param_dict["flags"] = tokens
    sp = specs.split()
    spec_count = len(sp)
    spec_idx = 0
    for i, val in enumerate(vals.split()):
        if spec_idx < spec_count:
            if sp[spec_idx].startswith("<"):
                key = strip_punc(sp[spec_idx])
                param_dict[key] = val
                spec_idx += 1
                continue
            elif sp[spec_idx].startswith("["):
                key = strip_punc(sp[spec_idx])
                param_dict[key] = val
                spec_idx += 1
                continue
        if "extra" in param_dict:
            param_dict["extra"].append(val)
        else:
            param_dict["extra"] = [val]

    return param_dict
