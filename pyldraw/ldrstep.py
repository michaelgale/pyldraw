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

from pyldraw.support.imgutils import ImageMixin
from .geometry import Vector, Matrix, safe_vector, BoundBox
from .helpers import normalize_filename, strip_part_ext, quantize, vector_str
from pyldraw import *


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
        self._delimited = None

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

    @property
    def delimited_objs(self):
        """Captures objects in a step which are between BEGIN/END delimiters.
        This can be useful for extracting objects which are marked for
        exclusion in a parts list, or objects added by LSYNTH, etc.
        A list of dictionaries is returned with the dictionary containing
        keys for the LDraw line that triggered the capture and a list of parts
        associated with the capture."""
        if not self._delimited is None:
            return self._delimited
        delimited = []
        group = {}
        is_captured = False
        # if we're a BuildStep then we need to use our post-processed objects
        # stored in 'step_objs' rather than the raw objects stored in 'objs'
        if isinstance(self, BuildStep):
            objs = self.step_objs
        else:
            objs = self.objs
        for o in objs:
            if isinstance(o, LdrMeta):
                if o.has_start_tag_capture:
                    continue
                if o.has_start_capture_meta and not is_captured:
                    is_captured = True
                    group["trigger"] = o
                    group["objs"] = []
                elif o.has_end_capture_meta and is_captured:
                    delimited.append(group)
                    group = {}
                    is_captured = False
            elif is_captured:
                if o.is_drawable:
                    group["objs"].append(o)
        for d in delimited:
            if d["trigger"].is_arrow_capture:
                o = d["trigger"]
                d["offset"] = LdrArrow.mean_offset_from_meta(o)
        self._delimited = delimited
        return self._delimited

    def iter_meta_objs(self, ignore_delimiters=False):
        """Generator which iterates over step objects which represent meta commands"""
        for o in self.objs:
            if isinstance(o, LdrMeta):
                if ignore_delimiters:
                    if not o.is_delimiter:
                        yield o
                else:
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

    @property
    def new_scale(self):
        return self.step_has_meta_command()

    @property
    def column_break(self):
        return self.step_has_meta_command()

    @property
    def page_break(self):
        return self.step_has_meta_command()

    @property
    def hide_pli(self):
        return self.step_has_meta_command()

    @property
    def hide_fullscale(self):
        return self.step_has_meta_command()

    @property
    def hide_preview(self):
        return self.step_has_meta_command()

    @property
    def hide_rotation_icon(self):
        return self.step_has_meta_command()

    @property
    def hide_page_num(self):
        return self.step_has_meta_command()

    @property
    def show_page_num(self):
        return self.step_has_meta_command()

    @property
    def new_page_num(self):
        return self.step_has_meta_command()

    @property
    def no_callout(self):
        return self.step_has_meta_command()


class BuildStep(LdrStep):
    """BuildStep is a richer representation of LdrStep with additional data to
    represent a building step in an instruction sequence. It also stores
    unwrapped object representations of the objects added at this step as well
    as the total model representation at this step."""

    def __init__(self, objs=None, **kwargs):
        super().__init__(objs, **kwargs)
        self.scale = 1.0
        self.aspect = Vector(0, 0, 0)
        self.pos = Vector(0, 0, 0)
        self.idx = None
        self.num = 1
        self.level = None
        self.qty = 1
        self.model_name = None
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
        # bounding boxes for overall model and parts added this step
        self._model_bound_box = None
        self._step_bound_box = None
        # default path for images
        self._default_img_path = None

    def __repr__(self) -> str:
        return "%s(%d step objects)" % (self.__class__.__name__, len(self.step_objs))

    def __rich__(self):
        return str(self)

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
            "Step: %3d %3d%s level %1d%s%s step-parts: %3d model-parts: %4d scale %.2f aspect %-11s qty: %d '%s'"
            % (
                self.idx,
                self.num,
                indent,
                self.level,
                postdent,
                model_state,
                len(self.step_parts),
                len(self.model_parts),
                self.scale,
                vector_str(self.aspect),
                self.qty,
                strip_part_ext(self.model_name),
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
        # reset containers
        self._step_objs = None
        self._model_objs = None
        self._delimited = None
        # apply new aspect angles and scale
        if self.rotation_relative:
            self.aspect += self.rotation_relative
        elif self.rotation_absolute:
            self.aspect = self.rotation_absolute
        elif self.new_scale:
            self.scale = self.new_scale
        aspect = Vector(self.aspect)
        # unwrap the objects from sub-model hierarchy
        name = strip_part_ext(self.model_name) if self.model_name is not None else None
        objs = recursive_unwrap_model(self, sub_models, path=name)
        self._step_objs = [o.rotated_by(aspect) for o in objs]
        if model_objs is not None:
            objs = recursive_unwrap_model(
                self, sub_models, objects=model_objs, path=name
            )
            self._model_objs = [o.rotated_by(aspect) for o in objs]

    @property
    def step_objs(self):
        """Returns a list of LdrObj representing new objects added at this step."""
        return self._step_objs

    @property
    def model_objs(self):
        """Returns a list of all LdrObj representing the total model"""
        return self._model_objs

    @property
    def is_virtual(self):
        """Returns true if this step just contains meta lines and no added parts to the model."""
        return len(self.step_parts) == 0

    def _modified_objs(self, only_for_step=True):
        """Ensures objects that captured between delimiter meta lines are modified
        as applicable, e.g. translated, hidden, etc."""
        if only_for_step:
            objs = filter_objs(self.step_objs, is_drawable=True)
        else:
            objs = filter_objs(self.model_objs, is_drawable=True)
        mod_objs = []

        for d in self.delimited_objs:
            for obj in d["objs"]:
                # if obj is a sub-model part, then use the path to filter objects
                # otherwise, simply use the sha1_hash attribute
                if isinstance(obj, LdrPart) and obj.is_model:
                    del_objs = filter_objs(objs, path=obj.path)
                else:
                    del_objs = filter_objs(objs, sha1_hash=obj.sha1_hash)
                if d["trigger"].is_arrow_capture:
                    offset = (
                        Vector(d["offset"])
                        * Matrix.euler_to_rot_matrix(self.aspect).transpose()
                    )
                    sh_objs = [o.translated(offset) for o in del_objs]
                    mod_objs.extend(self.arrows_for_offset(d["trigger"], sh_objs))
                    mod_objs.extend(sh_objs)
                objs = obj_difference(objs, del_objs)
            if d["trigger"].is_hide_part_capture:
                objs = obj_difference(objs, del_objs)
        return obj_union(objs, mod_objs)

    def arrows_for_offset(self, meta, objs):
        if len(objs) > 0:
            bb = self.bound_box(objs)
            arrows = LdrArrow.objs_from_meta(meta, aspect=self.aspect, origin=bb.centre)
            return [o.rotated_by(self.aspect) for o in arrows]
        else:
            return []

    @property
    def step_parts(self):
        """Returns a list of LdrPart objects representing the new parts added at this step"""
        return self._modified_objs(only_for_step=True)

    @property
    def model_parts(self):
        """Returns a list of LdrPart objects representing the total model at this step."""
        return self._modified_objs(only_for_step=False)

    @property
    def pli_parts(self):
        """Returns a dictionary part keys and quantities representing the PLI for this step."""
        pli = Counter()
        for o in self.step_parts:
            if o.part_key is not None:
                pli.update([o.part_key])
        for d in self.delimited_objs:
            if d["trigger"].is_hide_pli_capture:
                for o in d["objs"]:
                    if o.part_key is not None:
                        if o.part_key in pli:
                            pli.pop(o.part_key)
        pli = pli.most_common()
        return dict(pli)

    def bound_box(self, parts):
        """Returns the bounding box of the model at this step."""
        from .ldrmodel import LdrModel

        rot = Matrix.euler_to_rot_matrix(Vector(self.aspect))
        bb = BoundBox()
        for o in parts:
            if isinstance(o, LdrPart):
                m = LdrModel.from_part(o.name)
                pos = Vector(o.pos) * rot
                bb = bb.union(m.bound_box.translated(pos))
            else:
                pts = [Vector(pt) * rot for pt in o.points]
                bb = bb.union(BoundBox.from_pts(pts))
        return bb

    @property
    def step_bound_box(self):
        if self._step_bound_box is None:
            self._step_bound_box = self.bound_box(self.step_parts)
        return self._step_bound_box

    @property
    def model_bound_box(self):
        if self._model_bound_box is None:
            self._model_bound_box = self.bound_box(self.model_parts)
        return self._model_bound_box

    def render_model(self, **kwargs):
        """Renders an image of the model for this step."""
        path = self._get_path_from_dict(kwargs)
        fn = normalize_filename(self.model_filename(), path)
        ldv = LDViewRender(**kwargs)
        ldv.set_scale(self.scale)
        ldv.render_from_parts(self.model_parts, fn)
        img = ImageMixin.pad_image(fn, self.outline_width)
        ImageMixin.save_image(fn, img)
        self._remember_render_settings_from_dict(kwargs)

    def _get_path_from_dict(self, d):
        path = None
        if "output_path" in d:
            path = d["output_path"]
        else:
            if self._default_img_path is not None:
                path = self._default_img_path
        return path

    def _remember_render_settings_from_dict(self, d):
        if "output_path" in d:
            self._default_img_path = d["output_path"]
        if "dpi" in d:
            self.dpi = d["dpi"]

    def render_outline_image(self, **kwargs):
        """Renders the model image with outlines drawn around new parts"""
        path = self._get_path_from_dict(kwargs)
        unmasked = normalize_filename(self.masked_filenames[0][0], path)
        model = normalize_filename(self.model_filename(), path)
        outline = normalize_filename(self.outline_filename, path)
        mask_colour = LdrColour.ADDED_MASK()
        img = ImageMixin.merge_with_outlines(
            model,
            mask_colour.hue,
            unmasked,
            self.outline_colour.bgr,
            self.outline_width,
        )
        ImageMixin.save_image(outline, img)
        self._remember_render_settings_from_dict(kwargs)

    def _render_maskable_image(self, fn, mask_colour, submodel=None, **kwargs):
        add_colour = LdrColour.ADDED_MASK()
        step_parts = filter_objs(self.step_parts, path=submodel)
        prev_parts = obj_difference(self.model_parts, step_parts)
        prev_parts = obj_change_colour(prev_parts, mask_colour)
        new_parts = obj_change_colour(step_parts, add_colour, path=submodel)
        parts = [LdrMeta.from_colour(mask_colour), LdrMeta.from_colour(add_colour)]
        parts.extend(obj_union(prev_parts, new_parts))
        parts = exclude_objs(parts, path="arrow")
        ldv = LDViewRender(**kwargs)
        ldv.set_scale(self.scale)
        ldv.lofi_settings()
        ldv.render_from_parts(parts, fn)
        img = ImageMixin.pad_image(fn, self.outline_width)
        ImageMixin.save_image(fn, img)
        self._remember_render_settings_from_dict(kwargs)

    def render_unmasked_image(self, **kwargs):
        """Renders the model image with all new parts in ADDED_PARTS_COLOUR and
        all other parts in a transparent CLEAR_MASK_CODE colour"""
        path = self._get_path_from_dict(kwargs)
        for fn, name in self.unmasked_filenames:
            fn = normalize_filename(fn, path)
            self._render_maskable_image(fn, LdrColour.CLEAR_MASK(), name, **kwargs)
            # centroids = ImageMixin.get_centroids_of_hue(fn, ADDED_PARTS_HSV_HUE, area_thr=750, dim_thr=50)

    def render_masked_image(self, **kwargs):
        """Renders the model image with all new parts in ADDED_PARTS_COLOUR and
        all other parts in an opaque OPAQUE_MASK_CODE colour"""
        path = self._get_path_from_dict(kwargs)
        for fn, name in self.masked_filenames:
            fn = normalize_filename(fn, path)
            self._render_maskable_image(fn, LdrColour.OPAQUE_MASK(), name, **kwargs)
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
        self._remember_render_settings_from_dict(kwargs)
        for part in self.step_parts:
            if isinstance(part, LdrPart):
                part.render_image(**kwargs)


def assign_part_path(p, name=None, path_names=None):
    """Assigns a unique path for a part in a sub-model taking into account multiple
    instances of a sub-model"""
    if p is None:
        return "root"
    if name is None:
        return p

    name = strip_part_ext(name)
    next_ref = name + ":0"
    for pn in path_names:
        levels = pn.split("/")
        if len(levels) > 1:
            last = levels[-1]
            x = last.split(":")
            if len(x) == 2:
                if name == x[0]:
                    next_ref = name + ":" + str(int(x[1]) + 1)
                    break
    p = p + "/" + next_ref
    return p


def demote_path(p):
    """Strips the last item from a path to next level up in the hierarchy"""
    paths = p.split("/")
    if len(paths) > 1:
        return p.replace(paths[-1], "").rstrip("/")
    return p


def recursive_unwrap_model(
    model,
    submodels,
    objects=None,
    offset=None,
    matrix=None,
    only_submodel=None,
    path=None,
    path_names=None,
):
    """Recursively parses an LDraw model plus any sub-models and
    populates an object list representing that model.  To support selective
    parsing of only one submodel, only_submodel can be set to the desired
    submodel name."""
    o = offset if offset is not None else Vector(0, 0, 0)
    m = matrix if matrix is not None else Matrix.identity()
    all_paths = path_names if path_names is not None else []
    p = assign_part_path(path, path_names=all_paths)

    if objects is None:
        objects = []
    for obj in model.iter_objs():
        if only_submodel is not None:
            if not obj.matched_name(only_submodel):
                continue
        if obj.model_part_name in submodels:
            submodel = submodels[obj.model_part_name]
            new_matrix = m * obj.matrix
            new_loc = m * obj.pos + o
            p = assign_part_path(p, obj.model_part_name, path_names=all_paths)
            obj.path = p
            all_paths.append(p)
            objects = recursive_unwrap_model(
                submodel,
                submodels,
                objects,
                offset=new_loc,
                matrix=new_matrix,
                path=p,
                path_names=all_paths,
            )
            p = demote_path(p)
        else:
            if only_submodel is None:
                new_obj = obj.transformed(matrix=m, offset=o)
                new_obj.path = p
                objects.append(new_obj)
    return objects
