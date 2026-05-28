"""TropicalHexagram: line changes as tropical algebra operations."""

from __future__ import annotations

from typing import List, Optional

from .hexagram import Hexagram, Line


class TropicalHexagram:
    """Line changes interpreted through tropical algebra.

    In tropical mathematics:
    - Tropical addition: x ⊕ y = max(x, y)
    - Tropical multiplication: x ⊗ y = x + y
    - Tropical exponentiation: x^⊗n = n·x

    We model line changes as:
    - Yin (0) and Yang (1) as tropical elements
    - A line change yin→yang is tropical max (yang dominates)
    - Hexagram evolution as tropical polynomial evaluation
    - The "superior" line in any group is the tropical maximum
    """

    @staticmethod
    def tropical_add(a: float, b: float) -> float:
        """Tropical addition: max(a, b)."""
        return max(a, b)

    @staticmethod
    def tropical_multiply(a: float, b: float) -> float:
        """Tropical multiplication: a + b."""
        return a + b

    @staticmethod
    def tropical_power(a: float, n: int) -> float:
        """Tropical exponentiation: n * a."""
        return n * a

    @staticmethod
    def line_to_tropical(line: Line) -> float:
        """Map a line to its tropical value.

        Yin → 0.0, Yang → 1.0.
        Changing lines get a bonus weight: Old Yin → 0.5, Old Yang → 1.5.
        """
        if line == Line.YIN:
            return 0.0
        elif line == Line.YANG:
            return 1.0
        elif line == Line.OLD_YIN:
            return 0.5  # transitional — halfway
        else:  # OLD_YANG
            return 1.5

    @staticmethod
    def tropical_to_line(value: float) -> Line:
        """Map a tropical value back to the nearest line type."""
        if value < 0.25:
            return Line.YIN
        elif value < 0.75:
            return Line.OLD_YIN
        elif value < 1.25:
            return Line.YANG
        else:
            return Line.OLD_YANG

    @classmethod
    def tropical_max_line(cls, lines: List[Line]) -> int:
        """Find the 'superior' line index: the tropical maximum.

        Returns the index of the line with the highest tropical value.
        In case of ties, returns the lower index (closer to base).
        """
        best_idx = 0
        best_val = cls.line_to_tropical(lines[0])
        for i in range(1, len(lines)):
            val = cls.line_to_tropical(lines[i])
            if val > best_val:
                best_val = val
                best_idx = i
        return best_idx

    @classmethod
    def tropical_polynomial(cls, h: Hexagram, coefficients: Optional[List[float]] = None) -> float:
        """Evaluate the hexagram as a tropical polynomial.

        Each line contributes a term. The tropical polynomial is:
        P(h) = ⊕ᵢ (cᵢ ⊗ xᵢ) = max_i (cᵢ + xᵢ)

        where xᵢ is the tropical value of line i and cᵢ is the coefficient.
        Default coefficients weight by line position (top lines = more weight).
        """
        if coefficients is None:
            # Default: weight top lines more (positions 3,4,5 heavier)
            coefficients = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]

        terms = []
        for i, line in enumerate(h.lines):
            x_i = cls.line_to_tropical(line)
            c_i = coefficients[i]
            terms.append(cls.tropical_multiply(c_i, x_i))

        # Tropical sum = max of all terms
        return max(terms) if terms else 0.0

    @classmethod
    def tropical_transform(cls, h: Hexagram, changes: List[int]) -> Hexagram:
        """Transform a hexagram using tropical line changes.

        For each change index, the line is upgraded via tropical max:
        - If the line is yin, changing it → yang (0 ⊕ 1 = max(0,1) = 1)
        - If the line is yang, changing it → yin is modeled as tropical min

        The transformation captures the direction of change: some changes
        are "upgrades" (yin→yang) and some are "downgrades" (yang→yin).
        In tropical terms, upgrades dominate (the max wins).
        """
        new_lines = list(h.lines)
        for idx in changes:
            if idx < 0 or idx >= 6:
                raise ValueError(f"Line index must be 0-5, got {idx}")
            current = new_lines[idx]
            # Tropical flip: compute the complement
            if current.is_yang:
                new_lines[idx] = Line.YIN
            else:
                new_lines[idx] = Line.YANG
        return Hexagram(new_lines)

    @classmethod
    def tropical_distance(cls, h1: Hexagram, h2: Hexagram) -> float:
        """Tropical distance between two hexagrams.

        Sum of tropical absolute differences across all lines.
        Uses tropical values for each line.
        """
        dist = 0.0
        for l1, l2 in zip(h1.lines, h2.lines):
            dist += abs(cls.line_to_tropical(l1) - cls.line_to_tropical(l2))
        return dist

    @classmethod
    def tropical_evolution(cls, h: Hexagram, steps: int = 6) -> List[Hexagram]:
        """Compute the tropical evolution of a hexagram.

        At each step, change the line with the highest tropical value
        (the "dominant" line). This simulates tropical polynomial
        dynamics where the max operator drives evolution.
        """
        path = [h]
        current = h
        changed_indices: set = set()

        for _ in range(steps):
            lines = current.lines
            # Find best line to change (not already changed, prefer high tropical value)
            best_idx = -1
            best_val = -1.0
            for i, line in enumerate(lines):
                val = cls.line_to_tropical(line)
                if i not in changed_indices and val >= best_val:
                    best_val = val
                    best_idx = i

            if best_idx == -1:
                # All lines changed, reset
                changed_indices.clear()
                best_idx = cls.tropical_max_line(current.lines)

            current = current.flip_line(best_idx)
            changed_indices.add(best_idx)
            path.append(current)

        return path

    @classmethod
    def tropical_rank(cls, h: Hexagram) -> float:
        """The tropical rank of a hexagram.

        The tropical rank measures how 'yang-dominant' a hexagram is.
        It's the tropical sum (max) of all line values, weighted by position.
        """
        return cls.tropical_polynomial(h)
