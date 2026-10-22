"""Pengujian SA: penerimaan, temperatur, e^(delta E/T), dan validasi."""

import math
import random
import unittest

from src.algorithms.simulated_annealing import (
    sample_neighbor,
    simulated_annealing,
)
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def empty_deck(vehicles):
    return State(
        [ShipState(Ship("s", 2, 1, 2))],
        {v.id: v for v in vehicles},
    )


def make_loaded_states():
    initial = empty_deck([
        Vehicle("A", 1, 1, 10, 1, 0),
        Vehicle("B", 1, 1, 1, 1, 0),
    ])
    initial.ships[0].placements.append(
        Placement("A", "s", 0, 0)
    )

    worse = initial.copy()
    worse.ships[0].placements[0] = Placement(
        "B", "s", 0, 0
    )

    return initial, worse


class SimulatedAnnealingTests(unittest.TestCase):
    def test_accepts_better_neighbor_and_keeps_initial_state(self):
        initial = empty_deck([
            Vehicle("A", 1, 1, 10, 1, 0),
        ])
        before = initial.copy()

        result = simulated_annealing(
            initial,
            objective_1,
            generate_neighbors,
            {
                "max_iterations": 1,
                "seed": 42,
            },
        )

        self.assertTrue(is_valid(result["best_state"]))
        self.assertEqual(result["best_value"], 10)
        self.assertEqual(
            result["final_state"],
            result["best_state"],
        )
        self.assertEqual(result["final_value"], 10)

        self.assertEqual(result["initial_state"], before)
        self.assertIsNot(result["initial_state"], initial)
        self.assertEqual(initial, before)
        self.assertEqual(initial.outside_vehicle_ids, {"A"})

        self.assertEqual(result["history"], [0, 10])
        self.assertEqual(result["iterations"], 1)
        self.assertEqual(result["stuck_count"], 0)
        self.assertEqual(result["accept_worse"], 0)
        self.assertGreaterEqual(result["duration"], 0)

    def test_accepts_equal_value_move(self):
        initial, _ = make_loaded_states()

        moved = initial.copy()
        moved.ships[0].placements[0] = Placement(
            "A", "s", 1, 0
        )

        result = simulated_annealing(
            initial,
            objective_1,
            lambda state: iter([moved.copy()]),
            {
                "max_iterations": 1,
                "seed": 42,
            },
        )

        self.assertEqual(result["terminal_state"], moved)
        self.assertEqual(result["history"], [10, 10])
        self.assertEqual(result["e_deltaet_history"], [1.0])
        self.assertEqual(result["log_e_deltaet_history"], [0.0])
        self.assertEqual(result["accept_worse"], 0)
        self.assertEqual(result["stuck_count"], 1)

    def test_temperature_controls_worse_move_and_preserves_best(self):
        initial, worse = make_loaded_states()
        before = initial.copy()

        cases = [
            (1e9, 1, 1),     # Kandidat lebih buruk diterima.
            (0.01, 10, 0),   # Kandidat lebih buruk ditolak.
        ]

        for temperature, terminal, accepted in cases:
            with self.subTest(temperature=temperature):
                result = simulated_annealing(
                    initial,
                    objective_1,
                    lambda state: iter([worse.copy()]),
                    {
                        "max_iterations": 1,
                        "initial_temperature": temperature,
                        "seed": 42,
                    },
                )

                exponent = (1 - 10) / temperature

                self.assertTrue(is_valid(result["terminal_state"]))
                self.assertEqual(result["terminal_value"], terminal)
                self.assertEqual(
                    result["history"],
                    [10, terminal],
                )
                self.assertEqual(result["accept_worse"], accepted)

                self.assertEqual(result["best_value"], 10)
                self.assertEqual(result["best_state"], initial)
                self.assertEqual(result["best_history"], [10, 10])
                self.assertEqual(result["stuck_count"], 1)

                # Tetap dicatat ketika kandidat ditolak.
                self.assertEqual(
                    len(result["e_deltaet_history"]),
                    1,
                )
                self.assertAlmostEqual(
                    result["e_deltaet_history"][0],
                    math.exp(exponent),
                )
                self.assertEqual(
                    result["log_e_deltaet_history"],
                    [exponent],
                )
                self.assertEqual(initial, before)

    def test_sample_neighbor_checks_all_neighbors_for_improvement(self):
        initial, worse = make_loaded_states()

        better = initial.copy()
        better.ships[0].placements.append(
            Placement("B", "s", 1, 0)
        )

        class KeepFirstRng:
            def randrange(self, count):
                return count - 1

        candidate, value, has_improvement = sample_neighbor(
            initial,
            10,
            objective_1,
            lambda state: iter([worse, better]),
            KeepFirstRng(),
        )

        # Kandidat terpilih lebih buruk, tetapi ada neighbor lain
        # yang lebih baik. Jadi has_improvement harus tetap True.
        self.assertEqual(candidate, worse)
        self.assertIsNot(candidate, worse)
        self.assertEqual(value, 1)
        self.assertTrue(has_improvement)

    def test_stops_without_neighbor(self):
        initial = empty_deck([])

        result = simulated_annealing(
            initial,
            objective_1,
            generate_neighbors,
        )

        self.assertEqual(result["iterations"], 0)
        self.assertEqual(result["history"], [0])
        self.assertEqual(result["best_state"], initial)
        self.assertEqual(result["stuck_count"], 1)
        self.assertEqual(result["e_deltaet_history"], [])
        self.assertEqual(result["log_e_deltaet_history"], [])

    def test_stopping_conditions(self):
        cases = [
            (1, 100, 3),     # Temperatur 8 -> 4 -> 2 -> 1.
            (0.001, 2, 2),   # Batas iterasi tercapai.
            (0.001, 0, 0),   # Nol iterasi.
            (8, 100, 0),     # Temperatur awal sudah pada batas minimum.
        ]

        for minimum, limit, expected in cases:
            with self.subTest(
                minimum=minimum,
                limit=limit,
            ):
                initial = empty_deck([
                    Vehicle("A", 1, 1, 10, 1, 0),
                ])

                result = simulated_annealing(
                    initial,
                    objective_1,
                    generate_neighbors,
                    {
                        "initial_temperature": 8,
                        "cooling_rate": 0.5,
                        "min_temperature": minimum,
                        "max_iterations": limit,
                        "seed": 42,
                    },
                )

                self.assertEqual(result["iterations"], expected)

                for key in (
                    "history",
                    "best_history",
                    "temperature_history",
                ):
                    self.assertEqual(
                        len(result[key]),
                        expected + 1,
                    )

                for key in (
                    "e_deltaet_history",
                    "log_e_deltaet_history",
                ):
                    self.assertEqual(
                        len(result[key]),
                        expected,
                    )

                self.assertEqual(
                    result["temperature_history"],
                    [
                        8 * 0.5 ** step
                        for step in range(expected + 1)
                    ],
                )

    def test_real_core_validity_and_seed_repeatability(self):
        initial = empty_deck([
            Vehicle("A", 1, 1, 10, 1, 0),
            Vehicle("B", 1, 1, 20, 1, 0),
        ])
        before = initial.copy()

        def checked_objective(state):
            self.assertTrue(is_valid(state))
            return objective_1(state)

        parameters = {
            "max_iterations": 5,
            "seed": 42,
        }

        first = simulated_annealing(
            initial,
            checked_objective,
            generate_neighbors,
            parameters,
        )
        second = simulated_annealing(
            initial,
            checked_objective,
            generate_neighbors,
            parameters,
        )

        self.assertEqual(initial, before)
        self.assertEqual(first["iterations"], 5)
        self.assertEqual(
            first["best_state"],
            second["best_state"],
        )

        for key in (
            "history",
            "best_history",
            "temperature_history",
            "e_deltaet_history",
            "log_e_deltaet_history",
        ):
            self.assertEqual(first[key], second[key])

        self.assertEqual(
            first["best_value"],
            objective_1(first["best_state"]),
        )
        self.assertEqual(
            first["terminal_value"],
            first["history"][-1],
        )
        self.assertEqual(
            first["terminal_value"],
            objective_1(first["terminal_state"]),
        )
        self.assertEqual(
            first["best_history"],
            sorted(first["best_history"]),
        )
        self.assertEqual(
            first["best_history"][-1],
            first["best_value"],
        )
        self.assertGreaterEqual(first["duration"], 0)

    def test_records_eet_before_cooling(self):
        initial = empty_deck([
            Vehicle("A", 1, 1, 10, 1, 0),
        ])

        result = simulated_annealing(
            initial,
            objective_1,
            generate_neighbors,
            {
                "initial_temperature": 10,
                "cooling_rate": 0.5,
                "max_iterations": 1,
                "seed": 42,
            },
        )

        # Delta = 10, temperatur evaluasi = 10.
        self.assertEqual(len(result["e_deltaet_history"]), 1)
        self.assertAlmostEqual(
            result["e_deltaet_history"][0],
            math.exp(1),
        )
        self.assertEqual(
            result["log_e_deltaet_history"],
            [1.0],
        )
        self.assertEqual(
            result["temperature_history"],
            [10, 5],
        )

    def test_large_positive_exponent_does_not_crash(self):
        initial = empty_deck([
            Vehicle("A", 1, 1, 1000, 1, 0),
        ])

        result = simulated_annealing(
            initial,
            objective_1,
            generate_neighbors,
            {
                "initial_temperature": 1,
                "max_iterations": 1,
                "seed": 42,
            },
        )

        self.assertTrue(
            math.isinf(result["e_deltaet_history"][0])
        )
        self.assertGreater(
            result["e_deltaet_history"][0],
            0,
        )
        self.assertEqual(
            result["log_e_deltaet_history"],
            [1000.0],
        )
        self.assertEqual(result["best_value"], 1000)

    def test_rejects_invalid_parameters(self):
        cases = [
            {"max_iterations": -1},
            {"max_iterations": 1.5},
            {"max_iterations": True},
            {"initial_temperature": 0},
            {"initial_temperature": -1},
            {"initial_temperature": float("inf")},
            {"initial_temperature": float("nan")},
            {"cooling_rate": 0},
            {"cooling_rate": 1},
            {"cooling_rate": float("nan")},
            {"min_temperature": 0},
            {"min_temperature": float("inf")},
            {"min_temperature": float("nan")},
        ]

        for parameters in cases:
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    simulated_annealing(
                        empty_deck([]),
                        objective_1,
                        generate_neighbors,
                        parameters,
                    )

    def test_rejects_invalid_initial_state(self):
        initial, _ = make_loaded_states()

        initial.ships[0].placements.append(
            Placement("B", "s", 0, 0)
        )

        self.assertFalse(is_valid(initial))

        with self.assertRaises(ValueError):
            simulated_annealing(
                initial,
                objective_1,
                generate_neighbors,
            )


if __name__ == "__main__":
    unittest.main()