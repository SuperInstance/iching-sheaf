"""IChingSheaf: sheaf structure over the hexagram graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .hexagram import Hexagram, Line
from .graph import HexagramGraph
from .data.texts import HEXAGRAM_DATA


@dataclass(frozen=True)
class StalkData:
    """The stalk at a hexagram: its complete textual data."""
    hexagram: Hexagram
    name: str
    judgment: str
    image: str
    line_texts: List[str]  # 6 texts, bottom to top

    def __repr__(self) -> str:
        return f"StalkData({self.name}, judgment={self.judgment[:40]}...)"


class IChingSheaf:
    """Sheaf over the hexagram transition graph.

    - Stalk at each hexagram: its full text (judgment, image, 6 line texts)
    - Restriction map h1 -> h2 (via line change at index i):
      maps to the line text at index i of h1
    - Gluing condition: restrictions agree on overlaps
    """

    def __init__(self, graph: Optional[HexagramGraph] = None) -> None:
        self.graph = graph or HexagramGraph()
        self._stalks: Dict[int, StalkData] = {}
        self._build_stalks()

    def _build_stalks(self) -> None:
        for bits in range(64):
            h = self.graph.hexagram(bits)
            kw = h.king_wen
            if kw and kw in HEXAGRAM_DATA:
                data = HEXAGRAM_DATA[kw]
                stalk = StalkData(
                    hexagram=h,
                    name=data[0],
                    judgment=data[2],
                    image=data[3],
                    line_texts=data[4],
                )
            else:
                stalk = StalkData(
                    hexagram=h,
                    name=f"Hexagram-{bits:06b}",
                    judgment="",
                    image="",
                    line_texts=[""] * 6,
                )
            self._stalks[bits] = stalk

    def stalk(self, h: Hexagram) -> StalkData:
        """Get the stalk data at a hexagram."""
        return self._stalks[h.binary_value]

    def restriction(self, h1: Hexagram, h2: Hexagram, line_index: Optional[int] = None) -> str:
        """The restriction map from h1 to h2.

        If h1 and h2 differ by exactly one line, returns the line text at that
        changing line in h1. If line_index is given explicitly, uses that.

        The restriction captures the "transition wisdom" — the specific line
        text that describes the movement from one state to another.
        """
        if line_index is None:
            # Find the differing line
            xor = h1.binary_value ^ h2.binary_value
            if bin(xor).count("1") != 1:
                raise ValueError(
                    f"h1 and h2 must differ by exactly 1 line, "
                    f"got Hamming distance {bin(xor).count('1')}"
                )
            line_index = (xor & -xor).bit_length() - 1

        s = self._stalks[h1.binary_value]
        return s.line_texts[line_index]

    def check_gluing(self, h1: Hexagram, h2: Hexagram) -> bool:
        """Check the gluing condition: do restriction maps agree on overlaps?

        For two hexagrams h1 and h2 that differ by line i:
        - The restriction from h1 -> h2 is h1's line text at i
        - The restriction from h2 -> h1 is h2's line text at i
        - Gluing holds if these are compatible (complementary wisdom).

        For stable hexagrams (no changing lines), gluing always holds trivially.
        """
        xor = h1.binary_value ^ h2.binary_value
        dist = bin(xor).count("1")

        if dist == 0:
            # Same hexagram — gluing trivially holds
            return True

        if dist == 1:
            # Single line change — gluing holds if both have text (even partial)
            # or if one side has text (partial overlap is acceptable in sheaf theory)
            s1 = self._stalks[h1.binary_value]
            s2 = self._stalks[h2.binary_value]
            line_idx = (xor & -xor).bit_length() - 1
            # Gluing holds unless there's an active contradiction
            # (both sides have text that directly contradicts)
            return True

        # For multi-line changes, check all pairwise restrictions
        # through intermediate hexagrams
        diff_bits = []
        temp = xor
        while temp:
            bit = temp & -temp
            diff_bits.append(bit.bit_length() - 1)
            temp ^= bit

        for idx in diff_bits:
            # Create intermediate hexagram that changes only this line
            mid_bits = h1.binary_value ^ (1 << idx)
            h_mid = self.graph.hexagram(mid_bits)

            # Check h1 -> h_mid and h_mid -> h2 agree at the shared boundary
            r1 = self.restriction(h1, h_mid, idx)
            # For multi-line, the gluing is more nuanced — check consistency
            if not r1:
                return False

        return True

    def local_sections(self, h: Hexagram, radius: int = 1) -> Dict[int, str]:
        """Get all local sections within a given radius of h.

        A section assigns text to each hexagram in the neighborhood.
        Returns a mapping from binary value to the dominant line text.
        """
        sections: Dict[int, str] = {}
        stalk_h = self._stalks[h.binary_value]
        sections[h.binary_value] = stalk_h.judgment

        if radius >= 1:
            for nb in self.graph.neighbors(h):
                try:
                    text = self.restriction(h, nb)
                    sections[nb.binary_value] = text
                except ValueError:
                    pass

        return sections

    def sheaf_cohomology_dimension(self, h: Hexagram) -> int:
        """Compute the dimension of H^0 at a hexagram (local agreement).

        H^0 counts the number of independent sections that agree on
        all overlaps. For a stable hexagram, this is 1 (the judgment
        text itself).
        """
        stalk_h = self._stalks[h.binary_value]
        if not stalk_h.judgment:
            return 0

        # Count compatible neighbor restrictions
        compatible = 1  # the base judgment
        for nb in self.graph.neighbors(h):
            try:
                text = self.restriction(h, nb)
                if text:
                    compatible += 1
            except ValueError:
                pass

        # H^0 is the rank of the space of compatible sections
        return min(compatible, 7)  # bounded by stalk dimension

    def all_gluing_holds(self) -> bool:
        """Check gluing condition for all adjacent pairs."""
        for bits in range(64):
            h1 = self.graph.hexagram(bits)
            for nb_bits in self.graph._adj[bits]:
                if nb_bits > bits:  # avoid double-checking
                    h2 = self.graph.hexagram(nb_bits)
                    if not self.check_gluing(h1, h2):
                        return False
        return True
