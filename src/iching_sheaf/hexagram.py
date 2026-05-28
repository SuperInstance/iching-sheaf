"""Hexagram: the fundamental unit of the I Ching."""

from __future__ import annotations

import random
from enum import IntEnum
from typing import List, Optional

from .data.texts import HEXAGRAM_DATA, KING_WEN_TO_FUXI, FUXI_TO_KING_WEN, TRIGRAM_DATA


class Line(IntEnum):
    """A line in a hexagram.

    YIN=0 and YANG=1 are stable lines.
    OLD_YIN=2 and OLD_YANG=3 are changing lines.
    """
    YIN = 0
    YANG = 1
    OLD_YIN = 2
    OLD_YANG = 3

    @property
    def is_yang(self) -> bool:
        return self in (Line.YANG, Line.OLD_YANG)

    @property
    def is_changing(self) -> bool:
        return self in (Line.OLD_YIN, Line.OLD_YANG)

    @property
    def changed(self) -> Line:
        """Return the line after a change (if changing), else itself."""
        if self == Line.OLD_YIN:
            return Line.YANG
        if self == Line.OLD_YANG:
            return Line.YIN
        return self

    @property
    def stable_value(self) -> int:
        """The stable value (0=yin, 1=yang) ignoring change status."""
        return 1 if self.is_yang else 0


class Hexagram:
    """A hexagram in the I Ching.

    Lines are stored bottom-to-top (line 0 is the bottom).
    """

    __slots__ = ("_lines", "_king_wen")

    def __init__(self, lines: List[Line], king_wen: Optional[int] = None):
        if len(lines) != 6:
            raise ValueError(f"Hexagram must have exactly 6 lines, got {len(lines)}")
        self._lines = list(lines)
        self._king_wen = king_wen

    @classmethod
    def from_binary(cls, bits: int) -> Hexagram:
        """Create a hexagram from a 6-bit Fu Xi binary value (bit 0 = bottom line)."""
        lines = []
        for i in range(6):
            lines.append(Line.YANG if (bits >> i) & 1 else Line.YIN)
        kw = FUXI_TO_KING_WEN.get(bits)
        return cls(lines, king_wen=kw)

    @classmethod
    def from_king_wen(cls, number: int) -> Hexagram:
        """Create a hexagram from its King Wen number (1-64)."""
        if number not in HEXAGRAM_DATA:
            raise ValueError(f"Invalid King Wen number: {number}")
        fuxi = KING_WEN_TO_FUXI[number]
        return cls.from_binary(fuxi)

    @classmethod
    def from_coins(cls) -> Hexagram:
        """Cast a hexagram using the three-coin method.

        Each coin: heads=3, tails=2. Sum of three coins:
        6 = old yin, 7 = yang, 8 = yin, 9 = old yang.
        """
        lines: List[Line] = []
        for _ in range(6):
            coins = [random.choice([2, 3]) for _ in range(3)]
            total = sum(coins)
            if total == 6:
                lines.append(Line.OLD_YIN)
            elif total == 7:
                lines.append(Line.YANG)
            elif total == 8:
                lines.append(Line.YIN)
            else:  # 9
                lines.append(Line.OLD_YANG)
        return cls(lines)

    @classmethod
    def from_yarrow(cls) -> Hexagram:
        """Cast a hexagram using simulated yarrow stalk probabilities.

        Probabilities: old yin=1/16, yin=7/16, yang=5/16, old yang=3/16.
        """
        weights = [1, 5, 7, 3]  # OLD_YIN, YANG, YIN, OLD_YANG
        lines: List[Line] = []
        for _ in range(6):
            lines.append(random.choices(
                [Line.OLD_YIN, Line.YANG, Line.YIN, Line.OLD_YANG],
                weights=weights,
                k=1,
            )[0])
        return cls(lines)

    @property
    def lines(self) -> List[Line]:
        return list(self._lines)

    @property
    def king_wen(self) -> Optional[int]:
        if self._king_wen is not None:
            return self._king_wen
        # Try to find by binary value
        bits = self.binary_value
        return FUXI_TO_KING_WEN.get(bits)

    @property
    def name(self) -> str:
        kw = self.king_wen
        if kw and kw in HEXAGRAM_DATA:
            return HEXAGRAM_DATA[kw][0]
        return f"Hexagram({self.binary_value:06b})"

    @property
    def binary_value(self) -> int:
        """Fu Xi binary value (bit 0 = bottom line)."""
        val = 0
        for i, line in enumerate(self._lines):
            if line.is_yang:
                val |= (1 << i)
        return val

    @property
    def upper_trigram(self) -> int:
        """Upper trigram as 3-bit value (lines 3-5, bottom to top)."""
        return (self.binary_value >> 3) & 0x7

    @property
    def lower_trigram(self) -> int:
        """Lower trigram as 3-bit value (lines 0-2)."""
        return self.binary_value & 0x7

    @property
    def upper_trigram_name(self) -> str:
        return TRIGRAM_DATA[self.upper_trigram][1]

    @property
    def lower_trigram_name(self) -> str:
        return TRIGRAM_DATA[self.lower_trigram][1]

    @property
    def changing_lines(self) -> List[int]:
        """Indices of changing lines."""
        return [i for i, line in enumerate(self._lines) if line.is_changing]

    @property
    def target(self) -> Hexagram:
        """The hexagram obtained by changing all changing lines."""
        new_lines = [line.changed for line in self._lines]
        return Hexagram(new_lines)

    def line_at(self, index: int) -> Line:
        return self._lines[index]

    def set_line(self, index: int, line: Line) -> Hexagram:
        """Return a new hexagram with the given line changed."""
        new_lines = list(self._lines)
        new_lines[index] = line
        return Hexagram(new_lines)

    def flip_line(self, index: int) -> Hexagram:
        """Return a new hexagram with the given line flipped yin<->yang."""
        current = self._lines[index]
        new_line = Line.YIN if current.is_yang else Line.YANG
        return self.set_line(index, new_line)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hexagram):
            return NotImplemented
        return self.binary_value == other.binary_value

    def __hash__(self) -> int:
        return hash(self.binary_value)

    def __repr__(self) -> str:
        return f"Hexagram({self.name}, kw={self.king_wen}, bits={self.binary_value:06b})"

    def __str__(self) -> str:
        symbols = []
        for line in self._lines:
            if line == Line.YANG:
                symbols.append("━━━━━━━━━")
            elif line == Line.YIN:
                symbols.append("━━━ ━━━")
            elif line == Line.OLD_YANG:
                symbols.append("━━━○━━━")
            else:  # OLD_YIN
                symbols.append("━━━ × ━━━")
        return "\n".join(reversed(symbols))
