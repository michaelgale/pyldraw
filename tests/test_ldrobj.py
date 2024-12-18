# LdrObj tests
import pytest

from rich import print
from pyldraw import *
from pyldraw.geometry import BoundBox


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


def test_ldrobj_init():
    o1 = LdrObj()
    assert o1 is not None
    p1 = LdrPart(name="3001.dat", colour=15, aspect=(30, 55, 0))
    assert p1.name == "3001.dat"
    assert p1.colour.code == 15
    assert p1.colour.hex_code == "#FFFFFF"
    assert p1.pos.almost_same_as((0, 0, 0))

    with pytest.raises(ValueError):
        obj = LdrObj.from_str([1, 2, 3])

    with pytest.raises(ValueError):
        obj = LdrMeta.from_str([1, 2, 3])


def test_ldrcomment():
    o1 = LdrComment(text="// this is a comment")
    assert isinstance(o1, LdrComment)
    assert o1.text == "// this is a comment"
    o1 = LdrObj.from_str("0 // this is a comment")
    assert isinstance(o1, LdrComment)
    assert o1.text == "// this is a comment"


def test_ldrmeta():
    o1 = LdrObj.from_str("0 !META param1 param2")
    assert isinstance(o1, LdrMeta)
    o2 = LdrObj.from_str("0 ROTSTEP 30 50 25 ABS")
    assert isinstance(o2, LdrMeta)
    assert o2.rotation_absolute.almost_same_as((30, 50, 25))
    o3 = LdrObj.from_str("0 FILE MyModel.ldr")
    assert isinstance(o3, LdrMeta)
    o3 = LdrObj.from_str("0 NOFILE")
    assert isinstance(o3, LdrMeta)
    obj = LdrObj.from_str("0 !PY ROT FLIPY")
    assert isinstance(obj, LdrMeta)
    assert "FLIPY" in obj.parameters["flags"]
    assert obj.rotation_relative == (0, 180, 0)
    o1 = LdrObj.from_str("0 PLI BEGIN IGN")
    assert isinstance(o1, LdrMeta)
    o1 = LdrObj.from_str("0 PLI BEGIN")
    assert not isinstance(o1, LdrMeta)
    o1 = LdrObj.from_str("0 !PLI BEGIN IGN")
    assert isinstance(o1, LdrMeta)


def test_ldr_py_meta():
    obj = LdrObj.from_str("0 !PY SCALE 0.55")
    assert isinstance(obj, LdrMeta)
    assert "scale" in obj.parameters
    assert obj.new_scale == 0.55

    obj = LdrObj.from_str("0 !PY COL_BREAK")
    assert isinstance(obj, LdrMeta)
    assert obj.column_break
    assert obj.page_break is None

    obj = LdrObj.from_str("0 !PY PAGE_BREAK")
    assert isinstance(obj, LdrMeta)
    assert obj.page_break
    assert obj.column_break is None

    obj = LdrObj.from_str("0 !PY HIDE_PLI")
    assert isinstance(obj, LdrMeta)
    assert obj.hide_pli

    obj = LdrObj.from_str("0 !PY HIDE_FULLSCALE")
    assert isinstance(obj, LdrMeta)
    assert obj.hide_fullscale

    obj = LdrObj.from_str("0 !PY HIDE_PREVIEW")
    assert isinstance(obj, LdrMeta)
    assert obj.hide_preview

    obj = LdrObj.from_str("0 !PY HIDE_ROTICON")
    assert isinstance(obj, LdrMeta)
    assert obj.hide_rotation_icon

    obj = LdrObj.from_str("0 !PY HIDE_PAGE_NUM")
    assert isinstance(obj, LdrMeta)
    assert obj.hide_page_num

    obj = LdrObj.from_str("0 !PY SHOW_PAGE_NUM")
    assert isinstance(obj, LdrMeta)
    assert obj.show_page_num

    obj = LdrObj.from_str("0 !PY NO_CALLOUT")
    assert isinstance(obj, LdrMeta)
    assert obj.no_callout

    obj = LdrObj.from_str("0 !PY NEW_PAGE_NUM 3")
    assert isinstance(obj, LdrMeta)
    assert "number" in obj.parameters
    assert obj.new_page_num == 3


def test_ldrline():
    o1 = LdrObj.from_str("2 71 1 2 3 4 5 6")
    assert isinstance(o1, LdrLine)
    assert len(o1.points) == 2
    assert o1.colour.code == 71
    assert o1.colour.name_slug == "light-bluish-gray"


def test_ldrtriangle():
    o1 = LdrObj.from_str("3 14 2 4 6 1 3 5 9 8 7")
    assert isinstance(o1, LdrTriangle)
    assert len(o1.points) == 3


def test_ldrquad():
    o1 = LdrObj.from_str("4 1 0 2 4 5 6 7 5 9 8 0 2 3")
    assert isinstance(o1, LdrQuad)
    assert len(o1.points) == 4
    o3 = o1.transformed(offset=(-1, 2, -3))
    assert o3.points[0].almost_same_as((-1, 4, 1))
    assert o3.points[1].almost_same_as((4, 8, 4))
    assert o3.points[2].almost_same_as((4, 11, 5))
    assert o3.points[3] == (-1, 4, 0)


def test_ldrpart():
    o1 = LdrObj.from_str("1 4 5 10 20 1 0 0 0 1 0 0 0 -1 3001.dat")
    assert isinstance(o1, LdrPart)
    assert o1.is_part
    assert o1.description == "Brick 2 x 4"
    assert o1.colour.code == 4
    o1 = LdrObj.from_str("1 4 10 -50 20 -1 0 0 0 -1 0 0 0 -1 This Submodel 1.ldr")
    assert isinstance(o1, LdrPart)
    assert o1.is_model
    o3 = o1.transformed(offset=(-1, 2, -3))
    assert o3.pos == (9, -48, 17)


def test_find_parts():
    m1 = LdrModel.from_part("3001.dat")
    s1 = m1.steps[0]
    s1.objs = [o.rotated_by((0, 90, 0)) for o in s1.objs]
    prims = [o for o in m1.iter_primitives()]
    assert len(prims) == 886
    bb = m1.bound_box
    assert abs(bb.xlen - 40) < 1e-3
    assert abs(bb.ylen - 28) < 1e-3
    assert abs(bb.zlen - 80) < 1e-3
    prims = [p.rotated_by(LDV_ASPECT) for p in m1.iter_primitives()]
    ldv = LDViewRender(**LDV_ARGS)
    fn = m1.name + ".png"
    ldv.render_from_parts(prims, fn)
    assert os.path.isfile(IMG_PATH + fn)


def test_primitive_orientation():
    p1 = LdrPart().from_str("1 4 0 0 0 0 0 1 0 1 0 1 0 0 3001.dat")
    m1 = LdrModel.from_ldrpart(p1)
    prims = [o for o in m1.iter_primitives()]
    assert len(prims) == 886
    bb = m1.bound_box
    assert abs(bb.xlen - 40) < 1e-3
    assert abs(bb.ylen - 28) < 1e-3
    assert abs(bb.zlen - 80) < 1e-3
    prims = [p.rotated_by(LDV_ASPECT) for p in m1.iter_primitives()]
    ldv = LDViewRender(**LDV_ARGS)
    fn = m1.name + "_rot.png"
    ldv.render_from_parts(prims, fn)
    assert os.path.isfile(IMG_PATH + fn)


from pyldraw.geometry import Vector, Matrix


def test_norm_rot():
    p = LdrPart.from_str(
        "1 4 34.3976 -143.398 -11.3938 0.5736 0 0.8192 0.4698 0.8192 -0.329 -0.671 0.5736 0.4698 3010.dat"
    )
    n = LdrPart.from_str("1 4 -40 -124 70 1 0 0 0 1 0 0 0 1 3010.dat")
    a = Vector(-35.0, 55.0, 0.0)
    rot = Matrix.euler_to_rot_matrix(a)
    p1 = n.transformed(matrix=rot)
    assert p1 == p

    p2 = p.rotation_removed(a)
    assert p2 == n
