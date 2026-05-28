"""SheafReading: cohomological analysis of an I Ching reading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .hexagram import Hexagram, Line
from .graph import HexagramGraph
from .sheaf import IChingSheaf, StalkData


@dataclass
class Reading:
    """An I Ching reading: a hexagram with potential changing lines."""
    hexagram: Hexagram
    changing_lines: List[int]  # indices of changing lines (0-5)

    @classmethod
    def from_hexagram(cls, h: Hexagram) -> Reading:
        """Create a reading from a hexagram (detects changing lines)."""
        return cls(hexagram=h, changing_lines=h.changing_lines)

    @property
    def target(self) -> Hexagram:
        """The target hexagram after all changing lines change."""
        return self.hexagram.target

    @property
    def is_stable(self) -> bool:
        """No changing lines — a stable reading."""
        return len(self.changing_lines) == 0


class SheafReading:
    """Cohomological analysis of an I Ching reading.

    Interprets a reading (hexagram + changing lines) as a sheaf-theoretic
    object and computes cohomological invariants.
    """

    def __init__(self, reading: Reading, sheaf: Optional[IChingSheaf] = None,
                 graph: Optional[HexagramGraph] = None) -> None:
        self.reading = reading
        self.graph = graph or HexagramGraph()
        self.sheaf = sheaf or IChingSheaf(self.graph)

    def cohomology_h0(self) -> int:
        """Dimension of H^0: connected sections that agree.

        H^0 counts the number of independent global sections compatible
        with the reading. For stable hexagrams, H^0 = 1 (the judgment).
        For changing readings, H^0 may be 0 (contradiction) or 1 (resolution).
        """
        h = self.reading.hexagram
        stalk = self.sheaf.stalk(h)

        if self.reading.is_stable:
            # Stable: the judgment is a consistent global section
            return 1 if stalk.judgment else 0

        # Count how many changing lines are compatible with the judgment
        compatible = 0
        for idx in self.reading.changing_lines:
            if idx < len(stalk.line_texts) and stalk.line_texts[idx]:
                compatible += 1

        # H^0 = 1 if all changing lines have texts, else 0
        if compatible == len(self.reading.changing_lines) and stalk.judgment:
            return 1
        return 0

    def cohomology_h1(self) -> float:
        """Obstruction measure: dimension of H^1.

        H^1 measures the failure of local sections to glue into global sections.
        Nonzero H^1 means the reading contains genuine tension — the "wisdom"
        lives in the obstruction.

        Returns a float representing the obstruction dimension.
        """
        if self.reading.is_stable:
            return 0.0

        n_changing = len(self.reading.changing_lines)
        h = self.reading.hexagram
        target = self.reading.target
        stalk_h = self.sheaf.stalk(h)
        stalk_t = self.sheaf.stalk(target)

        # Count textual contradictions between source and target
        contradictions = 0.0
        for idx in self.reading.changing_lines:
            text_src = stalk_h.line_texts[idx] if idx < len(stalk_h.line_texts) else ""
            text_tgt = stalk_t.line_texts[idx] if idx < len(stalk_t.line_texts) else ""

            # A contradiction exists when both line texts are non-empty
            # but point in different directions
            if text_src and text_tgt:
                # Measure dissimilarity
                words_s = set(text_src.lower().split())
                words_t = set(text_tgt.lower().split())
                overlap = len(words_s & words_t)
                total = len(words_s | words_t)
                if total > 0:
                    contradictions += 1.0 - (overlap / total)
                else:
                    contradictions += 1.0

        # H^1 dimension is bounded by the number of changing lines
        # but weighted by textual tension
        return contradictions / max(n_changing, 1) * n_changing

    def obstruction_class(self) -> str:
        """Human-readable description of the contradiction/obstruction.

        Describes where the wisdom lives — in the gap between what is
        and what is becoming.
        """
        if self.reading.is_stable:
            return f"Stable: {self.reading.hexagram.name}. The situation is clear. No obstruction — act with confidence."

        h = self.reading.hexagram
        target = self.reading.target
        stalk_h = self.sheaf.stalk(h)
        stalk_t = self.sheaf.stalk(target)

        parts = [f"From {h.name} to {target.name}."]

        for idx in self.reading.changing_lines:
            line_text = stalk_h.line_texts[idx] if idx < len(stalk_h.line_texts) else "unknown"
            parts.append(
                f"  Line {idx + 1} (changing): \"{line_text}\""
            )

        h1 = self.cohomology_h1()
        if h1 > 0:
            parts.append(
                f"Obstruction (H¹ ≈ {h1:.2f}): The changing lines create tension. "
                f"The wisdom lies in navigating between {h.name} and {target.name}."
            )
        else:
            parts.append(
                "The transformation flows naturally. Trust the process."
            )

        return "\n".join(parts)

    def morphism_to_target(self) -> Hexagram:
        """The target hexagram: where the reading points.

        This is the hexagram obtained by changing all changing lines.
        In sheaf-theoretic terms, this is the image of the natural
        morphism from the source stalk to the target stalk.
        """
        return self.reading.target

    def persistence(self) -> float:
        """How 'deep' the reading is — how many lines agree between source and target.

        Returns a value between 0.0 (all lines changing) and 1.0 (no lines changing).
        Higher persistence means the reading is more stable/deeply rooted.
        """
        if self.reading.is_stable:
            return 1.0

        n_stable = 6 - len(self.reading.changing_lines)
        return n_stable / 6.0

    def section_compatibility(self) -> float:
        """Measure how compatible the source and target stalks are.

        Compares judgments and image texts for thematic overlap.
        """
        stalk_s = self.sheaf.stalk(self.reading.hexagram)
        stalk_t = self.sheaf.stalk(self.reading.target)

        words_j = set(stalk_s.judgment.lower().split()) & set(stalk_t.judgment.lower().split())
        words_i = set(stalk_s.image.lower().split()) & set(stalk_t.image.lower().split())

        total_j = len(set(stalk_s.judgment.lower().split()) | set(stalk_t.judgment.lower().split()))
        total_i = len(set(stalk_s.image.lower().split()) | set(stalk_t.image.lower().split()))

        overlap = 0.0
        if total_j > 0:
            overlap += len(words_j) / total_j
        if total_i > 0:
            overlap += len(words_i) / total_i

        return overlap / 2.0 if (total_j + total_i) > 0 else 0.0
