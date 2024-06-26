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
# Draw arrow symbols using LDraw shape primitives

from .geometry import safe_vector, Matrix, Vector
from .helpers import vector_str
from pyldraw import LdrColour, LdrTriangle, LdrQuad, LdrLine


class LdrArrow:
    def __init__(self, **kwargs):
        self.colour = LdrColour()
        self.border_colour = None
        self.matrix = Matrix.identity()
        self.tip_pos = Vector(0, 0, 0)
        self.tail_pos = Vector(0, 0, 0)
        self.tip_length = 16
        self.tip_width = 10
        self.tail_width = 4
        self.tip_taper = 3
        self.aspect = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                if "pos" in k:
                    self.__dict__[k] = safe_vector(v)
                elif "colour" in k:
                    self.__dict__[k] = LdrColour(v)
                else:
                    self.__dict__[k] = v

    def __repr__(self) -> str:
        return "%s(%s: %s)" % (self.__class__.__name__, str(self))

    def __str__(self):
        s = []
        s.append("LdrArrow: colour %d " % (self.colour.code))
        s.append("(%s) -> " % (vector_str(self.tail_pos)))
        s.append("(%s) " % (vector_str(self.tip_pos)))
        s.append("len: %.2f " % (self.length))
        s.append("dir: (%s) " % (vector_str(self.direction)))
        s.append("norm: (%s) " % (vector_str(self.normal)))
        return "".join(s)

    @property
    def length(self):
        """Length of the arrow from tip to tail"""
        return abs(self.tip_pos - self.tail_pos)

    @property
    def direction(self):
        """Direction of arrow from tail to tip"""
        return Vector((self.tail_pos - self.tip_pos).norm())

    @property
    def normal(self):
        """Returns a default normal vector orthogonal to arrow direction"""
        d = 90 * self.direction
        m = Vector(d.z, d.x, d.y)
        r = self.direction * Matrix.euler_to_rot_matrix(m)
        return r.cross(self.direction)

    @property
    def tail(self):
        """Tail position with the tip normalized to (0, 0, 0)"""
        return self.tail_pos - self.tip_pos

    @property
    def dir_str(self):
        if self.direction.almost_same_as((1, 0, 0)):
            return "+x"
        if self.direction.almost_same_as((-1, 0, 0)):
            return "-x"
        if self.direction.almost_same_as((0, 1, 0)):
            return "+y"
        if self.direction.almost_same_as((0, -1, 0)):
            return "-y"
        if self.direction.almost_same_as((0, 0, 1)):
            return "+z"
        if self.direction.almost_same_as((0, 0, -1)):
            return "-z"
        return ""

    def set_from_offset_bound_box(self, bb, offset):
        """Sets the arrow tip and tail position based on a bounding box region
        and offset.  Normally, the arrow tail is coincident with the bounding box
        centre and the tip is set at the offset from the tail."""
        tp = Vector(bb.centre)
        self.tail_pos = tp
        self.tip_pos = self.tail_pos - Vector(offset)

    def arrow_objs(self):
        """Returns a list of LdrObj shapes which render this arrow."""
        n = self.normal
        if self.aspect is not None:
            a = Vector(self.aspect)
            if "y" in self.dir_str:
                if a.y < 45 and a.y > -45:
                    n = Vector(1, 0, 0)
                elif a.y > 135 or a.y < -135:
                    n = Vector(1, 0, 0)

        tw2 = self.tip_width / 2
        p2l = self.tip_length * self.direction - tw2 * n
        p2r = self.tip_length * self.direction + tw2 * n
        p3 = (self.tip_length - self.tip_taper) * self.direction

        left_tip = LdrTriangle(colour=self.colour)
        left_tip.point1 = self.tip_pos
        left_tip.point2 = p2l + self.tip_pos
        left_tip.point3 = p3 + self.tip_pos

        right_tip = LdrTriangle(colour=self.colour)
        right_tip.point1 = self.tip_pos
        right_tip.point2 = p2r + self.tip_pos
        right_tip.point3 = p3 + self.tip_pos

        tl = self.length - self.tip_length + self.tip_taper
        tail = LdrQuad.from_size(tl * self.direction, self.tail_width * n)
        tail.colour = LdrColour(self.colour)
        ts = tl / 2 + self.tip_length - self.tip_taper
        tail.translate(Vector(ts * self.direction))
        tail.translate(self.tip_pos)

        objs = [left_tip, right_tip, tail]

        if self.border_colour is not None:
            ts = self.tip_taper / (self.tip_width / 2)
            tw = self.tip_width / 2 - self.tail_width / 2
            ptw = (self.tip_length - ts * tw) * self.direction
            pt2l = ptw - self.tail_width / 2 * n
            pt2r = ptw + self.tail_width / 2 * n
            bc = self.border_colour.code
            l1 = LdrLine(colour=bc, point1=self.tip_pos, point2=left_tip.point2)
            l2 = LdrLine(colour=bc, point1=self.tip_pos, point2=right_tip.point2)
            l3 = LdrLine(colour=bc, point1=left_tip.point2, point2=pt2l)
            l4 = LdrLine(colour=bc, point1=right_tip.point2, point2=pt2r)
            l5 = LdrLine(colour=bc, point1=pt2l, point2=tail.point2)
            l6 = LdrLine(colour=bc, point1=pt2r, point2=tail.point3)
            l7 = LdrLine(colour=bc, point1=tail.point2, point2=tail.point3)
            objs.extend([l1, l2, l3, l4, l5, l6, l7])
        return objs
