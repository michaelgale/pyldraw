# LdrObj tests

from rich import print, inspect
from pyldraw import *
from pyldraw.geometry import BoundBox


TEST_MODEL1 = """
1 1 0 -48 -70 1 0 0 0 1 0 -0 0 1 3010.dat
0 !PY PAGE_BREAK
0 STEP
1 2 0 -88 -70 1 0 0 0 1 0 -0 0 1 3001.dat
0 !PY SCALE 0.57
0 STEP
1 4 0 -88 -70 1 0 0 0 1 0 -0 0 1 3002.dat
0 !PY HIDE_FULLSCALE
0 !PY HIDE_PREVIEW
0 !PY HIDE_ROTICON
0 !PY HIDE_PAGE_NUM
0 !PY NO_CALLOUT
0 STEP
"""


def test_ldrstep_init():
    m1 = LdrModel.from_str(TEST_MODEL1)
    assert len(m1.steps) == 3
    assert len(m1.steps[0].objs) == 3
    assert len(m1.steps[1].objs) == 3


def test_ldrstep_meta():
    m1 = LdrModel.from_str(TEST_MODEL1)
    s1 = m1.steps[0]
    assert s1.page_break
    assert s1.column_break is None
    assert not s1.column_break
    s2 = m1.steps[1]
    assert not s2.page_break
    assert s2.new_scale == 0.57
    s3 = m1.steps[2]
    assert s3.hide_fullscale
    assert s3.hide_preview
    assert s3.hide_rotation_icon
    assert s3.hide_page_num
    assert s3.no_callout
    assert s3.new_page_num is None
