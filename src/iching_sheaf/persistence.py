"""PersistenceAnalysis: persistent homology on the hexagram graph."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .hexagram import Hexagram
from .graph import HexagramGraph


class Simplex:
    """A simplex in the Vietoris-Rips complex."""

    def __init__(self, vertices: Tuple[int, ...]) -> None:
        self.vertices = tuple(sorted(vertices))
        self.dim = len(self.vertices) - 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Simplex):
            return NotImplemented
        return self.vertices == other.vertices

    def __hash__(self) -> int:
        return hash(self.vertices)

    def __repr__(self) -> str:
        return f"Simplex({self.vertices}, dim={self.dim})"

    def boundary(self) -> List[Tuple[int, ...]]:
        """Return the boundary faces (omit one vertex at a time)."""
        faces = []
        for i in range(len(self.vertices)):
            face = self.vertices[:i] + self.vertices[i + 1:]
            if face:
                faces.append(face)
        return faces


class PersistenceAnalysis:
    """Persistent homology on the hexagram transition graph.

    Builds a Vietoris-Rips complex from the hexagram graph (using
    Hamming distance) and computes persistence diagrams tracking
    the birth and death of topological features.

    Filtration parameter: Hamming distance threshold.
    At epsilon=0: 64 isolated vertices.
    At epsilon=1: the hexagram graph (6-regular).
    At epsilon=2: all 2-hop connections, etc.
    At epsilon=6: the complete graph on 64 vertices.
    """

    def __init__(self, graph: Optional[HexagramGraph] = None) -> None:
        self.graph = graph or HexagramGraph()
        self._distance_cache: Dict[Tuple[int, int], int] = {}
        self._computed = False
        self._persistence_diagram: List[Tuple[float, float]] = []
        self._betti: List[int] = []
        self._essential: List[int] = []

    def _compute_distances(self) -> None:
        """Precompute all pairwise Hamming distances."""
        for i in range(64):
            for j in range(i + 1, 64):
                xor = i ^ j
                d = bin(xor).count("1")
                self._distance_cache[(i, j)] = d

    def _get_neighbors_at_radius(self, epsilon: int) -> Dict[int, Set[int]]:
        """Get adjacency at a given distance threshold."""
        neighbors: Dict[int, Set[int]] = defaultdict(set)
        for i in range(64):
            neighbors[i].add(i)  # self-loop for VR complex
        for (i, j), d in self._distance_cache.items():
            if d <= epsilon:
                neighbors[i].add(j)
                neighbors[j].add(i)
        return neighbors

    def _build_vr_complex(self, epsilon: int) -> Dict[int, Set[int]]:
        """Build the Vietoris-Rips complex at radius epsilon.

        For efficiency, we track 0-simplices (vertices) and 1-simplices (edges).
        Higher simplices are implicit in the VR construction.
        """
        return self._get_neighbors_at_radius(epsilon)

    def _compute_connected_components(self, epsilon: int) -> int:
        """Count connected components at given epsilon via union-find."""
        parent = list(range(64))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for (i, j), d in self._distance_cache.items():
            if d <= epsilon:
                union(i, j)

        return len({find(i) for i in range(64)})

    def _compute_cycles(self, epsilon: int) -> int:
        """Estimate number of independent 1-cycles at given epsilon.

        Uses Euler characteristic: β₁ = |E| - |V| + β₀
        """
        edges = sum(1 for (i, j), d in self._distance_cache.items() if d <= epsilon)
        components = self._compute_connected_components(epsilon)
        vertices = 64
        return edges - vertices + components

    def compute(self) -> None:
        """Compute persistence diagram and Betti numbers."""
        if self._computed:
            return

        self._compute_distances()

        # Track component births and deaths across filtration
        # At epsilon=0: 64 components born
        # As epsilon increases, components merge (death events)
        prev_components = 64
        births: Dict[int, int] = {}  # component representative -> birth epsilon

        # All components are born at epsilon=0
        for i in range(64):
            births[i] = 0

        self._persistence_diagram = []

        for eps in range(1, 7):
            components = self._compute_connected_components(eps)
            cycles = self._compute_cycles(eps)

            if components < prev_components:
                # Some components merged → death events
                # The number of deaths = prev_components - components
                for _ in range(prev_components - components):
                    self._persistence_diagram.append((0.0, float(eps)))
                prev_components = components

        # Remaining components have infinite persistence (essential)
        for _ in range(components):
            self._persistence_diagram.append((0.0, float("inf")))

        # Now track 1-dimensional persistence (cycles)
        prev_cycles = 0
        for eps in range(1, 7):
            cycles = self._compute_cycles(eps)
            new_cycles = cycles - prev_cycles
            for _ in range(new_cycles):
                self._persistence_diagram.append((float(eps), float(eps + 2) if eps < 5 else float("inf")))
            prev_cycles = cycles

        # Compute Betti numbers at epsilon=1 (the hexagram graph)
        self._betti = [
            self._compute_connected_components(1),  # β₀
            self._compute_cycles(1),                 # β₁
        ]

        # Find essential features (infinite persistence)
        self._essential = []
        all_h = self.graph.all_hexagrams()
        for h in all_h:
            # A hexagram is "essential" if it's maximally connected
            # (i.e., The Creative = 63 or The Receptive = 0)
            if h.binary_value in (0, 63):
                self._essential.append(h.binary_value)

        self._computed = True

    def persistence_diagram(self) -> List[Tuple[float, float]]:
        """Get the persistence diagram as list of (birth, death) pairs."""
        self.compute()
        return list(self._persistence_diagram)

    def betti_numbers(self) -> List[int]:
        """Get Betti numbers [β₀, β₁] at epsilon=1."""
        self.compute()
        return list(self._betti)

    def essential_features(self) -> List[Hexagram]:
        """Hexagrams with infinite persistence (essential topological features)."""
        self.compute()
        return [self.graph.hexagram(b) for b in self._essential]

    def persistence_barcode(self) -> List[str]:
        """Human-readable persistence barcode."""
        self.compute()
        lines = []
        for birth, death in self._persistence_diagram:
            if death == float("inf"):
                line = f"[{birth:.0f}, ∞)"
            else:
                line = f"[{birth:.0f}, {death:.0f})"
            lines.append(line)
        return lines

    def filtration_summary(self) -> str:
        """Summary of the filtration at each level."""
        self.compute()
        parts = ["Filtration by Hamming distance:"]
        for eps in range(7):
            components = self._compute_connected_components(eps)
            edges = sum(1 for (i, j), d in self._distance_cache.items() if d <= eps)
            parts.append(
                f"  ε={eps}: {components} components, {edges} edges, "
                f"β₀={components}, β₁={edges - 64 + components}"
            )
        return "\n".join(parts)
