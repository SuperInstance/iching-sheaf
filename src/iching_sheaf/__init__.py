"""iching-sheaf: The I Ching as a sheaf-theoretic system."""

from .hexagram import Line, Hexagram
from .graph import HexagramGraph
from .sheaf import IChingSheaf, StalkData
from .reading import SheafReading
from .category import TrigramCategory
from .tropical import TropicalHexagram
from .persistence import PersistenceAnalysis

__all__ = [
    "Line", "Hexagram",
    "HexagramGraph",
    "IChingSheaf", "StalkData",
    "SheafReading",
    "TrigramCategory",
    "TropicalHexagram",
    "PersistenceAnalysis",
]
__version__ = "1.0.0"
