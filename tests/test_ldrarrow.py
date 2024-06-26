# LdrObj tests

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


def test_arrow_init():
    a1 = LdrArrow(colour=4, tail_pos=(0, 50, 0))
    assert a1.length == 50
    assert a1.direction.almost_same_as((0, 1, 0))


def _ldv_objs(arrow):
    objs = []
    p = LdrPart(name="3001.dat", colour=3, pos=(0, 1, 0))
    p = p.rotated_by(LDV_ASPECT)
    objs.extend([p])
    objs.extend([o.rotated_by(LDV_ASPECT) for o in AXIS_LINES])
    objs.extend([o.rotated_by(LDV_ASPECT) for o in arrow.arrow_objs()])
    return objs


def test_render():
    ldv = LDViewRender(**LDV_ARGS)

    a1 = LdrArrow(colour=802, tail_pos=(0, -ARROW_LEN, 0))
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-yn.png")

    a1 = LdrArrow(colour=802, tail_pos=(0, ARROW_LEN, 0))
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-yp.png")

    a1 = LdrArrow(colour=804, tail_pos=(-ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-xn.png")

    a1 = LdrArrow(colour=804, tail_pos=(ARROW_LEN, 0, 0))
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-xp.png")

    a1 = LdrArrow(colour=801, tail_pos=(0, 0, -ARROW_LEN))
    a1.aspect = LDV_ASPECT
    a1.border_colour = LdrColour(15)
    ldv.render_from_parts(_ldv_objs(a1), "arrow-zn.png")

    a1 = LdrArrow(colour=801, tail_pos=(0, 0, ARROW_LEN))
    a1.aspect = LDV_ASPECT
    ldv.render_from_parts(_ldv_objs(a1), "arrow-zp.png")
