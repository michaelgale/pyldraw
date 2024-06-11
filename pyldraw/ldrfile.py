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

from collections import Counter
import hashlib
import inspect

from rich import print

from .geometry import Vector, Matrix
from .ldrobj import LdrObj, LdrMeta
from .ldrcolour import LdrColour
from .constants import *


def recursive_unwrap_model(
    model,
    submodels,
    objects=None,
    offset=None,
    matrix=None,
    only_submodel=None,
):
    """Recursively parses an LDraw model plus any submodels and
    populates an object list representing that model.  To support selective
    parsing of only one submodel, only_submodel can be set to the desired
    submodel name."""
    o = offset if offset is not None else Vector(0, 0, 0)
    m = matrix if matrix is not None else Matrix.identity()
    if objects is None:
        objects = []
    for obj in model.iter_objs():
        if only_submodel is not None:
            if not obj.is_model_named(only_submodel):
                continue
        if obj.model_part_name in submodels:
            submodel = submodels[obj.model_part_name]
            new_matrix = m * obj.matrix
            new_loc = m * obj.pos
            new_loc += o
            recursive_unwrap_model(
                submodel,
                submodels,
                objects,
                offset=new_loc,
                matrix=new_matrix,
            )
        else:
            if only_submodel is None:
                new_obj = obj.copy()
                new_obj = new_obj.transformed(matrix=m, offset=o)
                objects.append(new_obj)
    return objects


class LdrStep:
    """LdrStep is a simple container for LdrObj objects associated with s single step.
    LdrStep objects are delimited by STEP directives in an LDraw file.
    """

    def __init__(self, objs=None, **kwargs):
        self.objs = []
        if objs is not None:
            self.objs = objs
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        self._sub_models = None
        self._parts = None

    def __repr__(self) -> str:
        return "%s(%d objects)" % (self.__class__.__name__, len(self.objs))

    def __str__(self):
        return "Step: %d objects, %d parts,  %d sub-models" % (
            len(self.objs),
            self.part_qty,
            self.sub_model_qty,
        )

    def __rich__(self):
        s = []
        for o in self.objs:
            s.append(o.__rich__())
        return "\n".join(s)

    def __getitem__(self, key):
        return self.objs[key]

    def iter_objs(self):
        for o in self.objs:
            yield o

    @property
    def part_qty(self):
        return sum(v for _, v in self.parts.items())

    @property
    def sub_model_qty(self):
        return sum(v for _, v in self.sub_models.items())

    @property
    def sub_models(self):
        """Returns a dictionary of quantities of unique sub-model references in this step"""
        if self._sub_models is not None:
            return self._sub_models
        self._sub_models = Counter()
        for o in self.objs:
            if o.model_part_name is not None:
                self._sub_models.update([o.model_part_name])
        return self._sub_models

    @property
    def parts(self):
        """Returns a dictionary of quantities of unique part references in this step"""
        if self._parts is not None:
            return self._parts
        self._parts = Counter()
        for o in self.objs:
            if o.part_name is not None:
                self._parts.update([o.part_key])
        return self._parts

    def assign_path_to_objs(self, path):
        self.objs = [o.new_path(path) for o in self.objs]


class BuildStep(LdrStep):
    """BuildStep is a richer representation of LdrStep with additional data to
    represent a building step in an instruction sequence. It also stores
    unwrapped object representations of the objects added at this step as well
    as the total model representation at this step."""

    def __init__(self, objs=None, **kwargs):
        super().__init__(objs, **kwargs)
        self.scale = 1
        self.aspect = Vector(0, 0, 0)
        self.pos = Vector(0, 0, 0)
        self.idx = None
        self.level = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        # container for all objects which represent the complete model at this step
        self._model_objs = None
        # container for all objects added at this step
        self._step_objs = None
        self._sha1_hash = None

    def __repr__(self) -> str:
        return "%s(%d step objects)" % (self.__class__.__name__, len(self.step_objs))

    def __rich__(self):
        s = []
        s.append("STEP: %d level: %d aspect: %s" % (self.idx, self.level, self.aspect))
        s.append(
            "  step objs: %d  model objs: %d  step parts: %d  model parts: %d"
            % (
                len(self.step_objs),
                len(self.model_objs),
                len(self.step_parts),
                len(self.model_parts),
            )
        )
        for o in self.step_parts:
            s.append(o.__rich__())
        return "\n".join(s)

    def __str__(self):
        indent = " " * (self.level + 1)
        postdent = " " * (4 - self.level)
        if self.start_of_model and self.end_of_model:
            model_state = "="
        elif self.start_of_model:
            model_state = ">"
        elif self.end_of_model:
            model_state = "<"
        else:
            model_state = " "
        return (
            "STEP: %3d%s level: %1d%s%s step-parts: %3d model-parts: %4d aspect: %s "
            % (
                self.idx,
                indent,
                self.level,
                postdent,
                model_state,
                len(self.step_parts),
                len(self.model_parts),
                self.aspect,
            )
        )

    @property
    def sha1_hash(self):
        """Computes the SHA1 hash of this step to detect if the model has changed
        appearance.
        This is useful for caching renders of each step since parts
        can change sequence within a building step without requiring re-rendering.
        The hash uses both the object content at this step as well as the appearance
        of the total model.  This ensures early changes in the model build sequence
        will propagate to all subsequent steps.  Furthermore, the aspect angle of the
        model also will also change the hash."""
        if self._sha1_hash is None:
            shash = hashlib.sha1()
            shash.update(bytes(str(self.aspect), encoding="utf8"))
            objs = [str(o) for o in self.objs]
            objs.extend([str(o) for o in self.model_parts])
            objs = sorted(objs)
            for o in objs:
                shash.update(bytes(o, encoding="utf8"))
            self._sha1_hash = shash.hexdigest()
        return self._sha1_hash

    def unwrap(self, sub_models, model_objs=None):
        """Unwraps any sub-model references in this step into parts translated
        to the correct position and orientation in the model."""
        aspect = Vector(self.aspect)
        self._step_objs = None
        self._model_objs = None
        objs = recursive_unwrap_model(self, sub_models)
        self._step_objs = [o.rotated_by(aspect) for o in objs]
        if model_objs is not None:
            objs = recursive_unwrap_model(self, sub_models, objects=model_objs)
            self._model_objs = [o.rotated_by(aspect) for o in objs]

    @property
    def step_objs(self):
        """Returns a list of LdrObj representing new objects added at this step."""
        if self._step_objs is not None:
            return self._step_objs

    @property
    def model_objs(self):
        """Returns a list of all LdrObj representing the total model"""
        if self._model_objs is not None:
            return self._model_objs

    @property
    def step_parts(self):
        """Returns a list of LdrPart objects representing the new parts added at this step"""
        return [p for p in self.step_objs if p.part_name is not None]

    @property
    def model_parts(self):
        """Returns a list of LdrPart objects representing the total model at this step."""
        return [p for p in self.model_objs if p.part_name is not None]

    def iter_meta_objs(self):
        """Generator which iterates over step objects which represent meta commands"""
        for o in self.objs:
            if isinstance(o, LdrMeta):
                yield o

    def step_has_meta_command(self, attr=None):
        """Looks for an LdrMeta object with a desired attribute.
        Returns the attribute value or None."""
        if attr is None:
            attr = inspect.currentframe().f_back.f_code.co_name
        for o in self.iter_meta_objs():
            if attr in dir(o):
                v = getattr(o, attr)
                if v:
                    return v
        return None

    @property
    def rotation_absolute(self):
        return self.step_has_meta_command()

    @property
    def rotation_relative(self):
        return self.step_has_meta_command()

    @property
    def rotation_end(self):
        return self.step_has_meta_command()

    @property
    def start_of_model(self):
        return self.step_has_meta_command()

    @property
    def end_of_model(self):
        return self.step_has_meta_command()


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

    def assign_path_to_objs(self, path):
        """Assigns each LdrObj in this model with a path reference describing
        the object's position in the overall model hierarchy."""
        for step in self.steps:
            step.assign_path_to_objs(path)

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
        self.path = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        if self.path is not None:
            self.path = self.path[2:] + "/" + self.model_name
        else:
            self.path = self.model_name
        self.path = str(self.level) + "/" + self.path


class LdrFile:
    """LdrFile is a simple container for objects parsed from an LDraw file.
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
        self.initial_aspect = Vector(0, 0, 0)
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
            ks = k.split("-")
            colour = LdrColour(int(ks[1]))
            print(
                "%3dx [reverse %s]%-20s[not reverse] [%s]%s[/]"
                % (v, colour.hex_code, colour.name, RICH_PART_COLOUR, ks[0])
            )

    def write_model_to_file(self, fn, idx):
        model = self.model_parts_at_step(-1)
        with open(fn, "wt") as fp:
            for obj in model:
                fp.write(str(obj) + "\n")

    @property
    def piece_count(self):
        return len(self.model_parts_at_step(-1))

    @property
    def element_count(self):
        c = Counter()
        for o in self.model_parts_at_step(-1):
            c.update([o.part_key])
        return len(c)

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
            step.assign_path_to_objs(ctx.path)
            if len(step.sub_models) > 0:
                for name, qty in step.sub_models.items():
                    new_ctx = UnwrapCtx(
                        name,
                        self.models[name],
                        idx=ctx.idx,
                        level=ctx.level + 1,
                        qty=qty,
                        aspect=ctx.aspect,
                        path=ctx.path,
                    )
                    self.models[name].assign_path_to_objs(new_ctx.path)
                    _, new_idx = self.unwrap_build_steps(
                        ctx=new_ctx,
                        unwrapped=unwrapped,
                    )
                    ctx.idx = new_idx
            build_step = BuildStep(
                objs=step.objs,
                idx=ctx.idx,
                level=ctx.level,
                aspect=ctx.aspect,
            )
            build_step.unwrap(self.models, model_objs=ctx.model_objs)
            if build_step.rotation_relative:
                ctx.aspect += build_step.rotation_relative
            elif build_step.rotation_absolute:
                ctx.aspect = build_step.rotation_absolute
            elif build_step.rotation_end:
                ctx.aspect = Vector(self.initial_aspect)
            unwrapped.append(build_step)
            ctx.idx += 1
        return unwrapped, ctx.idx
