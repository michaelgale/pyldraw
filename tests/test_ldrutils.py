# LdrObj tests

from rich import print
from pyldraw import *
from pyldraw.geometry import BoundBox, Vector
from pyldraw.helpers import *

TEST_GROUPA = """
0 FILE submodel1.ldr
0 untitled model
0 Name: submodel1.ldr
0 Author: Michael Gale
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 0 0 -8 0 1 0 0 0 1 0 -0 0 1 3068b.dat
0 STEP
1 70 -30 -8 -30 1 0 0 0 1 0 -0 0 1 2420.dat
1 70 -30 -8 30 -0 0 1 0 1 0 -1 0 -0 2420.dat
1 70 30 -8 30 -1 0 0 0 1 0 -0 0 -1 2420.dat
1 70 30 -8 -30 0 0 -1 0 1 0 1 0 0 2420.dat
0 STEP
1 14 0 -32 30 -1 0 0 0 1 0 -0 0 -1 3010.dat
1 15 0 -32 30 -1 0 0 0 1 0 -0 0 -1 3010.dat
1 71 0 -32 30 -1 0 0 0 1 0 -0 0 -1 3010.dat
0 STEP
0 NOFILE
"""

TEST_GROUPB = """
0 FILE submodel1.ldr
0 untitled model
0 Name: submodel1.ldr
0 Author: Michael Gale
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 0 0 -8 0 1 0 0 0 1 0 -0 0 1 3068b.dat
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 28 20 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 28 40 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
0 STEP
1 70 -30 -8 -30 1 0 0 0 1 0 -0 0 1 2420.dat
1 70 -30 -8 30 -0 0 1 0 1 0 -1 0 -0 2420.dat
1 70 30 -8 30 -1 0 0 0 1 0 -0 0 -1 2420.dat
1 70 30 -8 -30 0 0 -1 0 1 0 1 0 0 2420.dat
0 STEP
1 14 0 -32 30 -1 0 0 0 1 0 -0 0 -1 3010.dat
0 STEP
0 NOFILE
"""

TEST_GROUPC = """
0 FILE submodel3.ldr
0 untitled model
0 Name: submodel3.ldr
0 Author: Michael Gale
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 0 0 -8 0 1 0 0 0 1 0 -0 0 1 3068b.dat
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 28 20 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 28 40 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
0 STEP
1 70 -30 -8 -30 1 0 0 0 1 0 -0 0 1 2420.dat
1 70 -30 -8 30 -0 0 1 0 1 0 -1 0 -0 submodel1.ldr
1 70 30 -8 30 -1 0 0 0 1 0 -0 0 -1 2420.dat
1 70 30 -8 -30 0 0 -1 0 1 0 1 0 0 2420.dat
0 STEP
1 14 0 -32 30 -1 0 0 0 1 0 -0 0 -1 big assembly.mpd
0 STEP
0 NOFILE
"""

MA = LdrModel.from_str(TEST_GROUPA, "GroupA")
for i, s in enumerate(MA.steps):
    if not i % 2 == 0:
        for o in s.objs:
            o.path = "0/groupa"
GA = [o for o in MA.iter_objs()]

MB = LdrModel.from_str(TEST_GROUPB, "GroupB")
GB = [o.new_path("0/groupb") for o in MB.iter_objs()]

MC = LdrModel.from_str(TEST_GROUPC, "GroupC")
GC = [o.new_path("0/groupc") for o in MC.iter_objs()]


def test_filter():
    x = filter_objs(GA, obj_type=LdrMeta)
    assert len(x) == 5

    x = filter_objs(GA, meta_key="STEP")
    assert len(x) == 3

    x = filter_objs(GA, meta_key="FILE")
    assert len(x) == 1

    y = filter_objs(GB, is_part=True)
    assert len(y) == 10

    z = obj_change_colour(GA, 8)
    assert len(z) == 17
    zc = filter_objs(z, is_part=True)
    assert all(o.colour.code == 8 for o in zc)

    z = obj_change_colour(GA, 8, is_part=True)
    assert all(o.colour.code == 8 for o in z if isinstance(o, LdrPart))

    assert sum([1 if o.colour.code == 72 else 0 for o in GB]) == 0
    x = obj_change_colour(GB, 72, colour=28)
    assert sum([1 if o.colour.code == 72 else 0 for o in x]) == 4

    y = filter_objs(GA, path="0/groupa")
    assert len(y) == 5

    y = filter_objs(GA, path="group")
    assert len(y) == 5
    y = filter_objs(GA, path="0/")
    assert len(y) == 5

    z = filter_objs(GA, path="0/groupb")
    assert len(z) == 0

    x = filter_objs(GB, colour=28)
    assert len(x) == 4
    x = filter_objs(GB, colour=28)
    assert len(x) == 4

    x = filter_objs(GB, name="3010.dat")
    assert len(x) == 1

    x = filter_objs(GB, name="3010")
    assert len(x) == 1

    x = obj_rename(GB, new_name="3666.dat", name="3010")
    assert sum([1 if o.part_name == "3666.dat" else 0 for o in x]) == 1
    x = obj_rename(GB, new_name="3666.dat", name="3010", colour=14)
    assert sum([1 if o.part_name == "3666.dat" else 0 for o in x]) == 1
    x = obj_rename(GB, new_name="3666.dat", name="3010", colour=15)
    assert sum([1 if o.part_name == "3666.dat" else 0 for o in x]) == 0

    x = filter_objs(GB, part_key="3010-14")
    assert len(x) == 1
    x = filter_objs(GB, part_key="3010-15")
    assert len(x) == 0

    x = filter_objs(GC, is_model=True)
    assert len(x) == 2
    x = filter_objs(GC, is_model=False)
    assert len(x) == 8

    x = filter_objs(GC, is_part=True)
    assert len(x) == 8
    x = filter_objs(GC, is_part=False)
    assert len(x) == 2


def test_bool_ops():
    x = obj_union(GA, GB)
    assert len(x) == 19

    y = obj_difference(GA, GB)
    assert len(y) == 2

    z = obj_intersect(GA, GB)
    assert len(z) == 15

    x = obj_exclusive(GA, GB)
    assert len(x) == 4

    x = filter_objs(GA, path="0/groupa")
    y = obj_difference(GA, x)
    assert len(y) == 10


def test_geo_ops():
    y = obj_move_to(GA, (-30, -40, 0), is_part=True)
    assert sum(1 if o.pos.almost_same_as((-30, -40, 0)) else 0 for o in y) == 9

    y = obj_move_to(GA, (-30, -40, 0), is_part=True, path="0/groupa")
    assert sum(1 if o.pos.almost_same_as((-30, -40, 0)) else 0 for o in y) == 4

    x = filter_objs(GA, is_part=True)
    y = obj_translated(x, (-7, 20, -50))
    diffs = [a.pos - b.pos for a, b in zip(x, y)]
    assert all(d.almost_same_as((7, -20, 50)) for d in diffs)

    x = filter_objs(GA, path="0/groupa")
    y = obj_difference(GA, x)
    x = obj_translated(x, (0, 100, 0))
    z = obj_union(y, x)

    x = obj_translated(GA, (0, 100, 0), path="0/groupa")

    y = obj_difference(z, x)
    assert len(y) == 0

    y = obj_exclusive(z, x)
    assert len(y) == 0


def test_bound_box():
    pts = [(-1, 2, 3), (3, 16, 32), (1.5, 7, -13)]
    bb = BoundBox.from_pts(pts)
    assert bb.xmin == -1
    assert bb.xmax == 3
    assert bb.ymin == 2
    assert bb.ymax == 16
    assert bb.zmin == -13
    assert bb.zmax == 32
    assert bb.xlen == 4
    assert bb.ylen == 14
    assert bb.zlen == 45
    assert bb.biggest_dim()[0] == "z"
    assert bb.biggest_dim()[1] == 45
    assert bb.face(">X").almost_same_as((3, 9, 9.5))
    assert bb.face("<x").almost_same_as((-1, 9, 9.5))
    assert bb.face(">z").almost_same_as((1, 9, 32))
    assert bb.face("<Z").almost_same_as((1, 9, -13))
    assert bb.face(">y").almost_same_as((1, 16, 9.5))
    assert bb.face("<Y").almost_same_as((1, 2, 9.5))

    pts = [Vector(-5, 1, 0), Vector(16, -7, 32), Vector(1.5, 7, -13)]
    bb = BoundBox.from_pts(pts)
    assert bb.xmin == -5
    assert bb.xmax == 16
    assert bb.ymin == -7
    assert bb.ymax == 7
    assert bb.zmin == -13
    assert bb.zmax == 32
    assert bb.xlen == 21
    assert bb.ylen == 14
    assert bb.zlen == 45

    other = (-50, 0, 100)
    bb = bb.union(other)
    assert bb.xmin == -50
    assert bb.xmax == 16
    assert bb.ymin == -7
    assert bb.ymax == 7
    assert bb.zmin == -13
    assert bb.zmax == 100
    assert bb.xlen == 66
    assert bb.ylen == 14
    assert bb.zlen == 113
    assert bb.biggest_dim()[0] == "z"
    assert bb.biggest_dim()[1] == 113

    bb = bb.union(Vector(-51, 18, 101))
    assert bb.xmin == -51
    assert bb.xmax == 16
    assert bb.ymin == -7
    assert bb.ymax == 18
    assert bb.zmin == -13
    assert bb.zmax == 101
    assert bb.xlen == 67
    assert bb.ylen == 25
    assert bb.zlen == 114

    q1 = LdrQuad.from_size(Vector(500, 0, 0), Vector(0, 400, 0))
    assert q1.bound_box.xmin == -250
    assert q1.bound_box.xmax == 250
    assert q1.bound_box.ymin == -200
    assert q1.bound_box.ymax == 200
    assert q1.bound_box.zmin == 0
    assert q1.bound_box.zmax == 0
    assert q1.bound_box.xlen == 500
    assert q1.bound_box.ylen == 400
    assert q1.bound_box.zlen == 0

    bb = bb.union(q1.points)
    assert bb.xmin == -250
    assert bb.xmax == 250
    assert bb.ymin == -200
    assert bb.ymax == 200
    assert bb.zmin == -13
    assert bb.zmax == 101
    assert bb.xlen == 500
    assert bb.ylen == 400
    assert bb.zlen == 114

    p1 = LdrPart(name="3001.dat", pos=(10, -50, 30))
    assert p1.bound_box.xmin == 10
    assert p1.bound_box.xmax == 10
    assert p1.bound_box.ymin == -50
    assert p1.bound_box.ymax == -50
    assert p1.bound_box.zmin == 30
    assert p1.bound_box.zmax == 30
    assert p1.bound_box.xlen == 0
    assert p1.bound_box.ylen == 0
    assert p1.bound_box.zlen == 0

    bb = MA.bound_box
    assert bb.xmin == -30
    assert bb.xmax == 30
    assert bb.ymin == -32
    assert bb.ymax == 0
    assert bb.zmin == -30
    assert bb.zmax == 30
    assert bb.xlen == 60
    assert bb.ylen == 32
    assert bb.zlen == 60

    bb1 = bb.translated((1, -2, 3))
    assert bb1.xmin == -29
    assert bb1.xmax == 31
    assert bb1.ymin == -34
    assert bb1.ymax == -2
    assert bb1.zmin == -27
    assert bb1.zmax == 33
    assert bb1.xlen == 60
    assert bb1.ylen == 32
    assert bb1.zlen == 60

    o1 = Vector(0, -100, 0)
    assert LdrArrow.norm_to_face(o1) == ">y"
    o1 = Vector(0, 0, 50)
    assert LdrArrow.norm_to_face(o1) == "<z"


def test_pitch_test():
    assert is_plate_multiple(8)
    assert is_plate_multiple(24)
    assert not is_plate_multiple(9)
    assert is_plate_multiple(12, with_stud=True)
    assert is_plate_multiple(12, with_either=True)
    assert not is_plate_multiple(8, with_stud=True)

    assert is_brick_multiple(24)
    assert is_brick_multiple(96)
    assert not is_brick_multiple(28)
    assert is_brick_multiple(100, with_stud=True)
    assert is_brick_multiple(100, with_either=True)
    assert not is_brick_multiple(96, with_stud=True)

    assert is_stud_multiple(40)
    assert is_stud_multiple(20)
    assert not is_stud_multiple(30)
    assert is_stud_multiple(44, with_stud=True)
    assert is_stud_multiple(44, with_either=True)
    assert not is_stud_multiple(40, with_stud=True)


def test_param_parsing():
    specs = "<x> <y> <z> (REL | ABS)"
    vals = "-35 55 0 ABS"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "flags" in p
    assert len(p["flags"]) == 1
    assert all(x in p for x in ("x", "y", "z"))
    assert p["x"] == "-35"

    specs = "( CERTIFY ( CCW | CW ) | NOCERTIFY ) <count> (A | B) [xr] [xb]"
    vals = "13 B 7"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "B" in p["flags"]
    assert p["count"] == "13"
    assert p["xr"] == "7"
    assert "xb" not in p

    vals = "13 B 7 8"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "B" in p["flags"]
    assert p["count"] == "13"
    assert p["xr"] == "7"
    assert p["xb"] == "8"

    vals = "13 B 7 8 5"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "B" in p["flags"]
    assert p["count"] == "13"
    assert p["xr"] == "7"
    assert p["xb"] == "8"
    assert p["extra"][0] == "5"

    vals = "13 B"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "B" in p["flags"]
    assert p["count"] == "13"
    assert "xr" not in p
    assert "xb" not in p

    vals = "13"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "B" not in p["flags"]
    assert p["count"] == "13"
    assert "xr" not in p
    assert "xb" not in p

    vals = "B"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert "B" in p["flags"]

    specs = ""
    vals = "13 B 7"
    mp = MetaValueParser(specs, vals)
    p = mp.param_dict
    assert len(p["flags"]) == 0
    assert len(p["extra"]) == 3

    specs = "[LENGTH length] [RATIO ratio] [TILT tilt] [COLOUR colour] <x> <y> <z>"
    mp = MetaValueParser(specs, vals="-20 -50 0 20 -50 0 LENGTH 3 TILT 30  COLOUR 802")
    p = mp.param_dict
    assert p["length"] == "3"
    assert p["tilt"] == "30"
    assert p["colour"] == "802"
    assert p["x"] == "-20"
    assert p["y"] == "-50"
    assert p["z"] == "0"
    assert p["extra"] == ["20", "-50", "0"]
