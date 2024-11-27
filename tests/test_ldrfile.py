# LdrFile tests

from rich import print, inspect
from pyldraw import *

TEST_STEP1 = """
1 1 -60 -32 -80 1 0 0 0 1 0 -0 0 1 submodel2.ldr
1 1 60 -32 -80 1 0 0 0 1 0 -0 0 1 submodel2.ldr
1 1 0 -48 -70 1 0 0 0 1 0 -0 0 1 3010.dat
0 STEP
"""

TEST_MODEL1 = """
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
0 STEP
0 NOFILE
"""

TEST_MODEL2 = """
0 FILE untitled model.ldr
0 untitled model
0 Name: 
0 Author: Michael Gale
1 2 0 0 0 1 0 0 0 1 0 -0 0 1 41539.dat
0 STEP
1 4 -40 -24 70 1 0 0 0 1 0 -0 0 1 3010.dat
1 4 40 -24 70 1 0 0 0 1 0 -0 0 1 3010.dat
1 71 0 -24 -70 1 0 0 0 1 0 -0 0 1 3008.dat
0 STEP
1 71 0 -8 0 1 0 0 0 1 0 -0 0 1 submodel1.ldr
0 STEP
1 1 -60 -32 -80 1 0 0 0 1 0 -0 0 1 submodel2.ldr
1 1 60 -32 -80 1 0 0 0 1 0 -0 0 1 submodel2.ldr
1 1 0 -48 -70 1 0 0 0 1 0 -0 0 1 3010.dat
0 STEP
1 15 0 -48 70 1 0 0 0 1 0 -0 0 1 3008.dat
0 STEP
0 NOFILE
"""

TEST_MODEL3 = """
0 FILE submodel1.ldr
0 untitled model
0 Name: submodel1.ldr
0 Author: Michael Gale
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
0 !PY ARROW BEGIN 0 -50 0
1 0 0 -8 0 1 0 0 0 1 0 -0 0 1 3068b.dat
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
0 !PY ARROW END
1 28 20 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 28 40 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
0 STEP
1 70 -30 -8 -30 1 0 0 0 1 0 -0 0 1 2420.dat
1 70 -30 -8 30 -0 0 1 0 1 0 -1 0 -0 2420.dat
1 70 30 -8 30 -1 0 0 0 1 0 -0 0 -1 2420.dat
1 70 30 -8 -30 0 0 -1 0 1 0 1 0 0 2420.dat
0 STEP
1 14 0 -32 30 -1 0 0 0 1 0 -0 0 -1 3010.dat
0 PLI BEGIN IGN
1 1 -60 -32 -80 1 0 0 0 1 0 -0 0 1 submodel2.ldr
1 1 60 -32 -80 1 0 0 0 1 0 -0 0 1 submodel2.ldr
0 PLI END
1 1 0 -48 -70 1 0 0 0 1 0 -0 0 1 3010.dat
1 4 40 -24 70 1 0 0 0 1 0 -0 0 1 3010.dat
0 !PY HIDE_PARTS BEGIN
1 71 0 -24 -70 1 0 0 0 1 0 -0 0 1 3008.dat
0 !PY HIDE_PARTS END
0 STEP
0 NOFILE
"""

TEST_MODEL4 = """
0 FILE submodel1.ldr
0 untitled model
0 Name: submodel1.ldr
0 Author: Michael Gale
1 28 0 0 0 1 0 0 0 1 0 -0 0 1 3031.dat
1 0 0 -8 0 1 0 0 0 1 0 -0 0 1 3068b.dat
0 STEP
0 !PY TAG BEGIN TEST1
1 70 -30 -8 -30 1 0 0 0 1 0 -0 0 1 2420.dat
1 70 -30 -8 30 -0 0 1 0 1 0 -1 0 -0 2420.dat
1 70 30 -8 30 -1 0 0 0 1 0 -0 0 -1 2420.dat
1 70 30 -8 -30 0 0 -1 0 1 0 1 0 0 2420.dat
0 STEP
0 !PY TAG BEGIN TEST2
1 14 0 -32 30 -1 0 0 0 1 0 -0 0 -1 3010.dat
0 !PY TAG END TEST1
1 40 0 -50 0 1 0 0 0 1 0 -0 0 1 submodel3.ldr
0 STEP
1 15 40 -32 30 -1 0 0 0 1 0 -0 0 -1 3023.dat
0 !PY TAG END TEST2
1 15 -40 -32 30 -1 0 0 0 1 0 -0 0 -1 3023.dat
0 STEP
0 NOFILE
0 FILE submodel3.ldr
0 untitled model
0 Name: submodel3.ldr
0 Author: Michael Gale
1 15 0 0 0 1 0 0 0 1 0 -0 0 1 6141.dat
0 STEP
1 40 0 -8 0 1 0 0 0 1 0 -0 0 1 98138.dat
0 STEP
0 NOFILE
"""


def test_ldrmodel():
    m1 = LdrModel.from_str(TEST_MODEL1)
    assert m1.name == "submodel1.ldr"
    assert m1.step_count == 3
    assert m1.obj_count == 15
    assert m1.part_count == 4
    assert m1.part_qty == 7
    assert m1.sub_model_count == 0
    assert m1.sub_model_qty == 0

    m1 = LdrModel.from_str(TEST_MODEL2)
    assert m1.name == "untitled model.ldr"
    assert m1.step_count == 5
    assert m1.obj_count == 19
    assert m1.part_count == 5
    assert m1.part_qty == 6
    assert m1.sub_model_count == 2
    assert m1.sub_model_qty == 3


def test_step_delimiter():
    m1 = LdrModel.from_str(TEST_MODEL3)
    for i, s in enumerate(m1.steps):
        d1 = s.delimited_objs
        if i == 0:
            assert len(d1) == 1
        elif i == 1:
            assert len(d1) == 0
        elif i == 2:
            assert len(d1) == 2
            assert len(d1[0]["objs"]) == 2
            assert len(d1[1]["objs"]) == 1


def test_ldrfile():
    f1 = LdrFile("./tests/testfiles/test_file1.ldr", initial_aspect=(0, 45, 0))

    assert f1.root is not None
    assert len(f1.models) == 3
    assert len(f1.build_steps) == 17
    assert f1.piece_count == 27
    assert f1.element_count == 14
    assert f1.build_steps[-1].sha1_hash == "c664f735f218aa5473e4034216ba0c204d0eb4c1"
    assert f1.colour_count == 10
    assert len(f1.objs_at_step(5)) == 2
    assert len(f1.step_parts_at_step(3)) == 4
    assert repr(f1) == "LdrFile(./tests/testfiles/test_file1.ldr)"
    s = f1.build_steps[3]
    bb = s.model_bound_box
    assert bb.xlen == 100
    assert bb.ylen == 20
    assert bb.zlen == 100
    bb = s.step_bound_box
    assert bb.xlen == 100
    assert bb.ylen == 12
    assert bb.zlen == 100
    assert (
        s.outline_filename
        == "3o_1_300_1.00_6ec016fcd9ae6e4183dc3b6972d2f8ca8026236f.png"
    )
    assert len(s.unmasked_filenames) == 1
    assert (
        s.unmasked_filenames[0][0]
        == "3u_1_300_1.00_6ec016fcd9ae6e4183dc3b6972d2f8ca8026236f.png"
    )
    assert len(s.masked_filenames) == 1
    assert (
        s.masked_filenames[0][0]
        == "3m_1_300_1.00_6ec016fcd9ae6e4183dc3b6972d2f8ca8026236f.png"
    )

    # for step in f1.iter_steps():
    #     print(step)

    # f1 = LdrFile("./tests/testfiles/Cafe2_clean.ldr", initial_aspect=(0, 45, 0))
    # f1.print_bom()
    # print("Piece count   : %dx" % (f1.piece_count))
    # print("Element count : %dx" % (f1.element_count))
    # print("Colour count  : %dx" % (f1.colour_count))


def test_ldrfile_ext():
    f1 = LdrFile("./tests/testfiles/test_file3.ldr", initial_aspect=(0, 45, 0))
    assert len(f1.build_steps) == 23
    assert f1.non_virtual_step_count == 19
    for step in f1.iter_steps():
        pli = step.pli_parts
        if step.idx == 3:
            assert len(pli) == 2
            assert "3001-5" in pli
            assert "3001-14" in pli
            assert pli["3001-5"] == 1
            assert pli["3001-14"] == 1
        elif step.idx == 4:
            assert len(pli) == 1
            assert "3008-71" in pli
            assert "3010-4" not in pli
            assert pli["3008-71"] == 1
    # for step in f1.iter_build_steps():
    #     print(step)

    # for o in step.step_parts:
    #     print(o, o.path)


def test_ldrfile_tags():
    f1 = LdrFile(from_str=TEST_MODEL4, initial_aspect=(35, 45, 0))
    assert len(f1.models) == 1
    assert len(f1.build_steps) == 6
    assert f1.piece_count == 11
    assert f1.element_count == 7
    t1 = sum([1 if o.has_tag("TEST1") else 0 for o in f1.model_parts_at_step(-1)])
    t2 = sum([1 if o.has_tag("TEST2") else 0 for o in f1.model_parts_at_step(-1)])
    t3 = sum(
        [1 if o.has_tag(["TEST2", "TEST1"]) else 0 for o in f1.model_parts_at_step(-1)]
    )
    assert t1 == 5
    assert t2 == 4
    assert t3 == 1
