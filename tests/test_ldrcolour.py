# LdrColour tests

from rich import print
from pyldraw import *


def test_init_colour():
    c1 = LdrColour(15)
    c2 = LdrColour("White")
    c3 = LdrColour([1.0, 1.0, 1.0])
    c4 = LdrColour([255, 255, 255])
    c5 = LdrColour("#FFFFFF")
    assert c1 == c2
    assert c1 == c3
    assert c1 == c4
    assert c1 == c5
    assert c1.rgb == (1.0, 1.0, 1.0)
    assert repr(c1) == "LdrColour(15, r: 1.00 g: 1.00 b: 1.00, #FFFFFF)"
    assert str(c1) == "15"
    assert c1.high_contrast_complement == (0, 0, 0)
    c0 = LdrColour(402)
    assert c0.name == "Reddish Orange"

    c0 = LdrColour(1)
    assert c0.bgr == (191, 85, 0)
    assert c0.hsv == (107, 255, 191)
    assert c0.hue == 107
    assert c0.saturation == 255
    assert c0.brightness == 191
    assert c0.rgbint == (0, 85, 191)

    c0 = LdrColour(4)
    assert c0.bgr == (9, 26, 201)
    assert c0.hsv == (3, 244, 201)
    r0 = repr(c0)
    assert all((x in r0 for x in ("LdrColour", "0.79", "0.10", "0.04", "#C91A09")))
    n0 = c0.rich_name()
    assert "Red" in n0
    assert "4" in n0

    c0 = LdrColour(0)
    n0 = c0.rich_name()
    assert "Black" in n0
    assert "0" in n0

    c0 = LdrColour(2)
    assert c0.bgr == (62, 122, 37)
    assert c0.hsv == (69, 178, 122)

    c0 = LdrColour(26)
    assert c0.bgr == (120, 57, 146)
    assert c0.hsv == (159, 155, 146)

    c1 = LdrColour("#901F76")
    assert c1.bgr == (118, 31, 144)
    assert c1.hsv == (157, 200, 144)


def test_equality():
    c1 = LdrColour([0.4, 0.2, 0.6])
    c2 = LdrColour("#663399")
    assert c1 == c2
    c3 = LdrColour([102, 51, 153])
    assert c2 == c3
    c4 = LdrColour(71)
    assert not c4 == c1
    assert c1.label is None
    assert c1.name == "Default"


def test_names():
    c1 = LdrColour(70)
    assert c1.name == "Reddish Brown"
    assert c1.name_slug == "reddish-brown"
    assert c1.compact_name == "Red Brown"
    assert c1.hex_code == "#582A12"
    assert c1.high_contrast_complement == (1.0, 1.0, 1.0)
    assert c1.bgr == (18, 42, 88)

    c2 = LdrColour.CLEAR_MASK()
    assert c2.code == CLEAR_MASK_CODE
    assert c2.alpha == 2

    c3 = LdrColour.ARROW_RED()
    assert c3.code == 804
    assert c3.luminance == 220
    assert c3.rgb == (1, 0, 0)

    c3 = LdrColour.ADDED_MASK()
    assert c3.code == ADDED_MASK_CODE
    assert c3.luminance == 100
    assert c3.bgr == (118, 31, 144)
    assert c3.hue == 157

    c2 = LdrColour.OPAQUE_MASK()
    assert c2.code == OPAQUE_MASK_CODE
    assert c2.edge == OPAQUE_MASK_COLOUR

    c1 = LdrColour(1)
    o1 = LdrMeta.from_colour(c1)
    assert o1.raw == "0 !COLOUR Blue CODE 1 VALUE #0055BF EDGE #05131D"
