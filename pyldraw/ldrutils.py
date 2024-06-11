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
# LDraw object utilities

from .ldrobj import LdrMeta, LdrPart


def filter_objs(
    a,
    as_mask=False,
    obj_type=None,
    is_part=None,
    part_key=None,
    name=None,
    meta_key=None,
    colour=None,
    path=None,
):
    x = [True] * len(a)
    if obj_type is not None:
        x = [xo and isinstance(o, obj_type) for xo, o in zip(x, a)]
    if meta_key is not None:
        x = [
            xo and (o.command == meta_key if isinstance(o, LdrMeta) else False)
            for xo, o in zip(x, a)
        ]
    if colour is not None:
        x = [xo and o.colour.code == colour for xo, o in zip(x, a)]
    if path is not None:
        x = [xo and o.path == path for xo, o in zip(x, a)]
    if is_part is not None:
        x = [
            xo and (bool(o.part_name) if isinstance(o, LdrPart) else False)
            for xo, o in zip(x, a)
        ]
    if part_key is not None:
        x = [xo and o.part_key == part_key for xo, o in zip(x, a)]
    if name is not None:
        x = [xo and o.matched_name(name) for xo, o in zip(x, a)]
    if as_mask:
        return x
    return [o for o, mask in zip(a, x) if mask]


def obj_rename(a, new_name, **filters):
    """changes all objects in a to different colour."""
    if len(filters):
        m = filter_objs(a, as_mask=True, **filters)
        return [o.renamed(new_name) if mask else o for o, mask in zip(a, m)]
    return [o.renamed(new_name) for o in a]


def obj_change_colour(a, new_colour, **filters):
    """changes all objects in a to different colour."""
    if len(filters):
        m = filter_objs(a, as_mask=True, **filters)
        return [o.new_colour(new_colour) if mask else o for o, mask in zip(a, m)]
    return [o.new_colour(new_colour) for o in a]


def obj_move_to(a, pos, **filters):
    """Moves all objects in a to new position"""
    if len(filters):
        m = filter_objs(a, as_mask=True, **filters)
        return [o.moved_to(pos) if mask else o for o, mask in zip(a, m)]
    return [o.moved_to(pos) for o in a]


def obj_translated(a, offset, **filters):
    """Moves all objects in a to new position"""
    if len(filters):
        m = filter_objs(a, as_mask=True, **filters)
        return [o.translated(offset) if mask else o for o, mask in zip(a, m)]
    return [o.translated(offset) for o in a]


def obj_union(a, b):
    """returns the union of objects from a and b"""
    x = [o for o in a]
    y = [o for o in b if o not in a]
    x.extend(y)
    return x


def obj_difference(a, b):
    """returns the objects of a minus any of the same elements in b"""
    return [o for o in a if o not in b]


def obj_intersect(a, b):
    """returns the common elements of a and b"""
    return [o for o in a if o in b]


def obj_exclusive(a, b):
    """returns the elements of a and b which are not common"""
    c = obj_union(a, b)
    return obj_difference(c, obj_intersect(a, b))
