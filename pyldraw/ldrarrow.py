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
from pyldraw import *


class LdrArrow:
    def __init__(self, **kwargs):
        self.colour = LdrColour.ARROW_RED()
        self.border_colour = None
        self.tip_pos = Vector(0, 0, 0)
        self.tail_pos = Vector(0, 0, 0)
        self.tip_length = 16
        self.tip_width = 10
        self.tail_width = 4
        self.tip_taper = 3
        self.aspect = None
        self.tilt = 0
        self.ratio = None
        self.dash = None
        self.wide = None
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

    def wide_style(self):
        """Apply a preset style for wide dashed arrows."""
        self.colour = LdrColour.ARROW_YELLOW()
        self.border_colour = LdrColour(0)
        self.tip_length = 15
        self.tip_width = 36
        self.tail_width = 20
        self.tip_taper = 0
        self.dash = [10, 5]
        self.wide = True

    def dash_line_style(self):
        """Apply a preset for dashed lines with no arrow head."""
        self.border_colour = None
        self.tip_length = 0
        self.tip_width = 0
        self.tail_width = 2
        self.tip_taper = 0
        self.dash = [5, 3]

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

    def arrow_objs(self):
        """Returns a list of LdrObj shapes which render this arrow."""
        n = self.normal
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
        ts = tl / 2 + self.tip_length - self.tip_taper
        tails = []
        if self.dash is None:
            tail = LdrQuad.from_size(tl * self.direction, self.tail_width * n)
            tail.colour = LdrColour(self.colour)
            tail.translate(Vector(ts * self.direction))
            tail.translate(self.tip_pos)
            tails.append(tail)
        else:
            sl = sum(self.dash)
            segments = int(tl / sl)
            for i in range(segments):
                tail = LdrQuad.from_size(
                    self.dash[0] * self.direction, self.tail_width * n
                )
                tail.colour = LdrColour(self.colour)
                loc = self.tip_length + self.dash[1] + self.dash[0] / 2 + (i * sl)
                tail.translate(Vector(loc * self.direction))
                tail.translate(self.tip_pos)
                tails.append(tail)
                if self.border_colour is not None:
                    for i in range(4):
                        a, b = i % 4, (i + 1) % 4
                        line = LdrLine(
                            colour=self.border_colour.code,
                            point1=tail._pts[a],
                            point2=tail._pts[b],
                        )
                        tails.append(line)
        if self.tip_width > 0:
            objs = [left_tip, right_tip]
            objs.extend(tails)
        else:
            objs = tails

        if self.border_colour is not None and self.tip_width > 0:
            ts = self.tip_taper / (self.tip_width / 2)
            tw = self.tip_width / 2 - self.tail_width / 2
            ptw = (self.tip_length - ts * tw) * self.direction
            pt2l = ptw - self.tail_width / 2 * n
            pt2r = ptw + self.tail_width / 2 * n
            bc = self.border_colour.code
            l1 = LdrLine(colour=bc, point1=self.tip_pos, point2=left_tip.point2)
            l2 = LdrLine(colour=bc, point1=self.tip_pos, point2=right_tip.point2)
            if self.dash is None:
                l3 = LdrLine(colour=bc, point1=left_tip.point2, point2=pt2l)
                l4 = LdrLine(colour=bc, point1=right_tip.point2, point2=pt2r)
                l5 = LdrLine(colour=bc, point1=pt2l, point2=tails[0].point2)
                l6 = LdrLine(colour=bc, point1=pt2r, point2=tails[0].point3)
                l7 = LdrLine(colour=bc, point1=tails[0].point2, point2=tails[0].point3)
                objs.extend([l1, l2, l3, l4, l5, l6, l7])
            else:
                l3 = LdrLine(colour=bc, point1=left_tip.point2, point2=right_tip.point2)
                objs.extend([l1, l2, l3])

        if self.ratio is not None:
            # apply optional arrow shift proportional to length
            offset = (self.ratio * self.length) * self.direction
            objs = [o.translated(offset) for o in objs]

        if "x" in self.direction.dir_str:
            # prefer arrow heads to lie "flat" with respect to the x-z axis
            angle = 90 * self.direction
            objs = [o.rotated_by(angle, origin=self.tip_pos) for o in objs]

        if "y" in self.direction.dir_str and self.aspect is not None and not self.wide:
            # prefer arrows to face the "camera" if standing vertical
            # except if they are wide
            angle = (90 - self.aspect[1]) * self.direction
            if "-" in self.direction.dir_str:
                angle = -1.0 * angle
            objs = [o.rotated_by(angle, origin=self.tip_pos) for o in objs]

        if abs(self.tilt) > 0:
            # apply optional rotation about arrow's "roll" axis
            angle = self.tilt * self.direction
            objs = [o.rotated_by(angle, origin=self.tip_pos) for o in objs]

        return objs

    @staticmethod
    def norm_to_face(v):
        """Converts normalized offset vector to boundbox face"""
        if v.norm().almost_same_as((0, -1, 0)):
            return ">y"
        if v.norm().almost_same_as((0, 1, 0)):
            return "<y"
        if v.norm().almost_same_as((-1, 0, 0)):
            return ">x"
        if v.norm().almost_same_as((1, 0, 0)):
            return "<x"
        if v.norm().almost_same_as((0, 0, -1)):
            return ">z"
        if v.norm().almost_same_as((0, 0, 1)):
            return "<z"
        return None

    @staticmethod
    def offset_list_from_meta(meta):
        """Returns a list of arrow offset vectors specified in the !PY ARROW meta."""
        p = meta.parameters
        offsets = [Vector.from_dict(p)]
        if "extra" in p:
            v = [float(e) for e in p["extra"]]
            extra_arrows = int(len(v) / 3)
            for _, i in enumerate(range(extra_arrows)):
                offsets.append(Vector(v[(i * 3) : (i * 3) + 3]))
        return offsets

    @staticmethod
    def mean_offset_from_meta(meta):
        """Computes the mean offset from a list of arrow offset vectors specified in the !PY ARROW meta"""
        offsets = LdrArrow.offset_list_from_meta(meta)
        t = [list(set([v[i] for v in offsets])) for i in range(3)]
        return Vector([0 if len(t[i]) > 1 else t[i][0] for i in range(3)])

    @staticmethod
    def objs_from_meta(meta, aspect=None, boundbox=None):
        """Returns arrow drawing primitives based on the arrows specified in the !PY ARROW meta."""
        p = meta.parameters
        offsets = LdrArrow.offset_list_from_meta(meta)
        mean = LdrArrow.mean_offset_from_meta(meta)
        origin = Vector()
        bb_face = None
        if boundbox is not None:
            bb_face = LdrArrow.norm_to_face(mean)
            origin = boundbox.face(bb_face) if bb_face is not None else boundbox.centre
        else:
            origin = origin + mean
        if bb_face is not None:
            # apply a slight offset to clear stud height or align with grid
            obj_dim = boundbox.axis_len(bb_face)
            if is_stud_multiple(obj_dim, with_either=True):
                origin = origin + LDR_HALF * mean.norm()
            elif is_plate_multiple(obj_dim, with_either=True):
                origin = origin + LDR_STUD * mean.norm()
        if boundbox is not None and bb_face is not None and "AUTO" in p["flags"]:
            # auto place arrows at element extents along biggest axis if:
            #   - longest face is not coincident with offset direction
            #   - the extents are at least 2 studs apart
            #   - the extents span an integer multiple of studs
            axis, ext = boundbox.biggest_dim()
            if (
                not axis in bb_face
                and not ext < 2 * LDR_PITCH
                and is_stud_multiple(ext)
            ):
                o = Vector(offsets[0])
                o1 = Vector(o)
                o1[axis] = -ext / 2 + LDR_HALF
                o2 = Vector(o)
                o2[axis] = ext / 2 - LDR_HALF
                offsets = [o1, o2]
        t = [list(set([v[i] for v in offsets])) for i in range(3)]
        t = [1 if len(t[i]) > 1 else 0 for i in range(3)]
        arrows = []
        if not "NO_ARROW" in p["flags"]:
            for o in offsets:
                a = LdrArrow(aspect=aspect)
                if "colour" in p:
                    a.colour = LdrColour(int(p["colour"]))
                if "tilt" in p:
                    a.tilt = float(p["tilt"])
                if "ratio" in p:
                    a.ratio = float(p["ratio"])
                if "WIDE" in p["flags"]:
                    a.wide_style()
                v = origin
                a.tail_pos = Vector(
                    [v[i] if not t[i] else v[i] - o[i] for i in range(3)]
                )
                v = a.tail_pos
                a.tip_pos = Vector([v[i] if t[i] else v[i] - o[i] for i in range(3)])
                if "length" in p:
                    # apply a fixed length offset rather than mean offset
                    fl = (a.length - float(p["length"])) * a.direction
                    a.tip_pos = a.tip_pos + fl
                arrows.append(a)
        if "EXTENTS" in p["flags"] and bb_face is not None:
            lines = boundbox.face_corners(bb_face)
            for e in lines:
                a = LdrArrow(aspect=aspect)
                a.dash_line_style()
                a.tail_pos = e
                v = a.tail_pos
                a.tip_pos = Vector([v[i] if t[i] else v[i] - mean[i] for i in range(3)])
                arrows.append(a)

        objs = [
            LdrMeta.from_colour(LdrColour.ARROW_RED()),
            LdrMeta.from_colour(LdrColour.ARROW_BLUE()),
            LdrMeta.from_colour(LdrColour.ARROW_GREEN()),
            LdrMeta.from_colour(LdrColour.ARROW_YELLOW()),
        ]
        for a in arrows:
            objs.extend([o.new_path("arrow") for o in a.arrow_objs()])
        return objs
