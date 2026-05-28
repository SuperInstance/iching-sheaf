# iching-sheaf

The I Ching as a sheaf-theoretic system: hexagram topology, sheaf cohomology, category theory, tropical algebra, and persistent homology.

## Installation

```bash
pip install iching-sheaf
```

## Quick Start

```python
from iching_sheaf import Hexagram, HexagramGraph, IChingSheaf, SheafReading
from iching_sheaf.reading import Reading

# Cast a hexagram
h = Hexagram.from_coins()
print(h.name)

# Explore the transition graph
graph = HexagramGraph()
print(f"64 hexagrams, {graph.edge_count} edges")

# Sheaf structure
sheaf = IChingSheaf(graph)
stalk = sheaf.stalk(h)
print(stalk.judgment)

# Cohomological analysis
reading = Reading.from_hexagram(h)
analysis = SheafReading(reading, sheaf, graph)
print(f"H⁰ = {analysis.cohomology_h0()}")
print(f"H¹ = {analysis.cohomology_h1():.2f}")
print(f"Persistence = {analysis.persistence():.2f}")
print(analysis.obstruction_class())
```

## Architecture

- **Hexagram**: 64 hexagrams with Fu Xi binary mapping, casting methods (coins, yarrow)
- **HexagramGraph**: 6-regular graph of single-line transitions (base space for the sheaf)
- **IChingSheaf**: Stalks (text data) + restriction maps (line texts) + gluing conditions
- **SheafReading**: Cohomology (H⁰, H¹), obstruction classes, persistence of readings
- **TrigramCategory**: 8 trigrams as category objects with identity, composition, associativity
- **TropicalHexagram**: Line changes as tropical algebra (max-plus semiring)
- **PersistenceAnalysis**: Vietoris-Rips complex, persistence diagrams, Betti numbers

## License

MIT
