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
# LDraw object base class

from .geometry import Vector, Matrix, safe_vector
from .helpers import quantize, vector_str, mat_str, rich_vector_str
from .constants import *
from .ldrcolour import LdrColour


class LdrObj:
    def __init__(self, **kwargs):
        self._colour = LdrColour()
        self.matrix = Matrix.identity()
        self._pts = [Vector(0, 0, 0)] * 4
        self.raw = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
            elif k == "point1" or k == "p1" or k == "pos":
                self._pts[0] = safe_vector(v)
            elif k == "point2" or k == "p2":
                self._pts[1] = safe_vector(v)
            elif k == "point3" or k == "p3":
                self._pts[2] = safe_vector(v)
            elif k == "point4" or k == "p4":
                self._pts[3] = safe_vector(v)

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, self.raw)

    def copy(self):
        if isinstance(self, LdrComment):
            new_obj = LdrComment()
        elif isinstance(self, LdrMeta):
            new_obj = LdrMeta()
        elif isinstance(self, LdrLine):
            new_obj = LdrLine()
        elif isinstance(self, LdrTriangle):
            new_obj = LdrTriangle()
        elif isinstance(self, LdrQuad):
            new_obj = LdrQuad()
        elif isinstance(self, LdrPart):
            new_obj = LdrPart()
        for k, v in obj.__dict__.items():
            new_obj.__dict__[k] = v
        return new_obj

    @property
    def is_model_named(self, name):
        if not isinstance(self, LdrPart):
            return False
        if not self.is_model:
            return False
        return self.name == name

    @property
    def model_name(self):
        if not isinstance(self, LdrPart):
            return None
        if not self.is_model:
            return None
        return self.name

    @property
    def part_name(self):
        if not isinstance(self, LdrPart):
            return None
        if not self.is_part:
            return None
        return self.name

    @property
    def is_step_delimiter(self):
        if not isinstance(self, LdrMeta):
            return False
        if self.command.upper() == "STEP":
            return True
        return False

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, code):
        self._colour = LdrColour(code)

    @property
    def pos(self):
        return self._pts[0]

    @pos.setter
    def pos(self, pt):
        self.set_points(pt)

    @property
    def point1(self):
        return self._pts[0]

    @property
    def point2(self):
        return self._pts[1]

    @property
    def point3(self):
        return self._pts[2]

    @property
    def point4(self):
        return self._pts[3]

    @property
    def points(self):
        if isinstance(self, LdrPart):
            return [pt for pt in self._pts[:1]]
        elif isinstance(self, LdrLine):
            return [pt for pt in self._pts[:2]]
        elif isinstance(self, LdrTriangle):
            return [pt for pt in self._pts[:3]]
        elif isinstance(self, LdrQuad):
            return [pt for pt in self._pts[:4]]
        return [pt for pt in self._pts]

    @property
    def points_str(self):
        return " ".join(vector_str(pt) for pt in self.points)

    def set_points(self, pts):
        if isinstance(pts, (list, tuple)):
            if isinstance(pts[0], str):
                vals = pts
            else:
                vals = " ".join([str(pt) for pt in pts])
        elif isinstance(pts, str):
            vals = pts.split()
        vals = [quantize(v) for v in vals]
        num_pts = len(vals) // 3
        new_pts = [vals[i : i + 3] for i in [0, 3, 6, 9][:num_pts]]
        self._pts = [safe_vector(pt) for pt in new_pts]

    def translate(self, offset):
        for pt in self._pts:
            pt += offset

    def translated(self, offset):
        for pt in self._pts:
            pt += offset
        return self

    def transform(self, matrix):
        for pt in self._pts:
            pt = pt * matrix

    def transformed(self, matrix=None, offset=None):
        matrix = matrix if matrix is not None else Matrix.identity()
        offset = offset if offset is not None else Vector(0, 0, 0)
        mt = matrix.transpose()
        self.matrix = matrix * self.matrix
        for pt in self._pts:
            pt = pt * mt
            pt = pt + offset
        return self

    def set_rotation(self, angle):
        self.matrix = Matrix.euler_to_rot_matrix(angle)

    def rotated_by(self, angle):
        rm = Matrix.euler_to_rot_matrix(angle)
        rt = rm.transpose()
        self.matrix = rm * self.matrix
        for pt in self.points:
            pt = pt * rt
        return self

    @staticmethod
    def from_str(s):
        split_line = s.split()
        line_type = int(split_line[0].lstrip())
        if line_type == 0:
            if len(split_line) > 1:
                cmd = split_line[1].upper()
                if cmd in LDR_META_DICT or cmd.startswith("!"):
                    return LdrMeta.from_str(s)
                else:
                    return LdrComment.from_str(s)
        elif line_type == 1:
            return LdrPart.from_str(s)
        elif line_type == 2:
            return LdrLine.from_str(s)
        elif line_type == 3:
            return LdrTriangle.from_str(s)
        elif line_type == 4:
            return LdrQuad.from_str(s)
        return None


class LdrComment(LdrObj):
    def __init__(self, **kwargs):
        self.text = ""
        super().__init__(**kwargs)

    def __str__(self):
        return "0 %s" % (self.text)

    def __rich__(self):
        s = []
        s.append("[bold white]0")
        s.append("[not bold %s]%s" % (RICH_COMMENT_COLOUR, self.text.rstrip()))
        return " ".join(s)

    @staticmethod
    def from_str(s):
        split_line = s.lower().split()
        line_type = int(split_line[0].lstrip())
        if not line_type == 0:
            return None
        obj = LdrComment()
        obj.raw = s
        obj.text = " ".join(split_line[1:])
        return obj


class LdrMeta(LdrObj):
    def __init__(self, **kwargs):
        self.text = ""
        self.command = ""
        self.parameters = None
        self.param_spec = None
        super().__init__(**kwargs)

    def __str__(self):
        return "0 %s %s" % (self.command, self.parameters)

    def __rich__(self):
        s = []
        s.append("[bold white]0")
        if self.command in MPD_META:
            s.append("[bold %s]%s[not bold]" % (RICH_MPD_COLOUR, self.command))
        else:
            s.append("[bold %s]%s[not bold]" % (RICH_META_COLOUR, self.command))
        for p in self.parameters.split():
            if p.lower().endswith(".ldr"):
                s.append("[bold %s]%s[not bold]" % (RICH_FILE_COLOUR, p))
            elif p.lower().endswith(".dat"):
                s.append("[bold %s]%s[not bold]" % (RICH_PART_COLOUR, p))
            else:
                s.append("[%s]%s" % (RICH_PARAM_COLOUR, p))
        return " ".join(s)

    @property
    def is_model_name(self):
        return self.command.upper() == "FILE"

    @property
    def model_name(self):
        if self.is_model_name:
            return self.parameters
        return None

    @staticmethod
    def from_str(s):
        split_line = s.split()
        line_type = int(split_line[0].lstrip())
        if not line_type == 0:
            return None
        obj = LdrMeta()
        obj.raw = s
        obj.text = " ".join(split_line[1:])
        cmd = split_line[1].upper()
        obj.command = cmd
        obj.parameters = " ".join(split_line[2:])
        for k, v in LDR_META_DICT.items():
            if k == obj.command:
                obj.param_spec = v
        return obj


class LdrLine(LdrObj):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return "2 %d %s" % (self.colour, self.points_str)

    def __rich__(self):
        s = []
        s.append("[bold white]2")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.point1, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point2, colour=RICH_COORD2_COLOUR))
        return " ".join(s)

    @staticmethod
    def from_str(s):
        split_line = s.lower().split()
        if not len(split_line) == 8:
            return None
        line_type = int(split_line[0].lstrip())
        if not line_type == 2:
            return None
        obj = LdrLine()
        obj.raw = s
        obj.colour = int(split_line[1])
        obj.set_points(split_line[2:8])
        return obj


class LdrTriangle(LdrObj):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return "3 %d %s" % (self.colour, self.points_str)

    def __rich__(self):
        s = []
        s.append("[bold white]3")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.point1, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point2, colour=RICH_COORD2_COLOUR))
        s.append(rich_vector_str(self.point3, colour=RICH_COORD1_COLOUR))
        return " ".join(s)

    @staticmethod
    def from_str(s):
        split_line = s.lower().split()
        if not len(split_line) == 11:
            return None
        line_type = int(split_line[0].lstrip())
        if not line_type == 3:
            return None
        obj = LdrTriangle()
        obj.raw = s
        obj.colour = int(split_line[1])
        obj.set_points(split_line[2:11])
        return obj


class LdrQuad(LdrObj):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return "4 %d %s" % (self.colour, self.points_str)

    def __rich__(self):
        s = []
        s.append("[bold white]4")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.point1, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point2, colour=RICH_COORD2_COLOUR))
        s.append(rich_vector_str(self.point3, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point4, colour=RICH_COORD2_COLOUR))
        return " ".join(s)

    @staticmethod
    def from_str(s):
        split_line = s.lower().split()
        if not len(split_line) == 14:
            return None
        line_type = int(split_line[0].lstrip())
        if not line_type == 4:
            return None
        obj = LdrQuad()
        obj.raw = s
        obj.colour = int(split_line[1])
        obj.set_points(split_line[2:14])
        return obj


class LdrPart(LdrObj):
    def __init__(self, **kwargs):
        self.name = None
        super().__init__(**kwargs)

    def __str__(self):
        return "1 %d %s %s %s" % (
            self.colour.code,
            vector_str(self.pos),
            mat_str(self.matrix.values),
            self.name,
        )

    def __rich__(self):
        s = []
        s.append("[bold white]1")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.pos, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.matrix.rows[0], colour=RICH_COORD2_COLOUR))
        s.append(rich_vector_str(self.matrix.rows[1], colour=RICH_COORD3_COLOUR))
        s.append(rich_vector_str(self.matrix.rows[2], colour=RICH_COORD2_COLOUR))
        if self.is_part:
            s.append("[%s]%s" % (RICH_PART_COLOUR, self.name))
        else:
            s.append("[%s]%s" % (RICH_FILE_COLOUR, self.name))
        return " ".join(s)

    @property
    def is_part(self):
        return self.name.lower().endswith(".dat")

    @property
    def is_model(self):
        return any(self.name.lower().endswith(x) for x in (".ldr", ".mpd"))

    @staticmethod
    def from_str(s):
        split_line = s.split()
        if not len(split_line) >= 15:
            return None
        line_type = int(split_line[0].lstrip())
        if not line_type == 1:
            return None
        p = LdrPart()
        p.raw = s
        p.colour = int(split_line[1])
        p.set_points(split_line[2:5])
        p.matrix = Matrix(
            [
                [
                    quantize(split_line[5]),
                    quantize(split_line[6]),
                    quantize(split_line[7]),
                ],
                [
                    quantize(split_line[8]),
                    quantize(split_line[9]),
                    quantize(split_line[10]),
                ],
                [
                    quantize(split_line[11]),
                    quantize(split_line[12]),
                    quantize(split_line[13]),
                ],
            ]
        )
        pname = " ".join(split_line[14:])
        p.name = pname
        return p
