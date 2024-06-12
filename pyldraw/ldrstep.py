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
# LdrStep class

from collections import Counter
import hashlib
import inspect

from rich import print

from .geometry import Vector, Matrix
from .ldrutils import *
from .helpers import normalize_filename, strip_part_ext
from pyldraw import *
from pyldraw.support.imgutils import ImageMixin


class LdrStep:
    """LdrStep is a simple container for LdrObj objects associated with s single step.
    LdrStep objects are delimited by STEP and ROTSTEP directives in an LDraw file.
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

    def delimited_objs(self):
        """Captures objects in a step which are between BEGIN/END delimiters.
        This can be useful for extracting objects which are marked for
        exclusion in a parts list, or objects added by LSYNTH, etc.
        A list of dictionaries is returned with the dictionary containing
        keys for the LDraw line that triggered the capture and a list of parts
        associated with the capture."""
        delimited = []
        group = {}
        is_captured = False
        for o in self.objs:
            if o.has_start_capture_meta and not is_captured:
                is_captured = True
                group["trigger"] = o.raw
                group["objs"] = []
            elif o.has_end_capture_meta and is_captured:
                delimited.append(group)
                group = {}
                is_captured = False
            elif is_captured:
                group["objs"].append(o)
        return delimited

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
        self.dpi = DEFAULT_DPI
        self.outline_width = 3
        self.outline_colour = LdrColour(14)
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        # container for all objects which represent the complete model at this step
        self._model_objs = None
        # container for all objects added at this step
        self._step_objs = None
        # hash code for detecting changes in model state
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
        will propagate to all subsequent steps.  Furthermore, the scale, dpi and
        aspect angle of the model also will also change the hash."""
        if self._sha1_hash is None:
            hk = hashlib.sha1()
            hk.update(bytes(str(self.aspect), encoding="utf8"))
            hk.update(bytes(str("%.3f" % (self.scale)), encoding="utf8"))
            hk.update(bytes(str("%3d" % (self.dpi)), encoding="utf8"))
            objs = [str(o) for o in self.objs]
            objs.extend([str(o) for o in self.model_parts])
            objs = sorted(objs)
            for o in objs:
                hk.update(bytes(o, encoding="utf8"))
            self._sha1_hash = hk.hexdigest()
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
        return filter_objs(self.step_objs, is_part=True)

    @property
    def model_parts(self):
        """Returns a list of LdrPart objects representing the total model at this step."""
        return filter_objs(self.model_objs, is_part=True)

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

    def render_model(self, **kwargs):
        """Renders an image of the model for this step."""
        path = kwargs["output_path"]
        fn = normalize_filename(self.model_filename(), path)
        if "dpi" in kwargs:
            kwargs["dpi"] = self.dpi
        ldv = LDViewRender(**kwargs)
        ldv.render_from_parts(self.model_parts, fn)
        img = ImageMixin.pad_image(fn, self.outline_width)
        ImageMixin.save_image(fn, img)

    def render_outline_image(self, **kwargs):
        path = kwargs["output_path"]
        unmasked = normalize_filename(self.unmasked_filenames[0][0], path)
        model = normalize_filename(self.model_filename(), path)
        outline = normalize_filename(self.outline_filename, path)
        img = ImageMixin.merge_with_outlines(
            model,
            ADDED_PARTS_HSV_HUE,
            unmasked,
            self.outline_colour.bgr,
            self.outline_width,
        )
        ImageMixin.save_image(outline, img)

    def _render_maskable_image(self, fn, mask_colour, submodel=None, **kwargs):
        step_parts = filter_objs(self.step_parts, path=submodel)
        prev_parts = obj_difference(self.model_parts, step_parts)
        prev_parts = obj_change_colour(prev_parts, mask_colour)
        new_parts = obj_change_colour(step_parts, ADDED_PARTS_COLOUR, path=submodel)
        parts = obj_union(prev_parts, new_parts)
        if "dpi" in kwargs:
            kwargs["dpi"] = self.dpi
        ldv = LDViewRender(**kwargs)
        ldv.lofi_settings()
        ldv.render_from_parts(parts, fn)
        img = ImageMixin.pad_image(fn, self.outline_width)
        ImageMixin.save_image(fn, img)

    def render_unmasked_image(self, **kwargs):
        path = kwargs["output_path"]
        for fn, name in self.unmasked_filenames:
            fn = normalize_filename(fn, path)
            self._render_maskable_image(fn, NON_MASKED_COLOUR, name, **kwargs)
            # centroids = ImageMixin.get_centroids_of_hue(fn, ADDED_PARTS_HSV_HUE, area_thr=750, dim_thr=50)

    def render_masked_image(self, **kwargs):
        path = kwargs["output_path"]
        for fn, name in self.masked_filenames:
            fn = normalize_filename(fn, path)
            self._render_maskable_image(fn, MASKED_OUT_COLOUR, name, **kwargs)
            # centroids = ImageMixin.get_centroids_of_hue(fn, ADDED_PARTS_HSV_HUE, area_thr=750, dim_thr=50)

    def model_filename(self, suffix=None):
        """Returns a unique representative filename for the step model image.
        The filename is based on attributes such as resolution, scale and hash code."""
        suffix = suffix if suffix is not None else ""
        return "%d%s_%d_%d_%.2f_%s.png" % (
            self.idx,
            suffix,
            self.level,
            self.dpi,
            self.scale,
            self.sha1_hash,
        )

    def _maskable_filenames(self, suffix):
        """Returns one or more filenames for maskable elements.
        One filename is returned if no sub-models are added in this step
        If there are sub-models, additional filenames are returned,
        as tuples (filename, sub-model name); one for each unique sub-model."""
        file_list = [(self.model_filename(suffix=suffix), None)]
        for sub_model, _ in self.sub_models.items():
            name = strip_part_ext(sub_model)
            file_list.append(
                (self.model_filename(suffix="%s-%s" % (suffix, name)), name)
            )
        return file_list

    @property
    def masked_filenames(self):
        """Returns one or more filenames for masked elements."""
        return self._maskable_filenames("m")

    @property
    def unmasked_filenames(self):
        """Returns one or more filenames for unmasked elements."""
        return self._maskable_filenames("u")

    @property
    def outline_filename(self):
        return self.model_filename(suffix="o")

    def render_parts_images(self, **kwargs):
        """Renders images of the parts used in this step."""
        if "dpi" in kwargs:
            kwargs["dpi"] = self.dpi
        for part in self.step_parts:
            part.render_image(**kwargs)

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
            if not obj.matched_name(only_submodel):
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
