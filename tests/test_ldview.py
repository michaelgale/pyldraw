# LdrFile tests

import os.path
from rich import print, inspect
from pyldraw import *


FN_LDR = "./tests/testfiles/test_file1.ldr"
FN_LDR2 = "./tests/testfiles/test_file2.ldr"
FN_LDR_MODEL = "./tests/outfiles/test_ldv1.ldr"
IMG_PATH = "./tests/outimages/"

LDV_ARGS = {
    "overwrite": False,
    "dpi": 150,
    "auto_crop": False,
    "output_path": IMG_PATH,
    "log_output": False,
    "log_level": 0,
}

TEST_RENDER_PARTS = True
TEST_RENDER_STEPS = False
TEST_RENDER_OUTLINE = True
TEST_STEP_RANGE = (1, 14)


def test_ldvrender_part():
    p1 = LdrPart(name="3001.dat", colour=4)
    p1.render_image(**LDV_ARGS)
    fn = IMG_PATH + p1.pli_filename(**LDV_ARGS)
    assert os.path.isfile(fn)


def test_ldvrender_file():
    f1 = LdrFile(FN_LDR, dpi=LDV_ARGS["dpi"], initial_aspect=(-35, -40, 0))
    if TEST_RENDER_STEPS:
        for i, step in enumerate(f1.iter_steps()):
            if i >= TEST_STEP_RANGE[0] and i <= TEST_STEP_RANGE[1]:
                step.render_model(**LDV_ARGS)
                step.render_masked_image(**LDV_ARGS)
                step.render_unmasked_image(**LDV_ARGS)
                if TEST_RENDER_OUTLINE:
                    step.render_outline_image(**LDV_ARGS)
                if TEST_RENDER_PARTS:
                    step.render_parts_images(**LDV_ARGS)


def test_ldvrender_features():
    f2 = LdrFile(FN_LDR2, dpi=LDV_ARGS["dpi"], initial_aspect=(-35, -35, 0))
    # f2.print_raw()
    # for step in f2.iter_steps():
    #     print(step)
    #     for o in step.step_parts:
    #         print(step.idx, step.level, repr(o))
    for i, step in enumerate(f2.iter_steps()):
        # print(step)
        if step.delimited_objs:
            d = step.delimited_objs
            if i == 1:
                assert len(d) == 1
                assert "trigger" in d[0]
                assert d[0]["trigger"].raw == "0 !PY ARROW BEGIN 0 -60 0"
                assert "offset" in d[0]
                assert d[0]["offset"].almost_same_as((0, -60, 0))
        # step.render_model(**LDV_ARGS)
        # step.render_masked_image(**LDV_ARGS)
        # step.render_unmasked_image(**LDV_ARGS)
        # step.render_outline_image(**LDV_ARGS)


# def test_ldvrender_big():
#     f1 = LdrFile("./tests/testfiles/Cafe2_clean.ldr", dpi=LDV_ARGS["dpi"], initial_aspect=(-35, 35, 0))
# f1.print_bom()
# for i, step in enumerate(f1.iter_steps()):
#     print(step)
# if i < 50:
#     step.render_model(**LDV_ARGS)
