"""pyldraw - A python library for working with LDraw files and data structures."""

# fmt: off
__project__ = 'pyldraw'
__version__ = '0.2.0'
# fmt: on

VERSION = __project__ + "-" + __version__

from .constants import *
from .support.ldview import LDViewRender
from .ldrcolour import LdrColour
from .ldrobj import LdrObj, LdrComment, LdrMeta, LdrLine, LdrTriangle, LdrQuad, LdrPart
from .ldrstep import LdrStep, BuildStep
from .ldrmodel import LdrModel
from .ldrfile import LdrModel, LdrFile
from .ldrutils import *
from .ldrarrow import LdrArrow
from .ldrlib import find_part
