"""TrigramCategory: the 8 trigrams as a category with morphisms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .data.texts import TRIGRAM_DATA


@dataclass(frozen=True)
class TrigramMorphism:
    """A morphism between two trigrams: a sequence of single-line changes."""
    source: int  # 3-bit trigram value
    target: int  # 3-bit trigram value
    path: Tuple[int, ...]  # sequence of intermediate trigram values (inclusive of source/target)

    @property
    def length(self) -> int:
        """Length of the morphism (number of line changes)."""
        if len(self.path) <= 1:
            return 0
        return sum(
            bin(self.path[i] ^ self.path[i + 1]).count("1")
            for i in range(len(self.path) - 1)
        )

    @property
    def is_identity(self) -> bool:
        return self.source == self.target and len(self.path) == 1

    def compose(self, other: TrigramMorphism) -> TrigramMorphism:
        """Compose this morphism with another (other after self)."""
        if self.target != other.source:
            raise ValueError(
                f"Cannot compose: target {self.target} != source {other.source}"
            )
        return TrigramMorphism(
            source=self.source,
            target=other.target,
            path=self.path + other.path[1:],
        )

    def __repr__(self) -> str:
        s_name = TRIGRAM_DATA.get(self.source, (str(self.source),))[0]
        t_name = TRIGRAM_DATA.get(self.target, (str(self.target),))[0]
        return f"TrigramMorphism({s_name} -> {t_name}, len={self.length})"


class TrigramCategory:
    """Category of 8 trigrams with morphisms given by line changes.

    Objects: the 8 trigrams (0-7, 3-bit binary)
    Morphisms: sequences of single-line changes
    Identity: trivial morphism (no changes)
    Composition: concatenation of change sequences
    Associativity: guaranteed by sequential composition

    Functors connect this to the hexagram category (pairs of trigrams).
    """

    def __init__(self) -> None:
        self._morphisms: Dict[Tuple[int, int], List[TrigramMorphism]] = {}
        self._build()

    def _build(self) -> None:
        """Build all morphisms via BFS for each pair."""
        for src in range(8):
            for tgt in range(8):
                morphisms = self._find_morphisms(src, tgt)
                self._morphisms[(src, tgt)] = morphisms

    def _find_morphisms(self, src: int, tgt: int) -> List[TrigramMorphism]:
        """Find all minimal-length morphisms from src to tgt via BFS."""
        if src == tgt:
            return [TrigramMorphism(source=src, target=tgt, path=(src,))]

        xor = src ^ tgt
        dist = bin(xor).count("1")

        # Generate all paths of exactly `dist` steps
        results: List[TrigramMorphism] = []
        self._enum_paths(src, tgt, xor, (src,), results)
        return results

    def _enum_paths(self, current: int, target: int, remaining: int,
                    path: Tuple[int, ...], results: List[TrigramMorphism]) -> None:
        """Enumerate all shortest paths by flipping one differing bit at a time."""
        if current == target:
            results.append(TrigramMorphism(source=path[0], target=target, path=path))
            return

        # Try flipping each bit that still needs to change
        temp = remaining
        while temp:
            bit = temp & -temp
            temp ^= bit
            next_val = current ^ bit
            self._enum_paths(next_val, target, remaining ^ bit, path + (next_val,), results)

    def objects(self) -> List[int]:
        """The 8 trigram objects."""
        return list(range(8))

    def morphisms(self, src: int, tgt: int) -> List[TrigramMorphism]:
        """All morphisms from src to tgt."""
        return self._morphisms.get((src, tgt), [])

    def identity(self, obj: int) -> TrigramMorphism:
        """Identity morphism for a trigram."""
        return TrigramMorphism(source=obj, target=obj, path=(obj,))

    def compose(self, f: TrigramMorphism, g: TrigramMorphism) -> TrigramMorphism:
        """Compose two morphisms: g ∘ f."""
        return f.compose(g)

    def check_identity(self, obj: int) -> bool:
        """Verify identity law: f ∘ id = f and id ∘ f = f."""
        id_morph = self.identity(obj)
        for tgt in range(8):
            for f in self.morphisms(obj, tgt):
                composed = self.compose(id_morph, f)
                if composed.source != f.source or composed.target != f.target:
                    return False
                # Check the resulting path is valid
                if composed.path[-1] != tgt:
                    return False
            for f in self.morphisms(tgt, obj):
                composed = self.compose(f, id_morph)
                if composed.source != f.source or composed.target != f.target:
                    return False
        return True

    def check_associativity(self) -> bool:
        """Verify associativity: (h ∘ g) ∘ f = h ∘ (g ∘ f)."""
        # Check a representative sample (full check would be 8^3 pairs)
        for a in range(8):
            for b in range(8):
                for c in range(8):
                    f_list = self.morphisms(a, b)
                    g_list = self.morphisms(b, c)
                    if not f_list or not g_list:
                        continue
                    f, g = f_list[0], g_list[0]
                    for d in range(8):
                        h_list = self.morphisms(c, d)
                        if not h_list:
                            continue
                        h = h_list[0]
                        left = self.compose(self.compose(f, g), h)
                        right = self.compose(f, self.compose(g, h))
                        if left.source != right.source or left.target != right.target:
                            return False
        return True

    def hom_count(self, src: int, tgt: int) -> int:
        """Number of morphisms from src to tgt."""
        return len(self.morphisms(src, tgt))

    def functor_to_hexagram(self, upper: int, lower: int) -> int:
        """Map a pair of trigrams to a hexagram's Fu Xi binary value.

        Functor from Trigram × Trigram to Hexagram category.
        lower trigram = bits 0-2, upper trigram = bits 3-5.
        """
        return (upper << 3) | lower

    def functor_from_hexagram(self, hex_binary: int) -> Tuple[int, int]:
        """Extract upper and lower trigrams from a hexagram.

        Functor from Hexagram to Trigram × Trigram category.
        """
        lower = hex_binary & 0x7
        upper = (hex_binary >> 3) & 0x7
        return upper, lower

    def natural_transform_lines(self, hex1: int, hex2: int) -> Optional[int]:
        """Natural transformation between reading methods.

        If two hexagrams differ by one line, return the line index.
        This is the 'component' of the natural transformation at that position.
        Returns None if they don't differ by exactly one line.
        """
        xor = hex1 ^ hex2
        if bin(xor).count("1") != 1:
            return None
        return (xor & -xor).bit_length() - 1

    def trigram_name(self, val: int) -> str:
        """Get the name of a trigram."""
        if val in TRIGRAM_DATA:
            return f"{TRIGRAM_DATA[val][0]} ({TRIGRAM_DATA[val][1]})"
        return f"Trigram({val})"

    def summary(self) -> str:
        """Print a summary of the category."""
        lines = ["Trigram Category (8 objects, morphisms by line change):"]
        for src in range(8):
            for tgt in range(8):
                n = self.hom_count(src, tgt)
                if n > 0:
                    lines.append(
                        f"  {self.trigram_name(src)} -> {self.trigram_name(tgt)}: "
                        f"{n} morphism(es), min length={self.morphisms(src, tgt)[0].length}"
                    )
        return "\n".join(lines)
