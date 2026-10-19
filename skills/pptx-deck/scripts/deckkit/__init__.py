"""deckkit — brand-driven native PPTX generation on top of python-pptx."""
from .brand import Brand, load_brand, contrast, luminance
from .canvas import Canvas
from .build import build
from .layouts import LAYOUTS, columns, grid_span, headline
from . import story  # noqa: F401  registers the summary layout
from . import frameworks  # noqa: F401  (registers the matrix and shift layouts)

__all__ = ["Brand", "load_brand", "contrast", "luminance", "Canvas", "build", "LAYOUTS",
           "columns", "grid_span", "headline"]
