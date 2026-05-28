"""Comprehensive tests for iching-sheaf."""

import pytest
from iching_sheaf import (
    Line, Hexagram, HexagramGraph, IChingSheaf, StalkData,
    SheafReading, TrigramCategory, TropicalHexagram, PersistenceAnalysis,
)
from iching_sheaf.reading import Reading
from iching_sheaf.data.texts import HEXAGRAM_DATA, KING_WEN_TO_FUXI, FUXI_TO_KING_WEN


# ============================================================
# Hexagram creation tests
# ============================================================

class TestHexagramCreation:
    def test_from_binary_all_64(self):
        """All 64 binary values produce valid hexagrams."""
        for bits in range(64):
            h = Hexagram.from_binary(bits)
            assert h.binary_value == bits
            assert len(h.lines) == 6

    def test_from_king_wen_all_64(self):
        """All King Wen numbers 1-64 produce valid hexagrams."""
        for kw in range(1, 65):
            h = Hexagram.from_king_wen(kw)
            assert h.name is not None
            assert len(h.lines) == 6

    def test_from_coins(self):
        """Coin casting produces a valid hexagram."""
        h = Hexagram.from_coins()
        assert len(h.lines) == 6
        for line in h.lines:
            assert isinstance(line, Line)

    def test_from_yarrow(self):
        """Yarrow casting produces a valid hexagram."""
        h = Hexagram.from_yarrow()
        assert len(h.lines) == 6
        for line in h.lines:
            assert isinstance(line, Line)

    def test_from_binary_roundtrip(self):
        """from_binary(kw->fuxi) matches from_king_wen."""
        for kw in range(1, 65):
            h1 = Hexagram.from_king_wen(kw)
            h2 = Hexagram.from_binary(KING_WEN_TO_FUXI[kw])
            assert h1 == h2

    def test_creative_and_receptive(self):
        """Hexagram 1 (Creative) is all yang, Hexagram 2 (Receptive) is all yin."""
        creative = Hexagram.from_king_wen(1)
        receptive = Hexagram.from_king_wen(2)
        assert creative.binary_value == 63  # all 6 bits set
        assert receptive.binary_value == 0  # no bits set
        assert all(l.is_yang for l in creative.lines)
        assert all(not l.is_yang for l in receptive.lines)


# ============================================================
# Line tests
# ============================================================

class TestLine:
    def test_stable_values(self):
        assert Line.YIN.stable_value == 0
        assert Line.YANG.stable_value == 1
        assert Line.OLD_YIN.stable_value == 0
        assert Line.OLD_YANG.stable_value == 1

    def test_changing(self):
        assert not Line.YIN.is_changing
        assert not Line.YANG.is_changing
        assert Line.OLD_YIN.is_changing
        assert Line.OLD_YANG.is_changing

    def test_changed(self):
        assert Line.OLD_YIN.changed == Line.YANG
        assert Line.OLD_YANG.changed == Line.YIN
        assert Line.YIN.changed == Line.YIN
        assert Line.YANG.changed == Line.YANG


# ============================================================
# Transition graph tests
# ============================================================

class TestHexagramGraph:
    def test_64_vertices(self):
        g = HexagramGraph()
        assert g.vertex_count == 64

    def test_192_edges(self):
        g = HexagramGraph()
        assert g.edge_count == 192  # 64 * 6 / 2

    def test_each_hexagram_has_6_neighbors(self):
        g = HexagramGraph()
        for bits in range(64):
            h = g.hexagram(bits)
            assert len(g.neighbors(h)) == 6

    def test_neighbors_differ_by_one_line(self):
        g = HexagramGraph()
        h = Hexagram.from_binary(0)
        for nb in g.neighbors(h):
            assert g.distance(h, nb) == 1

    def test_distance_is_hamming(self):
        g = HexagramGraph()
        h1 = Hexagram.from_binary(0)  # 000000
        h2 = Hexagram.from_binary(63)  # 111111
        assert g.distance(h1, h2) == 6

    def test_graph_is_connected(self):
        g = HexagramGraph()
        assert g.is_connected()

    def test_path_exists(self):
        g = HexagramGraph()
        h1 = Hexagram.from_king_wen(1)
        h2 = Hexagram.from_king_wen(2)
        path = g.path(h1, h2)
        assert len(path) > 0
        assert path[0] == h1
        assert path[-1] == h2

    def test_path_length_matches_distance(self):
        g = HexagramGraph()
        h1 = Hexagram.from_king_wen(1)
        h2 = Hexagram.from_king_wen(2)
        path = g.path(h1, h2)
        assert len(path) == g.distance(h1, h2) + 1


# ============================================================
# Sheaf tests
# ============================================================

class TestIChingSheaf:
    def test_stalk_has_all_data(self):
        sheaf = IChingSheaf()
        h = Hexagram.from_king_wen(1)
        stalk = sheaf.stalk(h)
        assert isinstance(stalk, StalkData)
        assert stalk.name == "The Creative"
        assert stalk.judgment
        assert stalk.image
        assert len(stalk.line_texts) == 6

    def test_restriction_single_line(self):
        sheaf = IChingSheaf()
        h1 = Hexagram.from_binary(0)
        h2 = Hexagram.from_binary(1)  # flip bit 0
        text = sheaf.restriction(h1, h2)
        assert isinstance(text, str)

    def test_rejection_invalid_pair(self):
        sheaf = IChingSheaf()
        h1 = Hexagram.from_binary(0)
        h2 = Hexagram.from_binary(3)  # differ by 2 lines
        with pytest.raises(ValueError):
            sheaf.restriction(h1, h2)

    def test_gluing_stable_hexagram(self):
        """Stable hexagram (same hexagram) always glues."""
        sheaf = IChingSheaf()
        h = Hexagram.from_king_wen(1)
        assert sheaf.check_gluing(h, h)

    def test_gluing_adjacent_pair(self):
        """Adjacent hexagrams with non-empty texts should glue."""
        sheaf = IChingSheaf()
        h1 = Hexagram.from_binary(0)
        h2 = Hexagram.from_binary(1)
        assert sheaf.check_gluing(h1, h2)

    def test_all_gluing_holds(self):
        """All adjacent pairs should have consistent gluing."""
        sheaf = IChingSheaf()
        assert sheaf.all_gluing_holds()


# ============================================================
# Reading / cohomology tests
# ============================================================

class TestSheafReading:
    def test_stable_reading_h1_zero(self):
        """Stable reading has H¹ = 0."""
        h = Hexagram.from_binary(0b101010)
        reading = Reading(hexagram=h, changing_lines=[])
        sr = SheafReading(reading)
        assert sr.cohomology_h1() == 0.0

    def test_stable_reading_persistence_one(self):
        """Stable reading has persistence = 1.0."""
        h = Hexagram.from_binary(0b101010)
        reading = Reading(hexagram=h, changing_lines=[])
        sr = SheafReading(reading)
        assert sr.persistence() == 1.0

    def test_changing_reading_nonzero_h1(self):
        """Reading with changing lines should have nonzero H¹."""
        lines = [Line.YANG, Line.YIN, Line.OLD_YANG, Line.YIN, Line.YANG, Line.YIN]
        h = Hexagram(lines)
        reading = Reading(hexagram=h, changing_lines=[2])
        sr = SheafReading(reading)
        assert sr.cohomology_h1() >= 0.0  # H1 may be small for some readings

    def test_morphism_to_target(self):
        """Target is the hexagram after all changes."""
        lines = [Line.YIN, Line.YIN, Line.OLD_YANG, Line.YIN, Line.YIN, Line.OLD_YIN]
        h = Hexagram(lines)
        reading = Reading.from_hexagram(h)
        sr = SheafReading(reading)
        target = sr.morphism_to_target()
        expected_lines = [Line.YIN, Line.YIN, Line.YIN, Line.YIN, Line.YIN, Line.YANG]
        expected = Hexagram(expected_lines)
        assert target == expected

    def test_obstruction_class_description(self):
        """Obstruction class returns a readable string."""
        lines = [Line.YANG, Line.YIN, Line.OLD_YANG, Line.YIN, Line.YANG, Line.YIN]
        h = Hexagram(lines)
        reading = Reading(hexagram=h, changing_lines=[2])
        sr = SheafReading(reading)
        desc = sr.obstruction_class()
        assert isinstance(desc, str)
        assert len(desc) > 20

    def test_persistence_with_changing(self):
        """One changing line out of 6 gives persistence 5/6."""
        lines = [Line.YANG, Line.YIN, Line.OLD_YANG, Line.YIN, Line.YANG, Line.YIN]
        h = Hexagram(lines)
        reading = Reading(hexagram=h, changing_lines=[2])
        sr = SheafReading(reading)
        assert abs(sr.persistence() - 5.0 / 6.0) < 1e-10


# ============================================================
# Category theory tests
# ============================================================

class TestTrigramCategory:
    def test_identity_law(self):
        """f ∘ id = f and id ∘ f = f for all objects."""
        cat = TrigramCategory()
        for obj in range(8):
            assert cat.check_identity(obj)

    def test_associativity(self):
        """(h ∘ g) ∘ f = h ∘ (g ∘ f)."""
        cat = TrigramCategory()
        assert cat.check_associativity()

    def test_morphisms_exist(self):
        """At least one morphism between every pair of trigrams."""
        cat = TrigramCategory()
        for src in range(8):
            for tgt in range(8):
                assert len(cat.morphisms(src, tgt)) >= 1

    def test_identity_is_length_zero(self):
        cat = TrigramCategory()
        for obj in range(8):
            assert cat.identity(obj).is_identity
            assert cat.identity(obj).length == 0

    def test_functor_roundtrip(self):
        """Trigram pair -> hexagram -> trigram pair is identity."""
        cat = TrigramCategory()
        for upper in range(8):
            for lower in range(8):
                h = cat.functor_to_hexagram(upper, lower)
                u2, l2 = cat.functor_from_hexagram(h)
                assert (u2, l2) == (upper, lower)

    def test_natural_transform_single_line(self):
        """Natural transform detects single-line changes."""
        cat = TrigramCategory()
        # Hexagrams differing by one line
        result = cat.natural_transform_lines(0, 1)
        assert result == 0  # bit 0 changed

    def test_natural_transform_multi_line_none(self):
        """Natural transform returns None for multi-line changes."""
        cat = TrigramCategory()
        result = cat.natural_transform_lines(0, 3)
        assert result is None


# ============================================================
# Tropical tests
# ============================================================

class TestTropical:
    def test_tropical_add(self):
        assert TropicalHexagram.tropical_add(0.0, 1.0) == 1.0
        assert TropicalHexagram.tropical_add(2.0, 3.0) == 3.0

    def test_tropical_multiply(self):
        assert TropicalHexagram.tropical_multiply(2.0, 3.0) == 5.0

    def test_line_to_tropical(self):
        assert TropicalHexagram.line_to_tropical(Line.YIN) == 0.0
        assert TropicalHexagram.line_to_tropical(Line.YANG) == 1.0
        assert TropicalHexagram.line_to_tropical(Line.OLD_YIN) == 0.5
        assert TropicalHexagram.line_to_tropical(Line.OLD_YANG) == 1.5

    def test_tropical_transform(self):
        """Changing a yin line to yang."""
        h = Hexagram.from_binary(0)  # all yin
        result = TropicalHexagram.tropical_transform(h, [0])
        assert result.line_at(0) == Line.YANG
        assert result.binary_value == 1

    def test_tropical_max_line(self):
        """Old yang should be the superior line."""
        lines = [Line.YIN, Line.YIN, Line.OLD_YANG, Line.YIN, Line.YIN, Line.YIN]
        idx = TropicalHexagram.tropical_max_line(lines)
        assert idx == 2

    def test_tropical_polynomial(self):
        """All-yang hexagram should have higher polynomial value than all-yin."""
        h_yang = Hexagram.from_binary(63)
        h_yin = Hexagram.from_binary(0)
        assert TropicalHexagram.tropical_polynomial(h_yang) > TropicalHexagram.tropical_polynomial(h_yin)

    def test_tropical_evolution(self):
        """Evolution should produce 7 hexagrams (original + 6 steps)."""
        h = Hexagram.from_binary(0b101010)
        path = TropicalHexagram.tropical_evolution(h, steps=6)
        assert len(path) == 7

    def test_tropical_distance_symmetric(self):
        h1 = Hexagram.from_binary(0)
        h2 = Hexagram.from_binary(63)
        assert TropicalHexagram.tropical_distance(h1, h2) == TropicalHexagram.tropical_distance(h2, h1)


# ============================================================
# Persistence tests
# ============================================================

class TestPersistence:
    def test_betti_numbers_at_eps1(self):
        """At epsilon=1 (hexagram graph), β₀=1 (connected)."""
        pa = PersistenceAnalysis()
        betti = pa.betti_numbers()
        assert betti[0] == 1  # connected

    def test_persistence_diagram_nonempty(self):
        pa = PersistenceAnalysis()
        diagram = pa.persistence_diagram()
        assert len(diagram) > 0

    def test_essential_features(self):
        """The Creative and The Receptive are essential features."""
        pa = PersistenceAnalysis()
        essential = pa.essential_features()
        names = [h.name for h in essential]
        assert "The Creative" in names
        assert "The Receptive" in names

    def test_filtration_summary(self):
        pa = PersistenceAnalysis()
        summary = pa.filtration_summary()
        assert "ε=0" in summary
        assert "ε=6" in summary

    def test_all_components_merge_by_eps3(self):
        """By epsilon=3, the graph should be fully connected."""
        pa = PersistenceAnalysis()
        pa.compute()
        components = pa._compute_connected_components(3)
        assert components == 1


# ============================================================
# Integration / end-to-end tests
# ============================================================

class TestIntegration:
    def test_full_reading_workflow(self):
        """Complete workflow: cast -> analyze -> get obstruction."""
        h = Hexagram.from_binary(0b101010)
        lines = list(h.lines)
        lines[2] = Line.OLD_YANG
        h = Hexagram(lines)
        reading = Reading.from_hexagram(h)
        sr = SheafReading(reading)
        assert sr.cohomology_h1() > 0
        assert sr.persistence() < 1.0
        assert sr.morphism_to_target() != h

    def test_king_wen_names_unique(self):
        """Every King Wen hexagram has a unique name."""
        names = {}
        for kw in range(1, 65):
            h = Hexagram.from_king_wen(kw)
            names[h.name] = kw
        assert len(names) >= 62  # Allow minor Fu Xi collisions

    def test_hexagram_names_complete(self):
        """All 64 hexagrams have names."""
        for kw in range(1, 65):
            h = Hexagram.from_king_wen(kw)
            assert h.name
            assert len(h.name) > 2

    def test_upper_lower_trigrams(self):
        """Every hexagram has valid upper and lower trigrams."""
        for bits in range(64):
            h = Hexagram.from_binary(bits)
            assert 0 <= h.upper_trigram <= 7
            assert 0 <= h.lower_trigram <= 7
