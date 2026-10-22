
import random
import unittest
from unittest.mock import patch

from src.core.constraint import is_valid
from src.core.neighbor import NoNeighborError, generate_neighbors, random_neighbor
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def test_swap_move_rotate_and_load_outside_without_mutating_source():
    vehicles = [Vehicle("A", 2, 1, 10, 1, 0), Vehicle("B", 1, 1, 20, 1, 0),
                Vehicle("C", 1, 1, 30, 1, 0)]
    state = State([ShipState(Ship("s", 4, 3, 3), [
        Placement("A", "s", 0, 0), Placement("B", "s", 2, 0)
    ])], {v.id: v for v in vehicles})
    neighbors = list(generate_neighbors(state))
    assert neighbors and all(is_valid(candidate) for candidate in neighbors)
    assert all(candidate is not state for candidate in neighbors)
    assert len({tuple(sorted(str(p) for p in c.ships[0].placements)) for c in neighbors}) == len(neighbors)
    assert any({p.vehicle_id for p in c.ships[0].placements} == {"A", "B", "C"}
               for c in neighbors)
    assert any({p.vehicle_id for p in c.ships[0].placements} == {"A", "C"} for c in neighbors)
    assert any({p.vehicle_id for p in c.ships[0].placements} == {"A", "B"}
               and next(p for p in c.ships[0].placements if p.vehicle_id == "A").x == 2
               for c in neighbors)
    assert all(len(c.ships[0].placements) >= 2 for c in neighbors)
    assert any(any(p.vehicle_id == "A" and p.orientation == "vertical"
                   for p in c.ships[0].placements) for c in neighbors)
    assert any(any(p.vehicle_id == "A" and p.x == 1
                   for p in c.ships[0].placements) for c in neighbors)
    assert state.outside_vehicle_ids == {"C"}
    assert [(p.vehicle_id, p.x, p.y) for p in state.ships[0].placements] == [
        ("A", 0, 0), ("B", 2, 0)
    ]
    assert is_valid(random_neighbor(state))


class RandomNeighborTests(unittest.TestCase):
    def test_returns_one_valid_state_without_building_all_neighbors(self):
        vehicle = Vehicle("A", 1, 1, 10, 1, 0)
        state = State([ShipState(Ship("s", 4, 3, 1))], {vehicle.id: vehicle})
        original = state.to_dict()

        with patch("src.core.neighbor.generate_neighbors", side_effect=AssertionError(
                "Sampler tidak boleh membuat seluruh neighbor")), patch.object(
                State, "copy", autospec=True, side_effect=State.copy) as copies:
            neighbor = random_neighbor(state, random.Random(7))

        self.assertEqual(copies.call_count, 1)
        self.assertTrue(is_valid(neighbor))
        self.assertNotEqual(neighbor.to_dict(), original)
        self.assertEqual(state.to_dict(), original)
        self.assertEqual(neighbor.to_dict(), random_neighbor(state, random.Random(7)).to_dict())

    def test_samples_only_allowed_neighbors_with_multiple_ships(self):
        vehicles = [Vehicle(name, 1, 1, 10, 1, 0) for name in ("A", "B", "C")]
        state = State([
            ShipState(Ship("s1", 2, 2, 2), [Placement("A", "s1", 0, 0)]),
            ShipState(Ship("s2", 2, 2, 2), [Placement("B", "s2", 0, 0)]),
        ], {vehicle.id: vehicle for vehicle in vehicles})
        original = state.to_dict()
        allowed = {frozenset(p for ship in neighbor.ships for p in ship.placements)
                   for neighbor in generate_neighbors(state)}
        for seed in range(10):
            neighbor = random_neighbor(state, random.Random(seed))
            self.assertTrue(is_valid(neighbor))
            self.assertIn(frozenset(p for ship in neighbor.ships for p in ship.placements), allowed)
        self.assertEqual(state.to_dict(), original)

    def test_distinguishes_no_neighbor_from_invalid_state(self):
        empty = State([ShipState(Ship("s", 1, 1, 1))], {})
        with self.assertRaises(NoNeighborError):
            random_neighbor(empty)

        vehicle = Vehicle("A", 1, 1, 10, 1, 0)
        invalid = State([ShipState(Ship("s", 1, 1, 1), [Placement("A", "s", 1, 0)])],
                        {vehicle.id: vehicle})
        with self.assertRaises(ValueError) as error:
            random_neighbor(invalid)
        self.assertNotIsInstance(error.exception, NoNeighborError)
