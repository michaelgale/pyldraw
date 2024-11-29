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

import hashlib

from .geometry import Vector, Matrix, safe_vector, BoundBox
from .helpers import (
    quantize,
    vector_str,
    mat_str,
    rich_vector_str,
    strip_part_ext,
    MetaValueParser,
    listify,
)
from pyldraw import *


class LdrObj:
    """LdrObj is a container class for a line of parsed LDraw text.
    It contains the raw text of the line as well as abstracted attributes
    about the LDraw object's colour, geometry, and other data applicable
    to its type."""

    def __init__(self, **kwargs):
        self._colour = LdrColour()
        self.matrix = Matrix.identity()
        self._pts = [Vector(0, 0, 0)] * 4
        self.raw = None
        self.path = None
        self.tags = None
        self._sha1_hash = None
        for k, v in kwargs.items():
            if k == "colour":
                self._colour = LdrColour(v)
            elif k == "aspect":
                self.set_rotation(v)
            elif k == "point1" or k == "p1" or k == "pos":
                self._pts[0] = safe_vector(v)
            elif k == "point2" or k == "p2":
                self._pts[1] = safe_vector(v)
            elif k == "point3" or k == "p3":
                self._pts[2] = safe_vector(v)
            elif k == "point4" or k == "p4":
                self._pts[3] = safe_vector(v)
            elif k in self.__dict__:
                self.__dict__[k] = v

    def __repr__(self) -> str:
        return "%s(%s: %s)" % (self.__class__.__name__, self.path, str(self))

    def verbose(self):
        s = []
        s.append("%s: " % (self.path))
        if len(str(self)) > 60:
            s.append(str(self)[:40])
            s.append(" ... ")
            last = len(str(self)) - 40
            last = min(last, 16)
            s.append(str(self)[-last:])
        else:
            s.append(str(self))
        if self.tags is not None:
            s.append(" (")
            s.append(" ".join(["%s" % (t) for t in self.tags]))
            s.append(")")
        return "".join(s)

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
        else:
            new_obj = LdrObj()
        for k, v in self.__dict__.items():
            new_obj.__dict__[k] = v
        return new_obj

    @property
    def sha1_hash(self):
        if self._sha1_hash is None:
            hk = hashlib.sha1()
            hk.update(bytes(str(self), encoding="utf8"))
            self._sha1_hash = hk.hexdigest()
        return self._sha1_hash

    @property
    def has_start_tag_capture(self):
        if isinstance(self, LdrMeta):
            if self.command.upper() == "!PY TAG BEGIN":
                return True
        return False

    @property
    def has_end_tag_capture(self):
        if isinstance(self, LdrMeta):
            if self.command.upper() == "!PY TAG END":
                return True
        return False

    @property
    def has_start_capture_meta(self):
        raw_text = self.raw.upper()
        if isinstance(self, LdrMeta):
            if "BEGIN" in raw_text:
                return True
            else:
                for e in START_META:
                    if all(s in raw_text for s in e.split()):
                        return True
        return False

    @property
    def has_end_capture_meta(self):
        raw_text = self.raw.upper()
        if isinstance(self, LdrMeta):
            if "END" in raw_text:
                return True
            else:
                for e in END_META:
                    if all(s in raw_text for s in e.split()):
                        return True
        return False

    @property
    def is_primitive(self):
        return isinstance(self, (LdrLine, LdrTriangle, LdrQuad))

    @property
    def is_drawable(self):
        return isinstance(self, (LdrPart, LdrLine, LdrTriangle, LdrQuad))

    @property
    def model_part_name(self):
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

    def matched_path(self, path, exact=False):
        if exact:
            return path == self.path
        if self.path is not None:
            return path in self.path
        return False

    def matched_name(self, name):
        if not isinstance(self, LdrPart):
            return False
        name_ext = strip_part_ext(name)
        my_name_ext = strip_part_ext(self.name)
        return name_ext == my_name_ext

    @property
    def part_key(self):
        if not isinstance(self, LdrPart):
            return None
        name = strip_part_ext(self.name)
        if self.is_part:
            return "%s-%d" % (name, self.colour.code)
        return name

    @property
    def is_step_delimiter(self):
        if not isinstance(self, LdrMeta):
            return False
        if self.command in DELIMITER_META:
            return True
        return False

    def has_tag(self, tags):
        if self.tags is None:
            return False
        tags = listify(tags)
        return all(t in self.tags for t in tags)

    def renamed(self, name):
        if not isinstance(self, LdrPart):
            return self
        obj = self.copy()
        obj.name = name
        return obj

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

    @point1.setter
    def point1(self, pt):
        self._pts[0] = safe_vector(pt)

    @property
    def point2(self):
        return self._pts[1]

    @point2.setter
    def point2(self, pt):
        self._pts[1] = safe_vector(pt)

    @property
    def point3(self):
        return self._pts[2]

    @point3.setter
    def point3(self, pt):
        self._pts[2] = safe_vector(pt)

    @property
    def point4(self):
        return self._pts[3]

    @point4.setter
    def point4(self, pt):
        self._pts[3] = safe_vector(pt)

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
        return []

    @property
    def bound_box(self):
        return BoundBox.from_pts(self.points)

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
        self._pts = [pt + Vector(offset) for pt in self._pts]

    def translated(self, offset):
        obj = self.copy()
        obj._pts = [pt + Vector(offset) for pt in obj._pts]
        return obj

    def moved_to(self, offset):
        obj = self.copy()
        obj._pts = [Vector(offset) for _ in obj._pts]
        return obj

    def transform(self, matrix):
        for pt in self._pts:
            pt = pt * matrix

    def transformed(self, matrix=None, offset=None):
        obj = self.copy()
        matrix = matrix if matrix is not None else Matrix.identity()
        offset = Vector(offset) if offset is not None else Vector(0, 0, 0)
        mt = matrix.transpose()
        obj.matrix = matrix * obj.matrix
        obj._pts = [pt * mt for pt in obj.points]
        obj._pts = [pt + offset for pt in obj.points]
        return obj

    def set_rotation(self, angle):
        self.matrix = Matrix.euler_to_rot_matrix(angle)

    def rotated_by(self, angle):
        obj = self.copy()
        rm = Matrix.euler_to_rot_matrix(angle)
        rt = rm.transpose()
        obj.matrix = rm * obj.matrix
        obj._pts = [pt * rt for pt in obj.points]
        return obj

    def rotated_by_matrix(self, matrix):
        obj = self.copy()
        rt = matrix.transpose()
        obj.matrix = matrix * obj.matrix
        obj._pts = [pt * rt for pt in obj.points]
        return obj

    def rotation_removed(self, aspect):
        obj = self.copy()
        a = Vector(aspect)
        if abs(a.x) > 0:
            obj = obj.rotated_by(Vector(-a.x, 0, 0))
        if abs(a.y) > 0:
            obj = obj.rotated_by(Vector(0, -a.y, 0))
        if abs(a.z) > 0:
            obj = obj.rotated_by(Vector(0, 0, -a.z))
        return obj

    def new_path(self, path):
        obj = self.copy()
        obj.path = path
        return obj

    def new_colour(self, colour):
        obj = self.copy()
        obj._colour = LdrColour(colour)
        return obj

    @staticmethod
    def from_str(s):
        if not isinstance(s, str):
            raise ValueError(
                "Cannot make a LdrObj instance. Expecting string, but got object of type %s"
                % (type(s))
            )

        if s is None:
            return None
        if len(s) < 2:
            return None
        split_line = s.split()
        line_type = int(split_line[0].lstrip())
        if line_type == 0:
            if len(split_line) > 1:
                for k, _ in LDR_META_DICT.items():
                    if k in s:
                        ks = k.split()
                        first = ks[0] if len(ks) > 1 else k
                        if split_line[1].startswith(first):
                            return LdrMeta.from_str(s)
                if split_line[1].startswith("!"):
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

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

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
        self.values = ""
        self.parameters = None
        self.param_spec = None
        super().__init__(**kwargs)

    def __str__(self):
        return "0 %s %s" % (self.command, self.values)

    def __rich__(self):
        s = []
        s.append("[bold white]0")
        if self.command in MPD_META:
            s.append("[bold %s]%s[not bold]" % (RICH_MPD_COLOUR, self.command))
        else:
            s.append("[bold %s]%s[not bold]" % (RICH_META_COLOUR, self.command))
        for p in self.values.split():
            if p.lower().endswith(".ldr"):
                s.append("[bold %s]%s[not bold]" % (RICH_FILE_COLOUR, p))
            elif p.lower().endswith(".dat"):
                s.append("[bold %s]%s[not bold]" % (RICH_PART_COLOUR, p))
            else:
                s.append("[%s]%s" % (RICH_PARAM_COLOUR, p))
        return " ".join(s)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

    @property
    def is_model_name(self):
        return self.command.upper() == "FILE"

    @property
    def model_name(self):
        if self.is_model_name:
            return self.values
        return None

    @property
    def start_of_model(self):
        return self.command.upper() == "FILE"

    @property
    def end_of_model(self):
        return self.command.upper() == "NOFILE"

    @property
    def is_delimiter(self):
        return self.start_of_model or self.end_of_model or self.is_step_delimiter

    @property
    def rotation_absolute(self):
        if self.command.upper() in ("ROTSTEP", "!PY ROT"):
            if "ABS" in self.parameters["flags"]:
                return Vector.from_dict(self.parameters)
        return None

    @property
    def rotation_relative(self):
        if self.command.upper() in ("ROTSTEP", "!PY ROT"):
            if "REL" in self.parameters["flags"]:
                return Vector.from_dict(self.parameters)
            elif "FLIPX" in self.parameters["flags"]:
                return Vector(180, 0, 0)
            elif "FLIPY" in self.parameters["flags"]:
                return Vector(0, 180, 0)
            elif "FLIPZ" in self.parameters["flags"]:
                return Vector(0, 0, 180)
        return None

    @property
    def rotation_end(self):
        if self.command.upper() == "ROTSTEP":
            if "END" in self.parameters["flags"]:
                return True
        return None

    @property
    def new_scale(self):
        if self.command == "!PY SCALE":
            if "scale" in self.parameters:
                return float(self.parameters["scale"])
        return None

    @property
    def column_break(self):
        if self.command.upper() == "!PY COL_BREAK":
            return True
        return None

    @property
    def page_break(self):
        if self.command.upper() == "!PY PAGE_BREAK":
            return True
        return None

    @property
    def hide_pli(self):
        if self.command.upper() == "!PY HIDE_PLI":
            return True
        return None

    @property
    def hide_fullscale(self):
        if self.command.upper() == "!PY HIDE_FULLSCALE":
            return True
        return None

    @property
    def hide_preview(self):
        if self.command.upper() == "!PY HIDE_PREVIEW":
            return True
        return None

    @property
    def hide_rotation_icon(self):
        if self.command.upper() == "!PY HIDE_ROTICON":
            return True
        return None

    @property
    def hide_page_num(self):
        if self.command.upper() == "!PY HIDE_PAGE_NUM":
            return True
        return None

    @property
    def show_page_num(self):
        if self.command.upper() == "!PY SHOW_PAGE_NUM":
            return True
        return None

    @property
    def new_page_num(self):
        if self.command == "!PY NEW_PAGE_NUM":
            if "number" in self.parameters:
                return int(self.parameters["number"])
        return None

    @property
    def columns(self):
        if self.command == "!PY COLUMNS":
            if "columns" in self.parameters:
                return int(self.parameters["columns"])
        return None

    @property
    def no_callout(self):
        if self.command.upper() == "!PY NO_CALLOUT":
            return True
        return None

    @property
    def is_arrow_capture(self):
        if self.command.upper() == "!PY ARROW BEGIN":
            return True
        return None

    @property
    def is_hide_part_capture(self):
        if self.command.upper() == "!PY HIDE_PARTS BEGIN":
            return True
        return None

    @property
    def is_hide_pli_capture(self):
        if self.command.upper() == "!PY HIDE_PLI BEGIN":
            return True
        return None

    @staticmethod
    def from_str(s):
        """Returns a LdrMeta object by parsing a string representation of LDraw meta line 0"""
        if not isinstance(s, str):
            raise ValueError(
                "Cannot make a LdrMeta instance. Expecting string, but got object of type %s"
                % (type(s))
            )
        split_line = s.split()
        line_type = int(split_line[0].lstrip())
        if not line_type == 0:
            return None
        obj = LdrMeta()
        obj.raw = s
        obj.text = " ".join(split_line[1:])
        for k, v in LDR_META_DICT.items():
            if obj.text.startswith(k):
                obj.command = k
                obj.param_spec = v
                obj.values = obj.text.replace(k, "").lstrip()
                mp = MetaValueParser(v, vals=obj.values)
                obj.parameters = mp.param_dict
                return obj
        return obj

    @staticmethod
    def from_colour(colour):
        """Returns a LdrMeta object representing a !COLOUR meta definition of a LdrColour object."""
        if not isinstance(colour, LdrColour):
            raise ValueError(
                "Cannot make a LdrMeta instance. Expecting LdrColour, but got object of type %s"
                % (type(colour))
            )
        name = colour.name if colour.name is not None else "Colour_%d" % (colour.code)
        edge = colour.edge if colour.edge is not None else colour.hex_code
        s = []
        s.append("0 !COLOUR %s" % (name.replace(" ", "_")))
        s.append("CODE %d" % (colour.code))
        s.append("VALUE %s" % (colour.hex_code))
        s.append("EDGE %s" % (edge))
        if colour.alpha is not None:
            s.append("ALPHA %d" % (colour.alpha))
        if colour.luminance is not None:
            s.append("LUMINANCE %d" % (colour.luminance))
        if colour.material is not None:
            s.append(colour.material.upper())
        s = " ".join(s)
        return LdrMeta.from_str(s)


class LdrLine(LdrObj):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return "2 %d %s" % (self.colour.code, self.points_str)

    def __rich__(self):
        s = []
        s.append("[bold white]2")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.point1, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point2, colour=RICH_COORD2_COLOUR))
        return " ".join(s)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

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
        return "3 %d %s" % (self.colour.code, self.points_str)

    def __rich__(self):
        s = []
        s.append("[bold white]3")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.point1, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point2, colour=RICH_COORD2_COLOUR))
        s.append(rich_vector_str(self.point3, colour=RICH_COORD1_COLOUR))
        return " ".join(s)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

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
        return "4 %d %s" % (self.colour.code, self.points_str)

    def __rich__(self):
        s = []
        s.append("[bold white]4")
        s.append(self.colour.__rich__())
        s.append(rich_vector_str(self.point1, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point2, colour=RICH_COORD2_COLOUR))
        s.append(rich_vector_str(self.point3, colour=RICH_COORD1_COLOUR))
        s.append(rich_vector_str(self.point4, colour=RICH_COORD2_COLOUR))
        return " ".join(s)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

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

    @staticmethod
    def from_size(length, width):
        """Makes an LdrQuad object using with a length and width specification.
        length and width are Vector objects with only either the x, y, or z value set.
        The length will specify +/- length/2 in its axis direction.
        The width will specify +/- width/2 in its axis direction"""
        obj = LdrQuad()
        l2 = abs(length) / 2
        w2 = abs(width) / 2
        dl = length.norm()
        dw = width.norm()
        obj.point1 = -l2 * dl - w2 * dw
        obj.point2 = l2 * dl - w2 * dw
        obj.point3 = l2 * dl + w2 * dw
        obj.point4 = -l2 * dl + w2 * dw
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

    def __hash__(self):
        return hash(str(self.raw), str(self.path))

    def __eq__(self, other):
        return self.is_identical(other)

    def __ne__(self, other):
        return not self.is_identical(other)

    @property
    def sha1_hash(self):
        if self._sha1_hash is None:
            hk = hashlib.sha1()
            hk.update(bytes(str(self.raw), encoding="utf8"))
            hk.update(bytes(str("%s" % (self.path)), encoding="utf8"))
            self._sha1_hash = hk.hexdigest()
        return self._sha1_hash

    @property
    def is_part(self):
        return self.name.lower().endswith(".dat")

    @property
    def description(self):
        """Looks up the part description from the LDraw library"""
        if self.is_part:
            return part_description(self.name)
        return None

    @property
    def is_model(self):
        return any(self.name.lower().endswith(x) for x in (".ldr", ".mpd"))

    def is_same_element(self, other):
        if not isinstance(other, LdrPart):
            return False
        return self.name == other.name and self.colour.code == other.colour.code

    def is_identical(self, other):
        if not self.is_same_element(other):
            return False
        if not self.pos.almost_same_as(other.pos):
            return False
        if not self.matrix.is_almost_same_as(other.matrix):
            return False
        return True

    @staticmethod
    def from_str(s):
        sl = s.split()
        if not len(sl) >= 15:
            return None
        line_type = int(sl[0].lstrip())
        if not line_type == 1:
            return None
        p = LdrPart()
        p.raw = s
        p.colour = int(sl[1])
        p.set_points(sl[2:5])
        p.matrix = Matrix(
            [
                [
                    quantize(sl[5]),
                    quantize(sl[6]),
                    quantize(sl[7]),
                ],
                [
                    quantize(sl[8]),
                    quantize(sl[9]),
                    quantize(sl[10]),
                ],
                [
                    quantize(sl[11]),
                    quantize(sl[12]),
                    quantize(sl[13]),
                ],
            ]
        )
        pname = " ".join(sl[14:])
        p.name = pname
        return p

    def render_image(self, scale=None, aspect=None, **kwargs):
        scale = scale if scale is not None else DEFAULT_PLI_SCALE
        aspect = aspect if aspect is not None else DEFAULT_PLI_ASPECT
        self.set_rotation(Vector(aspect))
        dpi = DEFAULT_DPI
        if "dpi" in kwargs:
            dpi = kwargs["dpi"]
        fn = self.pli_filename(scale, aspect, dpi)
        ldv = LDViewRender(**kwargs)
        ldv.set_scale(scale)
        ldv.render_from_parts([self], fn)

    def pli_filename(self, scale=None, aspect=None, dpi=None, **kwargs):
        scale = scale if scale is not None else DEFAULT_PLI_SCALE
        aspect = aspect if aspect is not None else DEFAULT_PLI_ASPECT
        dpi = dpi if dpi is not None else DEFAULT_DPI
        if "dpi" in kwargs:
            dpi = kwargs["dpi"]
        aspect = tuple(int(v) & 0xFF for v in aspect[:3])
        name = strip_part_ext(self.name)
        fn = "%s-%d-%3d-%.2f-%02X%02X%02X.png" % (
            name,
            self.colour.code,
            dpi,
            scale,
            aspect[0],
            aspect[1],
            aspect[2],
        )
        return fn
