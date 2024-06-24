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

from collections import Counter

from .geometry import Vector
from pyldraw import *


class LdrModel:
    """LdrModel is a simple container for LdrSteps within a single model definition.
    LdrModel objects are delimited by FILE / NOFILE directives in the LDraw file."""

    def __init__(self, name, **kwargs):
        self.name = name
        self.steps = []

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
