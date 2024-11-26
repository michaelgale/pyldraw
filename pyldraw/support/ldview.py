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
# LDView external renderer support

import os, tempfile
import datetime
import subprocess, shlex

from .imgutils import ImageMixin


LDVIEW_BIN = "/Applications/LDView.app/Contents/MacOS/LDView"
LDVIEW_DICT = {
    "DefaultMatrix": "1,0,0,0,1,0,0,0,1",
    "SnapshotSuffix": ".png",
    "BlackHighlights": 0,
    "ProcessLDConfig": 1,
    "EdgeThickness": 3,
    "EdgesOnly": 0,
    "ShowHighlightLines": 1,
    "ConditionalHighlights": 1,
    "SaveZoomToFit": 0,
    "SubduedLighting": 1,
    "UseSpecular": 1,
    "UseFlatShading": 0,
    "LightVector": "0,1,1",
    "AllowPrimitiveSubstitution": 0,
    "HiResPrimitives": 1,
    "UseQualityLighting": 1,
    "ShowAxes": 0,
    "UseQualityStuds": 1,
    "TextureStuds": 0,
    "SaveActualSize": 0,
    "SaveAlpha": 1,
    "AutoCrop": 0,
    "LineSmoothing": 1,
    "Texmaps": 1,
    "MemoryUsage": 2,
    "MultiThreaded": 1,
}

SNAPSHOT_DICT = [
    "page_width",
    "page_height",
    "auto_crop",
    "no_lines",
    "wireframe",
    "quality_lighting",
    "scale",
    "log_output",
    "log_level",
    "overwrite",
    "texmaps",
    "flat_shading",
    "specular",
]

# 10.0 / tan(0.005 deg)
LDU_DISTANCE = 114591


def camera_distance(scale=1.0, dpi=300, page_width=8.5):
    one = 20 * 1 / 64 * dpi * scale
    sz = page_width * dpi / one * LDU_DISTANCE * 0.775
    sz *= 1700 / 1000
    return sz


def _coord_str(x, y=None, sep=", "):
    if isinstance(x, (tuple, list)):
        a, b = float(x[0]), float(x[1])
    else:
        a, b = float(x), float(y)
    sa = ("%f" % (a)).rstrip("0").rstrip(".")
    sb = ("%f" % (b)).rstrip("0").rstrip(".")
    s = []
    s.append(str("%s" % (sa)))
    s.append(sep)
    s.append(str("%s" % (sb)))
    return "".join(s)


class LDViewRender:
    """LDView render session helper class."""

    def __init__(self, **kwargs):
        self.dpi = 300
        self.page_width = 8.5
        self.page_height = 11.0
        self.auto_crop = True
        self.no_lines = False
        self.wireframe = False
        self.quality_lighting = True
        self.flat_shading = False
        self.specular = True
        self.line_thickness = 3
        self.texmaps = True
        self.scale = 1.0
        self.output_path = None
        self.log_output = False
        self.log_level = 0
        self.overwrite = False
        self.tmp_path = tempfile.gettempdir() + os.sep + "temp.ldr"
        self.settings_snapshot = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __str__(self):
        s = []
        s.append("LDViewRender: ")
        s.append(" DPI: %d  Scale: %.2f" % (self.dpi, self.scale))
        s.append(
            " Page size: %s in (%s pixels)"
            % (
                _coord_str(self.page_width, self.page_height, " x "),
                _coord_str(self.pix_width, self.pix_height, " x "),
            )
        )
        s.append(" Auto crop: %s" % (self.auto_crop))
        s.append(" Camera distance: %d" % (self.cam_dist))
        return "\n".join(s)

    def snapshot_settings(self):
        self.settings_snapshot = {}
        for key in SNAPSHOT_DICT:
            self.settings_snapshot[key] = self.__dict__[key]

    def restore_settings(self):
        if self.settings_snapshot is None:
            return
        for key in SNAPSHOT_DICT:
            self.__dict__[key] = self.settings_snapshot[key]

    def lofi_settings(self):
        self.no_lines = True
        self.quality_lighting = False
        self.flat_shading = True
        self.texmaps = False
        self.specular = False

    @property
    def pix_width(self):
        return self.page_width * self.dpi

    @property
    def pix_height(self):
        return self.page_height * self.dpi

    @property
    def cam_dist(self):
        return int(camera_distance(self.scale, self.dpi, self.page_width))

    @property
    def args_cam(self):
        return "-ca0.01 -cg0.0,0.0,%d" % (self.cam_dist)

    @property
    def args_size(self):
        return "-SaveWidth=%d -SaveHeight=%d" % (
            self.pix_width,
            self.pix_height,
        )

    def set_page_size(self, width, height):
        self.page_width = width
        self.page_height = height

    def set_dpi(self, dpi):
        self.dpi = dpi

    def set_scale(self, scale):
        self.scale = scale

    def _logoutput(self, msg, tstart=None, level=2):
        if level <= self.log_level:
            print("%s: %s" % (tstart, msg))

    def render_from_str(self, ldrstr, outfile):
        """Render from a LDraw text string."""
        if self.log_output:
            s = ldrstr.splitlines()[0]
            self._logoutput("rendering string (%s)..." % (s[: min(len(s), 80)]))
        with open(self.tmp_path, "w") as f:
            f.write(ldrstr)
        self.render_from_file(self.tmp_path, outfile)

    def render_from_parts(self, parts, outfile):
        """Render using a list of LdrPart objects."""
        if self.log_output:
            self._logoutput("rendering parts (%s)..." % (len(parts)))
        ldrstr = "\n".join([str(p) for p in parts])
        self.render_from_str(ldrstr, outfile)

    def render_from_file(self, ldrfile, outfile):
        """Render from an LDraw file."""
        tstart = datetime.datetime.now()
        if self.output_path is not None:
            path, _ = os.path.split(outfile)
            oppath = os.path.normpath(self.output_path)
            if not oppath in path:
                filename = os.path.normpath(self.output_path + os.sep + outfile)
            else:
                filename = outfile
        else:
            filename = os.path.normpath(outfile)
        _, fno = os.path.split(filename)
        if not self.overwrite and os.path.isfile(os.path.normpath(filename)):
            if self.log_output:
                _, fno = os.path.split(filename)
                self._logoutput(
                    "rendered file %s already exists, skipping" % fno, tstart
                )
            return
        ldv = []
        ldv.append(LDVIEW_BIN)
        ldv.append("-SaveSnapShot=%s" % filename)
        ldv.append(self.args_size)
        ldv.append(self.args_cam)
        for key, value in LDVIEW_DICT.items():
            if key == "EdgeThickness":
                value = self.line_thickness
            elif key == "UseQualityLighting":
                value = 1 if self.quality_lighting else 0
            elif key == "Texmaps":
                value = 1 if self.texmaps else 0
            elif key == "UseFlatShading":
                value = 1 if self.flat_shading else 0
            elif key == "UseSpecular":
                value = 1 if self.specular else 0
            if self.no_lines:
                if key == "EdgeThickness":
                    value = 0
                elif key == "ShowHighlightLines":
                    value = 0
                elif key == "ConditionalHighlights":
                    value = 0
                elif key == "UseQualityStuds":
                    value = 0
            if self.wireframe:
                if key == "EdgesOnly":
                    value = 1
            ldv.append("-%s=%s" % (key, value))
        ldv.append(ldrfile)
        s = " ".join(ldv)
        args = shlex.split(s)
        subprocess.Popen(args).wait()
        if self.log_output:
            _, fni = os.path.split(ldrfile)
            _, fno = os.path.split(filename)
            self._logoutput("rendered file %s to %s..." % (fni, fno), tstart, level=0)

        if self.auto_crop:
            self.crop(filename)

    def crop(self, filename):
        """Crop image file."""
        tstart = datetime.datetime.now()
        img = ImageMixin.crop_to_content(filename)
        ImageMixin.save_image(filename, img)
        if self.log_output:
            _, fn = os.path.split(filename)
            self._logoutput(
                "> cropped %s to %s x %s" % (fn, img.shape[1], img.shape[0]), tstart
            )
