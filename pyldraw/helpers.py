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


class MetaValueParser:
    """Parses arbritrarily specified values and flags contained in a Meta command."""

    def __init__(self, specs, vals=None, **kwargs):
        self.specs = specs
        self.vals = vals
        self._flags = None
        self._keyvals = None

    def __str__(self):
        s = []
        s.append("MetaValueParser:")
        s.append("  Specs: %s" % (self.specs))
        s.append("  Flags: %s" % (self.flags))
        s.append("  Key values: %s" % (self.keyvals))
        s.append("  Labeled values:")
        for e in self.keyvals:
            if "label" in e:
                opt = "(optional)" if e["delimiter"] == "[" else ""
                s.append("    %s: %s %s" % (e["label"], e["keys"], opt))
        s.append("  Unlabeled values:")
        for e in self.keyvals:
            if "label" not in e:
                opt = "(optional)" if e["delimiter"] == "[" else ""
                s.append("    %s %s" % (e["keys"], opt))
        return "\n".join(s)

    @property
    def labeled_vals_labels(self):
        """Returns a list of labels associated with labelled keyvals"""
        return [e["label"] for e in self.keyvals if "label" in e]

    @property
    def unlabeled_vals(self):
        """Returns a list of keys associated with unlabelled keyvals"""
        return [e["keys"][0] for e in self.keyvals if "label" not in e]

    @property
    def flags(self):
        if self._flags is None:
            """Extracts expected flag tokens from provided specifications."""
            start_count = self.specs.count("(")
            end_count = self.specs.count(")")
            if start_count == 0 or end_count == 0 or not start_count == end_count:
                return []
            token_groups = []
            token_group = []
            capture_depth = 0
            for c in self.specs:
                if c == "(":
                    capture_depth += 1
                elif c == ")" and capture_depth > 0:
                    capture_depth -= 1
                    if capture_depth == 0:
                        tg = "".join(token_group).strip()
                        tg = tg.replace("|", "")
                        token_groups.extend(tg.split())
                        token_group = []
                else:
                    if capture_depth > 0:
                        token_group.append(c)
            self._flags = token_groups
        return self._flags

    @property
    def keyvals(self):
        if self._keyvals is None:
            self._keyvals = self._extract_vals()
        return self._keyvals

    def labelled_keyval(self, label):
        if label is not None:
            for e in self.keyvals:
                if "label" in e:
                    if label == e["label"]:
                        return e["keys"]
        return None

    def _extract_vals(self):
        """Extracts values which are delimited by <> or other symbol pair.
        Values can be named with a label prefix token as the first item
        followed by one or more value keys.
        <LABEL key1 key2 ...>
        Alternatively, a value can simply be unlabeled and specified with a key:
        <key>
        """
        captured = False
        keyvals = []
        val_cap = []
        for c in self.specs:
            if (c == "<" or c == "[") and not captured:
                start_delimit = c
                val_cap = []
                captured = True
            elif (c == ">" or c == "]") and captured:
                val_cap = "".join(val_cap)
                vs = val_cap.split()
                if len(vs) >= 2:
                    keyvals.append(
                        {
                            "delimiter": start_delimit,
                            "label": vs[0],
                            "keys": [v for v in vs[1:]],
                        }
                    )
                elif len(vs) == 1:
                    keyvals.append({"delimiter": start_delimit, "keys": [vs[0]]})
                captured = False
            elif captured:
                val_cap.append(c)
        return keyvals

    def matched_flags(self, vals=None):
        vals = vals if vals is not None else self.vals
        matched = []
        for v in vals.split():
            if v in self.flags:
                matched.append(v)
        return matched

    def matched_values(self, vals=None):
        vals = vals if vals is not None else self.vals
        matched = []
        # strip flags
        val_stack = [v for v in vals.split() if v not in self.flags]
        # extract labeled parameters and strip
        new_stack = []
        idx = 0
        for i, v in enumerate(val_stack):
            if idx >= len(val_stack):
                break
            vp = val_stack[idx]
            if vp in self.labeled_vals_labels:
                keys = self.labelled_keyval(vp)
                for offset, key in enumerate(keys):
                    matched.append({key: val_stack[idx + 1 + offset]})
                idx += len(keys) + 1
            else:
                new_stack.append(vp)
                idx += 1
        extra = []
        remaining = self.unlabeled_vals
        # assign remaining values to unlabelled key values
        # and if more values still remain, assign to "extra"
        for i, e in enumerate(new_stack):
            if i < len(remaining):
                key = remaining[i]
                matched.append({key: e})
            else:
                extra.append(e)
        if len(extra) > 0:
            matched.append({"extra": extra})
        return matched

    @property
    def param_dict(self):
        flags = self.matched_flags()
        vals = self.matched_values()
        pd = {}
        pd["flags"] = flags
        for v in vals:
            for k, e in v.items():
                pd[k] = e
        return pd
