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
# LDraw file parsing, with supporting model and step object classes

import os
from collections import Counter

from rich import print

from .geometry import Vector
from .constants import *
from .ldrcolour import LdrColour
from .ldrmodel import LdrModel
from .ldrstep import BuildStep
from .ldrutils import file_name_with_index


class UnwrapCtx:
    """A container class used to track the state of the model hierarchy when
    unwrapping a model into a linear building sequence.
    """

    def __init__(self, model_name, model, **kwargs):
        self.model_name = model_name
        self.model = model
        self.idx = 0
        self.level = 0
        self.qty = 0
        self.model_objs = []
        self.aspect = Vector(0, 0, 0)
        self.scale = 1.0
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v


class LdrFile:
    """LdrFile is a container for objects parsed from an LDraw file.
    It stores a root model and a dictionary of sub-models; each of which are
    LdrModel objects.  After parsing, a list of building steps is computed
    which represent a recursively unwrapped sequence of building instructions."""

    def __init__(self, filename=None, **kwargs):
        self.filename = filename
        # root model
        self.root = None
        # dictionary of submodels
        self.models = {}
        # list of unwrapped building steps (BuildStep objects)
        self.build_steps = None
        # default initial viewing angle
        self.initial_aspect = Vector(0, 0, 0)
        self.dpi = DEFAULT_DPI
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        if filename is not None:
            self.parse_file(filename)

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, self.filename)

    def parse_file(self, filename=None):
        """Parses an LDraw file into a structured object representation.
        This representation is also unwrapped into a linear sequence of
        building steps."""
        filename = filename if filename is not None else self.filename
        self.models = {}
        with open(filename, "rt") as fp:
            models = fp.read().split("0 FILE")
            root = None
            if len(models) == 1:
                root = models[0]
            else:
                root = "0 FILE " + models[1]
                for model in models[2:]:
                    model_name = model.splitlines()[0].strip()
                    model_str = "0 FILE " + model
                    m = LdrModel.from_str(model_str, model_name)
                    self.models[model_name] = m
            self.root = LdrModel.from_str(root, name="root")
        self.build_steps, _ = self.unwrap_build_steps()

    def print_raw(self):
        for s in self.build_steps:
            for o in s.objs:
                print(o)

    def print_bom(self):
        c = Counter()
        for o in self.model_parts_at_step(-1):
            c.update([o.part_key])
        c = c.most_common()
        for k, v in c:
            if k is None:
                continue
            ks = k.split("-")
            colour = LdrColour(int(ks[1]))
            if any(x in colour.name for x in ("Black", "Brown", "Dark")):
                print(
                    "[white]%3dx[/] [bold white on %s]%-20s[/] [%s]%s[/]"
                    % (v, colour.hex_code, colour.name, RICH_PART_COLOUR, ks[0])
                )
            else:
                print(
                    "[white]%3dx[/] [bold black on %s]%-20s[/] [%s]%s[/]"
                    % (v, colour.hex_code, colour.name, RICH_PART_COLOUR, ks[0])
                )

    def write_model_to_file(self, fn, idx=None):
        idx = idx if idx is not None else -1
        model = self.model_parts_at_step(idx)
        base_name_ext = os.path.basename(fn)
        base_name = os.path.splitext(os.path.basename(fn))[0]
        if idx < 0:
            idx = idx + len(self.build_steps)
        model_name = "%s_S%d" % (base_name, idx)
        model_name = base_name_ext.replace(base_name, model_name)
        with open(fn, "wt") as fp:
            fp.write("0 FILE %s\n" % (model_name))
            for obj in model:
                fp.write(str(obj) + "\n")
            fp.write("0 NOFILE\n")

    @property
    def piece_count(self):
        return len(self.model_parts_at_step(-1))

    @property
    def element_count(self):
        c = Counter()
        for o in self.model_parts_at_step(-1):
            c.update([o.part_key])
        return len(c)

    @property
    def colour_count(self):
        c = Counter()
        for o in self.model_parts_at_step(-1):
            c.update([o.colour.code])
        return len(c)

    def iter_steps(self):
        """Iterates through unwrapped building steps yielding a BuildStep object."""
        for step in self.build_steps:
            yield step

    def iter_root_steps(self):
        for step in self.build_steps:
            if step.level == 0:
                yield step

    def iter_model(self):
        """Iterates through snapshots of the build model at each build step.
        A list of LdrPart objects is returned representing the model state."""
        for step in self.build_steps:
            yield step.model_parts

    def model_parts_at_step(self, idx):
        return self.build_steps[idx].model_parts

    def step_parts_at_step(self, idx):
        return self.build_steps[idx].step_parts

    def objs_at_step(self, idx):
        return self.build_steps[idx].objs

    def unwrap_build_steps(self, ctx=None, unwrapped=None):
        """Unwraps the entire model object hierarchy into a linear sequence
        of building steps. The model is parsed recursively to determine the
        total accumulation of parts representing the model at each building step."""
        if ctx is None:
            ctx = UnwrapCtx("root", self.root, aspect=Vector(self.initial_aspect))
            unwrapped = []
        for step in ctx.model.build_steps(self.models):
            if len(step.sub_models) > 0:
                # this step has one or more references to submodels
                # recursively unwrap each unique submodel
                for name, qty in step.sub_models.items():
                    new_ctx = UnwrapCtx(
                        name,
                        self.models[name],
                        idx=ctx.idx,
                        level=ctx.level + 1,
                        qty=qty,
                        aspect=ctx.aspect,
                        scale=ctx.scale,
                    )
                    _, new_idx = self.unwrap_build_steps(
                        ctx=new_ctx,
                        unwrapped=unwrapped,
                    )
                    ctx.idx = new_idx
            build_step = BuildStep(
                objs=step.objs,
                dpi=self.dpi,
                **ctx.__dict__,
            )
            build_step.unwrap(self.models, model_objs=ctx.model_objs)
            ctx.aspect = build_step.aspect
            ctx.scale = build_step.scale
            if build_step.rotation_end:
                ctx.aspect = Vector(self.initial_aspect)
                build_step.aspect = ctx.aspect
            unwrapped.append(build_step)
            ctx.idx += 1
        return unwrapped, ctx.idx
