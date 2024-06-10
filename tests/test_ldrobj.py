# LdrObj tests

from rich import print
from pyldraw import *


def test_ldrobj_init():
    o1 = LdrObj()
    assert o1 is not None


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
    o3 = LdrObj.from_str("0 FILE MyModel.ldr")
    assert isinstance(o3, LdrMeta)
    o3 = LdrObj.from_str("0 NOFILE")
    assert isinstance(o3, LdrMeta)


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


def test_ldrpart():
    o1 = LdrObj.from_str("1 4 5 10 20 1 0 0 0 1 0 0 0 -1 3201.dat")
    assert isinstance(o1, LdrPart)
    assert o1.is_part
    o1 = LdrObj.from_str("1 4 10 -50 20 -1 0 0 0 -1 0 0 0 -1 This Submodel 1.ldr")
    assert isinstance(o1, LdrPart)
    assert o1.is_model
