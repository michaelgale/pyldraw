"""pyldraw - A python library for working with LDraw files and data structures."""

# fmt: off
__project__ = 'pyldraw'
__version__ = '0.3.3'
# fmt: on

VERSION = __project__ + "-" + __version__

from .constants import *
from .geometry import is_brick_multiple, is_plate_multiple, is_stud_multiple
from .ldrlib import find_part, part_description
from .support.ldview import LDViewRender
from .ldrcolour import LdrColour
from .ldrobj import LdrObj, LdrComment, LdrMeta, LdrLine, LdrTriangle, LdrQuad, LdrPart
from .ldrutils import *
from .ldrarrow import LdrArrow
from .ldrstep import LdrStep, BuildStep
from .ldrmodel import LdrModel
from .ldrfile import LdrModel, LdrFile
