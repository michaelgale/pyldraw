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
# LdrColour class

import slugify

from .constants import *


class LdrColour:

    """LDraw colour helper class.  This class can be used to store a
    colour and to perform conversions among:
      LDraw colour code, Bricklink colour code, colour name,
      RGB floating point, RGB hex"""

    __slots__ = ("_code", "r", "g", "b")

    def __init__(self, colour=None, red=None, green=None, blue=None, **kwargs):
        self._code = LDR_DEF_COLOUR
        self.r = 0.0
        self.g = 0.0
        self.b = 0.0
        if colour is not None:
            if isinstance(colour, int):
                self.code = colour
            elif isinstance(colour, LdrColour):
                self.code = colour.code
            elif isinstance(colour, (list, tuple)):
                self.set_rgb(colour)
            elif isinstance(colour, str):
                if colour in LDR_CODE_FROM_NAME:
                    self.code = LDR_CODE_FROM_NAME[colour]
                else:
                    c = LdrColour.code_from_hex(colour)
                    if c is not None:
                        self.code = c
        else:
            if red is not None and green is not None and blue is not None:
                self.set_rgb(red, green, blue)

    def __repr__(self):
        return "%s(%s, r: %.2f g: %.2f b: %.2f, %s)" % (
            self.__class__.__name__,
            self.code,
            self.red,
            self.green,
            self.blue,
            self.hex_code,
        )

    def __str__(self):
        return str(self.code)

    def __rich__(self):
        if self.code == 16 or self.code == 24:
            return "[bold navajo_white1]%s" % (self.code)
        if self.code == "0":
            return "[bold]0"
        return "[%s reverse]%s[not reverse]" % (self.hex_code, self.code)

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code):
        self._code = code
        self.set_rgb(LdrColour.code_to_rgb(code))

    @property
    def red(self):
        return self.r

    @property
    def green(self):
        return self.g

    @property
    def blue(self):
        return self.b

    @property
    def name(self):
        if self.code in LDR_COLOUR_NAME:
            return LDR_COLOUR_NAME[self.code]
        return None

    @property
    def name_slug(self):
        return slugify.slugify("-".join(self.name.split()))

    @property
    def hex_code(self):
        return "#%02X%02X%02X" % (
            int(self.r * 255.0),
            int(self.g * 255.0),
            int(self.b * 255.0),
        )

    def set_rgb(self, r, g=None, b=None):
        if r is None:
            return
        if isinstance(r, (tuple, list)):
            self.r, self.g, self.b = r[0], r[1], r[2]
        else:
            self.r, self.g, self.b = r, g, b

    @staticmethod
    def code_to_rgb(code):
        if code in LDR_COLOUR_HEX:
            rgb = LDR_COLOUR_HEX[code]
            [rd, gd, bd] = tuple(int(rgb[i : i + 2], 16) for i in (0, 2, 4))
            r = float(rd) / 255.0
            g = float(gd) / 255.0
            b = float(bd) / 255.0
            return r, g, b
        return None

    @staticmethod
    def code_from_hex(val):
        val = val.replace("#", "")
        for k, v in LDR_COLOUR_HEX.items():
            if v.lower() == val.lower():
                return k
        return None
