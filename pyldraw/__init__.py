"""pyldraw - A python library for working with LDraw files and data structures."""

# fmt: off
__project__ = 'pyldraw'
__version__ = '0.1.0'
# fmt: on

VERSION = __project__ + "-" + __version__

from .constants import *
from .ldrcolour import LdrColour
from .ldrobj import LdrObj, LdrComment, LdrMeta, LdrLine, LdrTriangle, LdrQuad, LdrPart
from .ldrfile import LdrStep, LdrModel, LdrFile, BuildStep
from .ldrutils import *
