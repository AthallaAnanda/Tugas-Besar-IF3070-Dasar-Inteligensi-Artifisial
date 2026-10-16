"""Perilaku Steepest Ascent pada state valid dan batas berhenti."""

import unittest

from src.algorithms.hill_climbing import steepest_ascent
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def empty_deck(vehicles):
    return State([ShipState(Ship("s", 2, 1, 2))], {v.id: v for v in vehicles})


class SteepestAscentTests(unittest.TestCase):
    def test_chooses_best_neighbor_and_keeps_initial_state(self):
        initial = empty_deck([
            Vehicle("A", 1, 1, 10, 1, 0),
            Vehicle("B", 1, 1, 20, 1, 0),
        ])
        result = steepest_ascent(initial, objective_1, generate_neighbors,
                                 {"max_iterations": 1})

        self.assertTrue(is_valid(result["best_state"]))
        self.assertEqual(result["best_value"], 20)
        self.assertIs(result["best_state"], result["final_state"])
        self.assertIsNot(result["initial_state"], initial)
        self.assertEqual(result["initial_state"].to_dict(), initial.to_dict())
        self.assertEqual(result["history"], [0, 20])
        self.assertEqual(result["iterations"], 1)
        self.assertGreaterEqual(result["duration"], 0)
        self.assertEqual(initial.outside_vehicle_ids, {"A", "B"})

    def test_stops_without_neighbor_or_improvement(self):
        no_vehicle = empty_deck([])
        result = steepest_ascent(no_vehicle, objective_1, generate_neighbors)
        self.assertEqual(result["history"], [0, 0])
        self.assertEqual(result["iterations"], 1)
        self.assertEqual(result["best_state"].to_dict(), no_vehicle.to_dict())

        single = State.from_dict({
            "vehicles": [vars(Vehicle("A", 1, 1, 10, 1, 0))],
            "ships": [{"id": "s", "width": 1, "length": 1, "max_capacity": 1,
                       "placements": [{"vehicle_id": "A", "ship_id": "s", "x": 0, "y": 0}]}],
        })
        result = steepest_ascent(single, objective_1, generate_neighbors)
        self.assertEqual(result["best_value"], 10)
        self.assertEqual(result["history"], [10, 10])
        self.assertEqual(result["iterations"], 1)

    def test_finds_both_vehicles_before_stopping(self):
        initial = empty_deck([
            Vehicle("A", 1, 1, 10, 1, 0),
            Vehicle("B", 1, 1, 20, 1, 0),
        ])
        result = steepest_ascent(initial, objective_1, generate_neighbors)
        self.assertEqual(result["best_value"], 30)
        self.assertEqual(result["iterations"], 3)
        self.assertEqual(result["history"], [0, 20, 30, 30])
        self.assertEqual(result["best_state"].outside_vehicle_ids, set())

    def test_rejects_invalid_iteration_limit(self):
        for limit in (0, -1, 1.5, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                steepest_ascent(empty_deck([]), objective_1, generate_neighbors,
                                 {"max_iterations": limit})
