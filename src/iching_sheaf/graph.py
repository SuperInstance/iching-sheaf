"""HexagramGraph: the transition graph of all 64 hexagrams."""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .hexagram import Hexagram, Line


class HexagramGraph:
    """Graph of 64 hexagrams where edges connect hexagrams differing by one line.

    This forms the base space (topology) for the sheaf structure.
    Each hexagram has up to 6 neighbors (one for each possible line flip).
    """

    def __init__(self) -> None:
        self._hexagrams: Dict[int, Hexagram] = {}
        self._adj: Dict[int, List[int]] = {}
        self._build()

    def _build(self) -> None:
        # Create all 64 hexagrams
        for bits in range(64):
            h = Hexagram.from_binary(bits)
            self._hexagrams[bits] = h

        # Build adjacency: flip each of 6 bits
        for bits in range(64):
            neighbors = []
            for line_idx in range(6):
                neighbor_bits = bits ^ (1 << line_idx)
                neighbors.append(neighbor_bits)
            self._adj[bits] = neighbors

    def hexagram(self, binary: int) -> Hexagram:
        """Get a hexagram by its Fu Xi binary value."""
        return self._hexagrams[binary]

    def hexagram_by_kw(self, king_wen: int) -> Hexagram:
        """Get a hexagram by King Wen number."""
        from .data.texts import KING_WEN_TO_FUXI
        return self._hexagrams[KING_WEN_TO_FUXI[king_wen]]

    def all_hexagrams(self) -> List[Hexagram]:
        return list(self._hexagrams.values())

    def neighbors(self, h: Hexagram) -> List[Hexagram]:
        """Return the 6 hexagrams that differ from h by exactly one line."""
        return [self._hexagrams[nb] for nb in self._adj[h.binary_value]]

    def distance(self, h1: Hexagram, h2: Hexagram) -> int:
        """Minimum number of line changes to get from h1 to h2 (Hamming distance)."""
        xor = h1.binary_value ^ h2.binary_value
        return bin(xor).count("1")

    def path(self, h1: Hexagram, h2: Hexagram) -> List[Hexagram]:
        """Find a shortest path from h1 to h2 via BFS."""
        if h1 == h2:
            return [h1]
        visited: Set[int] = {h1.binary_value}
        queue: deque[Tuple[int, List[int]]] = deque()
        queue.append((h1.binary_value, [h1.binary_value]))
        while queue:
            current, path = queue.popleft()
            for nb in self._adj[current]:
                if nb == h2.binary_value:
                    return [self._hexagrams[b] for b in path + [nb]]
                if nb not in visited:
                    visited.add(nb)
                    queue.append((nb, path + [nb]))
        return []  # unreachable (shouldn't happen on connected graph)

    @property
    def vertex_count(self) -> int:
        return 64

    @property
    def edge_count(self) -> int:
        return 64 * 6 // 2  # each edge counted from both endpoints

    def is_connected(self) -> bool:
        """Check the graph is connected via BFS from hexagram 0."""
        visited: Set[int] = set()
        queue = deque([0])
        visited.add(0)
        while queue:
            current = queue.popleft()
            for nb in self._adj[current]:
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return len(visited) == 64

    def degree(self, h: Hexagram) -> int:
        """Degree of a hexagram (always 6 in this graph)."""
        return len(self._adj[h.binary_value])

    def euler_characteristic(self) -> int:
        """Euler characteristic of the graph (V - E)."""
        return self.vertex_count - self.edge_count

    def adjacency_matrix(self) -> List[List[int]]:
        """Return the 64x64 adjacency matrix."""
        n = 64
        mat = [[0] * n for _ in range(n)]
        for bits in range(n):
            for nb in self._adj[bits]:
                mat[bits][nb] = 1
        return mat
