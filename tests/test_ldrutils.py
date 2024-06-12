# LdrObj tests

from rich import print
from pyldraw import *

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

MA = LdrModel.from_str(TEST_GROUPA, "GroupA")
for i, s in enumerate(MA.steps):
    if not i % 2 == 0:
        for o in s.objs:
            o.path = "0/groupa"
GA = [o for o in MA.iter_objs()]
MB = LdrModel.from_str(TEST_GROUPB, "GroupB")
MB.assign_path_to_objs("0/groupb")
GB = [o for o in MB.iter_objs()]


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
