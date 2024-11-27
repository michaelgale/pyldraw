# LdrObj tests
import os.path

from rich import print
from pyldraw import *

IMG_PATH = "./tests/outimages/"

LDV_ARGS = {
    "overwrite": False,
    "dpi": 300,
    "auto_crop": False,
    "output_path": IMG_PATH,
    "log_output": False,
    "log_level": 0,
}

LDV_ASPECT = (-35, -35, 0)
AXIS_LINES = [
    LdrLine(colour=804, point1=(0, 0, 0), point2=(200, 0, 0)),
    LdrLine(colour=802, point1=(0, 0, 0), point2=(0, 200, 0)),
    LdrLine(colour=801, point1=(0, 0, 0), point2=(0, 0, 200)),
]
ARROW_LEN = 80
TEST_RENDER_ALL_ARROWS = False


def test_arrow_init():
    a1 = LdrArrow(colour=4, tail_pos=(0, 50, 0))
    assert a1.length == 50
    assert a1.direction.almost_same_as((0, 1, 0))


def _ldv_objs(arrow):
    objs = []
    p = LdrPart(name="3023.dat", colour=3, pos=(0, 1, 0))
    p = p.rotated_by(LDV_ASPECT)
    objs.extend([p])
    objs.extend([o.rotated_by(LDV_ASPECT) for o in AXIS_LINES])
    objs.extend([o.rotated_by(LDV_ASPECT) for o in arrow.arrow_objs()])
    return objs


def test_meta():
    s = "0 !PY ARROW BEGIN COLOUR 1 TILT -30 LENGTH 80 RATIO 0.5 -30 -100 0 30 -100 0"
    m = LdrMeta.from_str(s)
    a0 = LdrArrow.objs_from_meta(m, aspect=LDV_ASPECT)
    ldv = LDViewRender(**LDV_ARGS)
    ldv.render_from_parts(a0, "arrow-meta.png")

    s = "0 !PY ARROW BEGIN COLOUR 1 -30 -100 0 30 -100 0"
    o = LdrArrow.mean_offset_from_meta(LdrMeta.from_str(s))
    assert o.almost_same_as((0, -100, 0))

    s = "0 !PY ARROW BEGIN COLOUR 1 -50 0 10  -50 0 -10  -50 0 20  -50 0 -20"
    l0 = LdrArrow.offset_list_from_meta(LdrMeta.from_str(s))
    assert len(l0) == 4
    o = LdrArrow.mean_offset_from_meta(LdrMeta.from_str(s))
    assert o.almost_same_as((-50, 0, 0))


def test_render():
    ldv = LDViewRender(**LDV_ARGS)

    a1 = LdrArrow(colour=802, tail_pos=(0, -ARROW_LEN, 0))
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-yn.png")
    assert os.path.isfile(IMG_PATH + "arrow-yn.png")

    a1 = LdrArrow(colour=802, tail_pos=(0, ARROW_LEN, 0))
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-yp.png")
    assert os.path.isfile(IMG_PATH + "arrow-yp.png")

    a1 = LdrArrow(colour=804, tail_pos=(-ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-xn.png")
    assert os.path.isfile(IMG_PATH + "arrow-xn.png")

    a1 = LdrArrow(colour=801, tail_pos=(0, 0, -ARROW_LEN))
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-zn.png")
    assert os.path.isfile(IMG_PATH + "arrow-zn.png")

    a1 = LdrArrow(colour=801, tail_pos=(0, 0, ARROW_LEN))
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-zp.png")
    assert os.path.isfile(IMG_PATH + "arrow-zp.png")

    if not TEST_RENDER_ALL_ARROWS:
        return

    a1 = LdrArrow(colour=802, tail_pos=(0, -ARROW_LEN, 0), tilt=55)
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    assert a1.tilt == 55
    ldv.render_from_parts(_ldv_objs(a1), "arrow-yn55.png")
    assert os.path.isfile(IMG_PATH + "arrow-yn55.png")

    a1 = LdrArrow(colour=802, tail_pos=(0, -ARROW_LEN, 0), tilt=-55)
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    assert a1.tilt == -55
    ldv.render_from_parts(_ldv_objs(a1), "arrow-yn-55.png")
    assert os.path.isfile(IMG_PATH + "arrow-yn-55.png")

    a1 = LdrArrow(colour=802, tail_pos=(0, -ARROW_LEN, 0), ratio=0.25)
    a1.aspect = LDV_ASPECT
    assert a1.ratio == 0.25
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-ynr.png")
    assert os.path.isfile(IMG_PATH + "arrow-ynr.png")

    a1 = LdrArrow(tail_pos=(-1.25 * ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    a1.dash_style()
    ldv.render_from_parts(_ldv_objs(a1), "arrow-dash1.png")
    assert os.path.isfile(IMG_PATH + "arrow-dash1.png")
    a1 = LdrArrow(tail_pos=(-1.5 * ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    a1.dash_style()
    ldv.render_from_parts(_ldv_objs(a1), "arrow-dash2.png")
    assert os.path.isfile(IMG_PATH + "arrow-dash2.png")
    a1 = LdrArrow(tail_pos=(-1.75 * ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    a1.dash_style()
    ldv.render_from_parts(_ldv_objs(a1), "arrow-dash3.png")
    assert os.path.isfile(IMG_PATH + "arrow-dash3.png")

    a1 = LdrArrow(colour=804, tail_pos=(ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-xp.png")
    assert os.path.isfile(IMG_PATH + "arrow-xp.png")

    a1 = LdrArrow(colour=804, tail_pos=(ARROW_LEN, 0, 0), tilt=-45, ratio=0.5)
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-xprt.png")
    assert os.path.isfile(IMG_PATH + "arrow-xprt.png")

    a1 = LdrArrow(colour=804, tail_pos=(ARROW_LEN, 0, 0), ratio=0.5)
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-xpr.png")
    assert os.path.isfile(IMG_PATH + "arrow-xpr.png")
