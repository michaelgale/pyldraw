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

import math
import slugify

from .constants import *
from .support.imgutils import ImageMixin


class LdrColour:

    """LDraw colour helper class.  This class can be used to store a
    colour and to perform conversions among:
      LDraw colour code, Bricklink colour code, colour name,
      RGB floating point, RGB hex"""

    def __init__(self, colour=None, red=None, green=None, blue=None, **kwargs):
        self._code = LDR_DEF_COLOUR
        self.r = 0.0
        self.g = 0.0
        self.b = 0.0
        self.alpha = None
        self.luminance = None
        self.label = None
        self.material = None
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
                        self.set_with_hex(colour)
        else:
            if red is not None and green is not None and blue is not None:
                self.set_rgb(red, green, blue)
        self.edge = "#05131D" if not self.code == 0 else "#FFFFFF"
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

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
        if self.code == 16 or self.code == 24 or self.code not in LDR_COLOUR_NAME:
            return "[bold navajo_white1]%s" % (self.code)
        if self.code == "0":
            return "[bold]0"
        return "[%s reverse]%s[not reverse]" % (self.hex_code, self.code)

    def rich_name(self):
        if any(x in self.name for x in ("Black", "Brown", "Dark")):
            return "[white]%3d[/] [white on %s]%-20s[/] [white]%6s[/]" % (
                self.code,
                self.hex_code,
                self.name,
                self.hex_code,
            )
        else:
            return "[white]%3d[/] [black on %s]%-20s[/] [white]%6s[/]" % (
                self.code,
                self.hex_code,
                self.name,
                self.hex_code,
            )

    def __eq__(self, other):
        if not isinstance(other, LdrColour):
            return False
        if self.code == other.code:
            return True
        if (
            self.red == other.red
            and self.green == other.green
            and self.blue == other.blue
        ):
            return True
        return False

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code):
        self._code = code
        self.set_rgb(LdrColour.code_to_rgb(code))

    @property
    def red(self):
        """Red channel value between 0.0 and 1.0"""
        return self.r

    @property
    def green(self):
        """Green channel value between 0.0 and 1.0"""
        return self.g

    @property
    def blue(self):
        """Blue channel value between 0.0 and 1.0"""
        return self.b

    @property
    def name(self):
        """LDraw colour name"""
        if self.code in LDR_COLOUR_NAME:
            return LDR_COLOUR_NAME[self.code]
        return self.label

    @property
    def name_slug(self):
        """Slugified LDraw colour name"""
        return slugify.slugify("-".join(self.name.split()))

    @property
    def compact_name(self):
        """Compact/abbreviated LDraw colour name"""
        name = self.name
        replacements = [
            "Bright Br",
            "Light Lt",
            "Dark Dk",
            "Medium Med",
            "Bluish Bl",
            "Reddish Red",
            "Chrome Chr",
            "Yellowish Ylw",
        ]
        for replacement in replacements:
            rs = replacement.split()
            name = name.replace(rs[0], rs[1])
        return name

    @property
    def hex_code(self):
        """Hexadecimal colour code string"""
        return "#%02X%02X%02X" % (
            int(self.r * 255.0),
            int(self.g * 255.0),
            int(self.b * 255.0),
        )

    @property
    def bgr(self):
        """Return a tuple of (blue, green, red) as int8 values."""
        return (int(self.b * 255), int(self.g * 255), int(self.r * 255))

    @property
    def rgbint(self):
        """Return a tuple of (red, green, blue) as int8 values."""
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255))

    @property
    def hsv(self):
        """Return a tuple of (hue, saturation, brightness) as int8 values."""
        return ImageMixin.bgr2hsv(self.bgr)

    @property
    def hue(self):
        """Hue value as int8 range 0 ~ 180"""
        return int(self.hsv[0])

    @property
    def saturation(self):
        """Saturation value as int8 range 0 ~ 255"""
        return int(self.hsv[1])

    @property
    def brightness(self):
        """Brightness value as int8 range 0 ~ 255"""
        return int(self.hsv[2])

    @property
    def high_contrast_complement(self):
        """Return a high contrast complement colour value, i.e. black or white depending on this colour's intensity"""
        level = self.r * self.r + self.g * self.g + self.b * self.b
        level = math.sqrt(level)
        if level < 1.2:
            return (1.0, 1.0, 1.0)
        return (0.0, 0.0, 0.0)

    @property
    def rgb(self):
        """Return a tuple of (red, green, blue) as float values 0.0 ~ 1.0"""
        return self.r, self.g, self.b

    def set_rgb(self, r, g=None, b=None):
        """Set red, green, and blue channel values."""
        if r is None:
            return
        if isinstance(r, (tuple, list)):
            self.r, self.g, self.b = r[0], r[1], r[2]
        else:
            self.r, self.g, self.b = r, g, b
        if any((x > 1.0 for x in (self.r, self.g, self.b))):
            self.r = self.r / 255
            self.g = self.g / 255
            self.b = self.b / 255

    def set_with_hex(self, val):
        """Set red, green, and blue channel values with a hex code."""
        rgb = val.replace("#", "")
        [rd, gd, bd] = tuple(int(rgb[i : i + 2], 16) for i in (0, 2, 4))
        self.r = float(rd) / 255.0
        self.g = float(gd) / 255.0
        self.b = float(bd) / 255.0

    @staticmethod
    def code_to_rgb(code):
        if code in LDR_COLOUR_HEX:
            rgb = LDR_COLOUR_HEX[code]
        elif isinstance(code, str):
            rgb = code.replace("#", "")
        else:
            return None
        [rd, gd, bd] = tuple(int(rgb[i : i + 2], 16) for i in (0, 2, 4))
        r = float(rd) / 255.0
        g = float(gd) / 255.0
        b = float(bd) / 255.0
        return r, g, b

    @staticmethod
    def code_from_hex(val):
        val = val.replace("#", "")
        for k, v in LDR_COLOUR_HEX.items():
            if v.lower() == val.lower():
                return k
        return None

    @staticmethod
    def from_meta(obj):
        from .ldrobj import LdrMeta

        """Make a LdrColour instance from a LdrMeta object defined with a parsed LDraw !COLOUR meta"""
        if not isinstance(obj, LdrMeta):
            raise ValueError(
                "Cannot make a LdrColour instance with meta object of type %s"
                % (type(obj))
            )
        c = LdrColour()
        p = obj.parameters
        c.code = int(p["code"])
        c.set_with_hex(p["value"])
        c.edge = p["edge"]
        if "alpha" in p:
            c.alpha = p["alpha"]
        if "luminance" in p:
            c.alpha = p["luminance"]
        c.label = p["name"].replace("_", " ")
        if "flags" in p:
            if len(p["flags"]) > 0:
                c.material = p["flags"][0]
        return c

    @staticmethod
    def CLEAR_MASK():
        """LdrColour preset with a colour used for masking clear"""
        c = LdrColour(CLEAR_MASK_CODE, alpha=2, edge=CLEAR_MASK_COLOUR)
        c.set_rgb(LdrColour.code_to_rgb(CLEAR_MASK_COLOUR))
        return c

    @staticmethod
    def OPAQUE_MASK():
        """LdrColour preset with a colour used for masking opaque"""
        c = LdrColour(OPAQUE_MASK_CODE, edge=OPAQUE_MASK_COLOUR)
        c.set_rgb(LdrColour.code_to_rgb(OPAQUE_MASK_COLOUR))
        return c

    @staticmethod
    def ADDED_MASK():
        """LdrColour preset with a colour used for masking parts added to a step"""
        c = LdrColour(ADDED_MASK_CODE, luminance=100, edge=ADDED_MASK_COLOUR)
        c.set_rgb(LdrColour.code_to_rgb(ADDED_MASK_COLOUR))
        return c

    @staticmethod
    def ARROW_RED():
        """LdrColour preset for red arrow shapes"""
        c = LdrColour(804, luminance=220, edge=ARROW_RED_COLOUR)
        c.set_rgb(LdrColour.code_to_rgb(ARROW_RED_COLOUR))
        return c

    @staticmethod
    def ARROW_BLUE():
        """LdrColour preset for blue arrow shapes"""
        c = LdrColour(801, luminance=220, edge=ARROW_BLUE_COLOUR)
        c.set_rgb(LdrColour.code_to_rgb(ARROW_BLUE_COLOUR))
        return c

    @staticmethod
    def ARROW_GREEN():
        """LdrColour preset for green arrow shapes"""
        c = LdrColour(802, luminance=220, edge=ARROW_GREEN_COLOUR)
        c.set_rgb(LdrColour.code_to_rgb(ARROW_GREEN_COLOUR))
        return c
