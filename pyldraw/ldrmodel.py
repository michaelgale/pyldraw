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
# LdrModel object class

import os

from collections import Counter

from .geometry import Vector, BoundBox, Matrix
from pyldraw import *
from .ldrlib import find_part


class LdrModel:
    """LdrModel is a simple container for LdrSteps within a single model definition.
    LdrModel objects are delimited by FILE / NOFILE directives in the LDraw file."""

    def __init__(self, name, **kwargs):
        self.name = name
        self.steps = []
        self._bound_box = None

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def iter_steps(self):
        """Generator to iterate through LdrStep objects in this model"""
        for step in self.steps:
            yield step

    def iter_objs(self):
        """Generator to iterate through all LdrObj objects in this
        model across all steps"""
        for step in self.steps:
            for obj in step.iter_objs():
                yield obj

    def iter_parts(self):
        for o in self.iter_objs():
            if isinstance(o, LdrPart):
                yield o

    def iter_primitives(self):
        for o in self.iter_objs():
            if isinstance(o, (LdrLine, LdrTriangle, LdrQuad)):
                yield o

    @property
    def step_count(self):
        return len(self.steps)

    @property
    def obj_count(self):
        return len([1 for o in self.iter_objs()])

    @property
    def part_count(self):
        c = Counter()
        for s in self.steps:
            for k, _ in s.parts.items():
                c.update([k])
        return len(c)

    @property
    def sub_model_count(self):
        c = Counter()
        for s in self.steps:
            for k, _ in s.sub_models.items():
                c.update([k])
        return len(c)

    @property
    def part_qty(self):
        return sum(s.part_qty for s in self.steps)

    @property
    def sub_model_qty(self):
        return sum(s.sub_model_qty for s in self.steps)

    @property
    def bound_box(self):
        if self._bound_box is None:
            bb = BoundBox()
            for o in self.iter_objs():
                bb = bb.union(o.points)
            self._bound_box = bb
        return self._bound_box

    def build_steps(self, sub_models, at_aspect=None):
        """Unwraps steps into BuildStep objects which place objects at the
        correct orientation and unwraps sub-models into parts."""
        aspect = at_aspect if at_aspect is not None else Vector(0, 0, 0)
        steps = []
        for step in self.iter_steps():
            build_step = BuildStep(objs=step.objs, aspect=aspect)
            build_step.unwrap(sub_models)
            steps.append(build_step)
        return steps

    @staticmethod
    def from_str(s, name=None):
        """Retuns a LdrModel object based on parsing an LDraw string representing
        a root or sub-model."""
        objs = []
        steps = []
        for line in s.splitlines():
            obj = LdrObj.from_str(line)
            if obj is not None:
                objs.append(obj)
                if obj.is_step_delimiter:
                    if len(objs) > 0:
                        steps.append(LdrStep(objs))
                    objs = []
        if len(objs) > 0:
            if len(steps) > 0:
                steps[-1].objs.extend(objs)
            else:
                steps.append(LdrStep(objs))

        if name is not None:
            name = name
        else:
            if steps[0][0].is_model_name:
                name = steps[0][0].model_name
        m = LdrModel(name)
        m.steps = steps
        return m

    @staticmethod
    def from_file(filename):
        """Retuns a LdrModel object based on parsing an the contents of an LDraw file"""
        _, name = os.path.split(filename)
        with open(filename, "rt") as fp:
            lines = fp.readlines()
        return LdrModel.from_str("\n".join(lines), name=name)

    @staticmethod
    def from_part(filename):
        """Returns a LdrModel which represents the primitive geometry of a part.
        This requires unwrapping the part and its subparts until all of the
        primitive geometry is extracted.  The resulting LdrModel contains only
        one step which includes all of the primitive objects to make the part."""
        models = LdrModel.unwrap_part_submodels(file=filename)
        objs = LdrModel.recursive_unwrap_part(models["root"], models)
        m = LdrModel(name=filename)
        step = LdrStep(objs)
        m.steps = [step]
        return m

    @staticmethod
    def unwrap_part_submodels(model=None, submodels=None, file=None):
        """Recursively unwrap a part to discover all of the sub-model parts in
        the part hierarchy.  A dictionary is returned with the keys representing
        the part names and the values containing LdrModel objects.  This dictionary
        can then be used to traverse a part hierarchy (starting with the "root" object)
        to unwrap the primitive objects representing its geometry."""
        if model is None:
            fn = find_part(file)
            m = LdrModel.from_file(fn)
        else:
            m = model
        sm = submodels if submodels is not None else {"root": m}
        for p in m.iter_parts():
            fn = find_part(p.name)
            if fn is not None:
                if p.name not in sm:
                    next_model = LdrModel.from_file(fn)
                    sm = LdrModel.unwrap_part_submodels(model=next_model, submodels=sm)
                    sm[p.name] = next_model
        return sm

    @staticmethod
    def recursive_unwrap_part(
        model,
        submodels,
        objects=None,
        offset=None,
        matrix=None,
    ):
        """Recursively parses an LDraw part plus any submodels and
        populates an object list representing the primitives for the part.
        """
        o = offset if offset is not None else Vector(0, 0, 0)
        m = matrix if matrix is not None else Matrix.identity()
        if objects is None:
            objects = []
        for obj in model.iter_objs():
            if obj.part_name in submodels:
                submodel = submodels[obj.part_name]
                new_matrix = m * obj.matrix
                new_loc = m * obj.pos
                new_loc += o
                LdrModel.recursive_unwrap_part(
                    submodel,
                    submodels,
                    objects,
                    offset=new_loc,
                    matrix=new_matrix,
                )
            else:
                if obj.is_primitive:
                    new_obj = obj.copy()
                    new_obj = new_obj.transformed(matrix=m, offset=o)
                    objects.append(new_obj)
        return objects
