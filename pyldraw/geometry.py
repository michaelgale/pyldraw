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
# Geometry helper classes and functions


import copy
import math
from math import degrees, atan2
from numbers import Number
from functools import reduce


class MatrixError(Exception):
    pass


class Axis(object):
    pass


class XAxis(Axis):
    pass


class YAxis(Axis):
    pass


class ZAxis(Axis):
    pass


class AngleUnits(object):
    pass


class Radians(AngleUnits):
    pass


class Degrees(AngleUnits):
    pass


def _rows_multiplication(r1, r2):
    rows = [
        [
            r1[0][0] * r2[0][0] + r1[0][1] * r2[1][0] + r1[0][2] * r2[2][0],
            r1[0][0] * r2[0][1] + r1[0][1] * r2[1][1] + r1[0][2] * r2[2][1],
            r1[0][0] * r2[0][2] + r1[0][1] * r2[1][2] + r1[0][2] * r2[2][2],
        ],
        [
            r1[1][0] * r2[0][0] + r1[1][1] * r2[1][0] + r1[1][2] * r2[2][0],
            r1[1][0] * r2[0][1] + r1[1][1] * r2[1][1] + r1[1][2] * r2[2][1],
            r1[1][0] * r2[0][2] + r1[1][1] * r2[1][2] + r1[1][2] * r2[2][2],
        ],
        [
            r1[2][0] * r2[0][0] + r1[2][1] * r2[1][0] + r1[2][2] * r2[2][0],
            r1[2][0] * r2[0][1] + r1[2][1] * r2[1][1] + r1[2][2] * r2[2][1],
            r1[2][0] * r2[0][2] + r1[2][1] * r2[1][2] + r1[2][2] * r2[2][2],
        ],
    ]
    return rows


class Matrix(object):
    """a transformation matrix"""

    __slots__ = "rows"

    def __init__(self, rows):
        self.rows = rows

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, str(self.values))

    def __str__(self):
        format_string = "((%f, %f, %f),\n" " (%f, %f, %f),\n" " (%f, %f, %f))"
        return format_string % (self.values)

    def __eq__(self, other):
        if not isinstance(other, Matrix):
            return False
        return self.rows == other.rows

    def __mul__(self, other):
        if isinstance(other, Matrix):
            r1 = self.rows
            r2 = other.rows
            return Matrix(_rows_multiplication(r1, r2))
        elif isinstance(other, Vector):
            r = self.rows
            x, y, z = other.x, other.y, other.z
            return Vector(
                r[0][0] * x + r[0][1] * y + r[0][2] * z,
                r[1][0] * x + r[1][1] * y + r[1][2] * z,
                r[2][0] * x + r[2][1] * y + r[2][2] * z,
            )
        else:
            raise MatrixError

    def __rmul__(self, other):
        if isinstance(other, Matrix):
            r1 = other.rows
            r2 = self.rows
            return Matrix(_rows_multiplication(r1, r2))
        elif isinstance(other, Vector):
            r = self.rows
            x, y, z = other.x, other.y, other.z
            return Vector(
                x * r[0][0] + y * r[1][0] + z * r[2][0],
                x * r[0][1] + y * r[1][1] + z * r[2][1],
                x * r[0][2] + y * r[1][2] + z * r[2][2],
            )
        else:
            raise MatrixError

    @property
    def values(self):
        return tuple(reduce(lambda x, y: x + y, self.rows))

    def is_almost_same_as(self, other, tolerance=1e-3):
        return all(
            [abs(self.rows[i][j] - other.rows[i][j]) > tolerance]
            for i in range(3)
            for j in range(3)
        )

    def copy(self):
        """make a copy of this matrix"""
        return Matrix(copy.deepcopy(self.rows))

    def rotate(self, angle, axis, units=Degrees):
        """rotate the matrix by an angle around an axis"""
        if units == Degrees:
            c = math.cos(angle / 180.0 * math.pi)
            s = math.sin(angle / 180.0 * math.pi)
        else:
            c = math.cos(angle)
            s = math.sin(angle)
        if axis == XAxis:
            rotation = Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])
        elif axis == YAxis:
            rotation = Matrix([[c, 0, -s], [0, 1, 0], [s, 0, c]])
        elif axis == ZAxis:
            rotation = Matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        else:
            raise MatrixError("Invalid axis specified.")
        return self * rotation

    def scale(self, sx, sy, sz):
        """scale the matrix by a number"""
        return Matrix([[sx, 0, 0], [0, sy, 0], [0, 0, sz]]) * self

    def transpose(self):
        """transpose"""
        r = self.rows
        return Matrix(
            [
                [r[0][0], r[1][0], r[2][0]],
                [r[0][1], r[1][1], r[2][1]],
                [r[0][2], r[1][2], r[2][2]],
            ]
        )

    def det(self):
        """determinant of the matrix"""
        r = self.rows
        terms = (
            r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1]),
            r[0][1] * (r[1][2] * r[2][0] - r[1][0] * r[2][2]),
            r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]),
        )
        return sum(terms)

    def flatten(self):
        """flatten the matrix"""
        return tuple(reduce(lambda x, y: x + y, self.rows))

    def fix_diagonal(self):
        """Some applications do not like matrices with zero diagonal elements."""
        corrected = False
        for i in range(3):
            if self.rows[i][i] == 0.0:
                self.rows[i][i] = 0.001
                corrected = True
        return corrected

    @staticmethod
    def euler_to_rot_matrix(euler):
        """converts a 3D tuple of euler rotation angles into a rotation matrix"""
        ax = Matrix.identity().rotate(euler[0], XAxis)
        ay = Matrix.identity().rotate(euler[1], YAxis)
        az = Matrix.identity().rotate(euler[2], ZAxis)
        rm = az * ay * ax
        rm = rm.transpose()
        return rm

    @staticmethod
    def identity():
        return Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])


class Vector(object):
    """a Vector in 3D"""

    __slots__ = ("x", "y", "z")

    def __init__(self, x, y=None, z=None):
        if isinstance(x, Vector):
            self.x = x.x
            self.y = x.y
            self.z = x.z
        elif isinstance(x, (tuple, list)):
            self.x = float(x[0])
            self.y = float(x[1])
            self.z = float(x[2])
        elif y is not None and z is not None:
            self.x, self.y, self.z = float(x), float(y), float(z)
        else:
            self.x = 0
            self.y = 0
            self.z = 0

    def __repr__(self) -> str:
        return "%s(%s, %s, %s)" % (self.__class__.__name__, self.x, self.y, self.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __add__(self, other):
        other = Vector(other)
        x = self.x + other.x
        y = self.y + other.y
        z = self.z + other.z
        # Return a new object.
        return Vector(x, y, z)

    __radd__ = __add__

    def __sub__(self, other):
        other = Vector(other)
        x = self.x - other.x
        y = self.y - other.y
        z = self.z - other.z
        # Return a new object.
        return Vector(x, y, z)

    def __rsub__(self, other):
        other = Vector(other)
        x = other.x - self.x
        y = other.y - self.y
        z = other.z - self.z
        # Return a new object.
        return Vector(x, y, z)

    def __cmp__(self, other):
        # This next expression will only return zero (equals) if all
        # expressions are false.
        return self.x != other.x or self.y != other.y or self.z != other.z

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            if not isinstance(other, (list, tuple)):
                return False
            if not len(other) == 3:
                return False
            return self.x == other[0] and self.y == other[1] and self.z == other[2]
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __abs__(self):
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def __rmul__(self, other):
        if isinstance(other, Number):
            return Vector(self.x * other, self.y * other, self.z * other)
        raise ValueError("Cannot multiply %s with %s" % (self.__class__, type(other)))

    def __div__(self, other):
        if isinstance(other, Number):
            return Vector(self.x / other, self.y / other, self.z / other)
        raise ValueError("Cannot divide %s with %s" % (self.__class__, type(other)))

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self.x
            elif key == 1:
                return self.y
            return self.z

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key == 0:
                self.x = value
            elif key == 1:
                self.y = value
            else:
                self.z = value

    def as_tuple(self):
        return (self.x, self.y, self.z)

    def copy(self):
        """vector = copy(self)
        Copy the vector so that new vectors containing the same values
        are passed around rather than references to the same object.
        """
        return Vector(self.x, self.y, self.z)

    def cross(self, other):
        """cross product"""
        return Vector(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def dot(self, other):
        """dot product"""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def norm(self):
        """normalized"""
        _length = abs(self)
        return Vector(self.x / _length, self.y / _length, self.z / _length)

    def polar_xy(self, r_offset=0.0):
        r = ((self.x + r_offset) * (self.x + r_offset) + self.y * self.y) ** 0.5
        t = degrees(atan2(self.y, (self.x + r_offset)))
        return (r, t)

    def offset_xy(self, xo, yo):
        return Vector(self.x + xo, self.y + yo, self.z)

    def polar_quad(self, r_offset=0.0):
        r, t = self.polar_xy(r_offset=0.0)
        if t > 0:
            if t > 90.0:
                return "TL"
            else:
                return "TR"
        else:
            if t < -90.0:
                return "BL"
            else:
                return "BR"

    def almost_same_as(self, other, tolerance=1e-3):
        if not isinstance(other, Vector):
            other = Vector(other)
        if abs(self.x - other.x) > tolerance:
            return False
        if abs(self.y - other.y) > tolerance:
            return False
        if abs(self.z - other.z) > tolerance:
            return False
        return True

    def is_colinear_with(self, other, tolerance=1e-3):
        """Returns true if two coordinates are the same between
        two vectors and are co-aligned."""
        if not isinstance(other, Vector):
            return False
        matched_axis = 0
        if abs(self.x - other.x) <= tolerance:
            matched_axis += 1
        if abs(self.y - other.y) <= tolerance:
            matched_axis += 1
        if abs(self.z - other.z) <= tolerance:
            matched_axis += 1
        return matched_axis


def safe_vector(v):
    """returns a Vector object by automatically inferring the input argument v"""
    if isinstance(v, Vector):
        return v
    elif isinstance(v, (tuple, list)):
        return Vector(v[0], v[1], v[2])
    elif isinstance(v, (float, int)):
        return Vector(v, v, v)
    return Vector(0, 0, 0)


class BoundBox:
    """A container class for representing the bounding box of a 3D object."""

    __slots__ = ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")

    def __init__(self, **kwargs):
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        self.zmin = None
        self.zmax = None

    def __str__(self):
        s = []
        s.append("BoundBox x: %f - %f (%f)" % (self.xmin, self.xmax, self.xlen))
        s.append("         y: %f - %f (%f)" % (self.ymin, self.ymax, self.ylen))
        s.append("         z: %f - %f (%f)" % (self.zmin, self.zmax, self.zlen))
        return "\n".join(s)

    @property
    def xlen(self):
        return self.xmax - self.xmin

    @property
    def ylen(self):
        return self.ymax - self.ymin

    @property
    def zlen(self):
        return self.zmax - self.zmin

    @property
    def size(self):
        return (self.xlen, self.ylen, self.zlen)

    @property
    def centre(self):
        return Vector(
            self.xmin + self.xlen / 2,
            self.ymin + self.ylen / 2,
            self.zmin + self.zlen / 2,
        )

    def translated(self, pt):
        pt = Vector(pt)
        bb = copy.copy(self)
        bb.xmin = bb.xmin + pt.x
        bb.xmax = bb.xmax + pt.x
        bb.ymin = bb.ymin + pt.y
        bb.ymax = bb.ymax + pt.y
        bb.zmin = bb.zmin + pt.z
        bb.zmax = bb.zmax + pt.z
        return bb

    def union(self, other):
        if isinstance(other, BoundBox):
            pts = [
                Vector(other.xmin, other.ymin, other.zmin),
                Vector(other.xmax, other.ymax, other.zmax),
            ]
        elif isinstance(other, (tuple, list)):
            if len(other) == 3 and isinstance(other[0], Number):
                pts = [Vector(other)]
            else:
                if isinstance(other[0], (tuple, list, Vector)):
                    pts = [Vector(v) for v in other]
                else:
                    pts = other
        else:
            pts = [Vector(other)]

        if self.xmin is None:
            self.xmin = pts[0].x
            self.xmax = pts[0].x
            self.ymin = pts[0].y
            self.ymax = pts[0].y
            self.zmin = pts[0].z
            self.zmax = pts[0].z

        for pt in pts:
            self.xmin = min(self.xmin, pt.x)
            self.xmax = max(self.xmax, pt.x)
            self.ymin = min(self.ymin, pt.y)
            self.ymax = max(self.ymax, pt.y)
            self.zmin = min(self.zmin, pt.z)
            self.zmax = max(self.zmax, pt.z)

        return self

    @staticmethod
    def from_pts(pts):
        bb = BoundBox()
        return bb.union(pts)
