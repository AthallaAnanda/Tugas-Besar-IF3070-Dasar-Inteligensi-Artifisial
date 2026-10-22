"""Pengujian GA: roulette, crossover, mutasi, generasi, dan validasi."""

import math
import random
import unittest
from dataclasses import replace

from src.algorithms.genetic_algorithm import (
    crossover,
    genes,
    genetic_algorithm,
    mutate,
    select_parent,
)
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def make_state(placements=(), capacity=2):
    vehicles = [
        Vehicle("A", 1, 1, 10, 1, 0),
        Vehicle("B", 1, 1, 20, 1, 0),
    ]

    loaded = []
    for vehicle_id, x in placements:
        loaded.append(Placement(vehicle_id, "s", x, 0))

    return State(
        [ShipState(Ship("s", 2, 1, capacity), loaded)],
        {v.id: v for v in vehicles},
    )


def make_population():
    return [
        make_state(),                 # ShippingFee 0
        make_state([("A", 0)]),       # ShippingFee 10
        make_state([("B", 0)]),       # ShippingFee 20
    ]


class FixedRng:
    """Angka acak terkontrol untuk test roulette dan crossover."""

    def __init__(self, values):
        self.values = iter(values)

    def random(self):
        return next(self.values)

    def shuffle(self, items):
        pass


class GeneticAlgorithmTests(unittest.TestCase):
    def test_roulette_selects_correct_fitness_interval(self):
        population = make_population()

        # Fitness buatan untuk menguji perhitungan interval:
        # total 60, interval 0..10, 10..30, dan 30..60.
        cases = [
            (0.1, 0),
            (0.4, 1),
            (0.9, 2),
        ]

        for draw, expected in cases:
            with self.subTest(draw=draw):
                parent = select_parent(
                    population,
                    [10, 20, 30],
                    FixedRng([draw]),
                )

                self.assertIs(parent, population[expected])

    def test_roulette_handles_zero_fitness(self):
        population = make_population()

        # Seluruh fitness nol: tetap memilih anggota populasi.
        parent = select_parent(
            population,
            [0, 0, 0],
            random.Random(42),
        )

        self.assertTrue(
            any(parent is state for state in population)
        )

        # Hanya satu individu memiliki fitness positif.
        parent = select_parent(
            population,
            [0, 10, 0],
            FixedRng([0.0]),
        )

        self.assertIs(parent, population[1])

    def test_roulette_rejects_invalid_fitness(self):
        population = make_population()

        cases = [
            ([], []),
            (population, [10]),
            (population, [-1, 10, 20]),
            (population, [float("nan"), 10, 20]),
            (population, [float("inf"), 10, 20]),
            (population, [1e308, 1e308, 0]),
        ]

        for individuals, fitness in cases:
            with self.subTest(fitness=fitness):
                with self.assertRaises(ValueError):
                    select_parent(
                        individuals,
                        fitness,
                        random.Random(42),
                    )

    def test_roulette_returns_parent_despite_rounding(self):
        population = [make_state() for _ in range(11)]
        rng = FixedRng([math.nextafter(1.0, 0.0)])

        parent = select_parent(
            population,
            [1e16] + [1.0] * 10,
            rng,
        )

        self.assertTrue(
            any(parent is state for state in population)
        )

    def test_genes_only_contains_loaded_vehicles(self):
        state = make_state([("A", 0)])

        result = genes(state)

        self.assertEqual(set(result), {"A"})
        self.assertEqual(
            result["A"],
            state.ships[0].placements[0],
        )
        self.assertIsNone(result.get("B"))

    def test_crossover_repairs_overlap_and_capacity(self):
        cases = [
            (1, 2, {"A", "B"}),  # Keduanya muat.
            (0, 2, {"A"}),       # B bertumpuk dengan A.
            (1, 1, {"A"}),       # Berat total melampaui kapasitas.
        ]

        for position, capacity, expected in cases:
            with self.subTest(
                position=position,
                capacity=capacity,
            ):
                parent_a = make_state(
                    [("A", 0)],
                    capacity,
                )
                parent_b = make_state(
                    [("B", position)],
                    capacity,
                )

                before_a = parent_a.copy()
                before_b = parent_b.copy()

                # Urutan tetap A, B.
                # A diwarisi dari parent A, B dari parent B.
                child = crossover(
                    parent_a,
                    parent_b,
                    FixedRng([0.1, 0.9]),
                )

                self.assertTrue(is_valid(child))
                self.assertEqual(set(genes(child)), expected)
                self.assertEqual(
                    child.vehicles,
                    parent_a.vehicles,
                )
                self.assertEqual(parent_a, before_a)
                self.assertEqual(parent_b, before_b)

                # Perubahan child tidak boleh mengubah parent.
                child.ships[0].placements.clear()

                self.assertEqual(parent_a, before_a)
                self.assertEqual(parent_b, before_b)

    def test_mutation_uses_real_neighbor_and_keeps_initial_state(self):
        state = make_state([("A", 0)])
        before = state.copy()
        neighbors = list(generate_neighbors(state))

        self.assertTrue(neighbors)

        result = mutate(state, random.Random(42))

        self.assertTrue(is_valid(result))
        self.assertIn(result, neighbors)
        self.assertIsNot(result, state)
        self.assertEqual(state, before)

    def test_mutation_without_neighbors_returns_copy(self):
        state = make_state(capacity=0)

        self.assertEqual(list(generate_neighbors(state)), [])

        result = mutate(state, random.Random(42))

        self.assertEqual(result, state)
        self.assertIsNot(result, state)
        self.assertIsNot(
            result.ships[0].placements,
            state.ships[0].placements,
        )

    def test_preserves_initial_population_and_returns_best(self):
        population = make_population()[1:]
        before = [state.copy() for state in population]

        result = genetic_algorithm(
            lambda: population,
            objective_1,
            {
                "population_size": 2,
                "max_iterations": 1,
                "crossover_rate": 0,
                "mutation_rate": 0,
                "seed": 42,
            },
        )

        self.assertTrue(is_valid(result["best_state"]))
        self.assertEqual(result["best_value"], 20)
        self.assertEqual(
            result["final_state"],
            result["best_state"],
        )
        self.assertEqual(result["final_value"], 20)

        self.assertEqual(
            result["initial_state"],
            population[1],
        )
        self.assertIsNot(
            result["initial_state"],
            population[1],
        )
        self.assertEqual(population, before)

        self.assertEqual(result["history"], [20, 20])
        self.assertEqual(result["mean_history"], [15, 20])
        self.assertEqual(result["best_history"], [20, 20])
        self.assertEqual(result["iterations"], 1)
        self.assertGreaterEqual(result["duration"], 0)

    def test_finds_both_vehicles_and_repeats_with_same_seed(self):
        population = make_population()
        before = [state.copy() for state in population]
        evaluated = []

        def checked_objective(state):
            self.assertTrue(is_valid(state))
            evaluated.append(state.copy())
            return objective_1(state)

        parameters = {
            "population_size": 3,
            "max_iterations": 10,
            "crossover_rate": 1,
            "mutation_rate": 1,
            "seed": 42,
        }

        first = genetic_algorithm(
            lambda: population,
            checked_objective,
            parameters,
        )
        second = genetic_algorithm(
            lambda: population,
            checked_objective,
            parameters,
        )

        self.assertEqual(population, before)
        self.assertEqual(first["best_value"], 30)
        self.assertEqual(objective_1(first["best_state"]), 30)
        self.assertEqual(
            first["best_state"].outside_vehicle_ids,
            set(),
        )

        self.assertEqual(first["population_size"], 3)
        self.assertEqual(first["iterations"], 10)

        for key in ("history", "mean_history", "best_history"):
            self.assertEqual(len(first[key]), 11)
            self.assertEqual(first[key], second[key])

        self.assertEqual(
            first["best_history"],
            sorted(first["best_history"]),
        )
        self.assertEqual(
            first["best_state"],
            second["best_state"],
        )
        self.assertEqual(
            first["best_history"][-1],
            first["best_value"],
        )

        # Dua run × tiga individu × sebelas populasi.
        self.assertEqual(len(evaluated), 2 * 3 * 11)

        for maximum, mean in zip(
            first["history"],
            first["mean_history"],
        ):
            self.assertLessEqual(mean, maximum)

    def test_keeps_best_record_when_next_generation_is_worse(self):
        population = make_population()[1:]

        result = genetic_algorithm(
            lambda: population,
            objective_1,
            {
                "population_size": 2,
                "max_iterations": 1,
                "crossover_rate": 0,
                "mutation_rate": 0,
                "seed": 4,
            },
        )

        # Pada seed ini, generasi baru hanya memuat individu bernilai 10.
        self.assertEqual(result["history"], [20, 10])
        self.assertEqual(result["best_history"], [20, 20])
        self.assertEqual(result["best_value"], 20)
        self.assertEqual(objective_1(result["best_state"]), 20)

    def test_handles_population_without_vehicles(self):
        empty = State(
            [ShipState(Ship("s", 2, 1, 2))],
            {},
        )

        result = genetic_algorithm(
            lambda: [empty, empty.copy()],
            objective_1,
            {
                "population_size": 2,
                "max_iterations": 2,
                "mutation_rate": 1,
                "seed": 42,
            },
        )

        self.assertTrue(is_valid(result["best_state"]))
        self.assertEqual(result["best_value"], 0)
        self.assertEqual(result["history"], [0, 0, 0])
        self.assertEqual(result["mean_history"], [0, 0, 0])
        self.assertEqual(result["iterations"], 2)

    def test_zero_iterations_returns_best_initial_individual(self):
        result = genetic_algorithm(
            make_population,
            objective_1,
            {
                "population_size": 3,
                "max_iterations": 0,
            },
        )

        self.assertEqual(result["iterations"], 0)
        self.assertEqual(result["best_value"], 20)
        self.assertEqual(result["history"], [20])
        self.assertEqual(result["mean_history"], [10])
        self.assertEqual(result["best_history"], [20])

    def test_rejects_invalid_parameters(self):
        cases = [
            {"population_size": 1},
            {"population_size": 2.5},
            {"population_size": True},
            {"max_iterations": -1},
            {"max_iterations": 1.5},
            {"max_iterations": True},
            {"crossover_rate": -0.1},
            {"crossover_rate": 1.1},
            {"crossover_rate": float("inf")},
            {"mutation_rate": -0.1},
            {"mutation_rate": 1.1},
            {"mutation_rate": float("nan")},
        ]

        for invalid in cases:
            parameters = {
                "population_size": 3,
                "max_iterations": 0,
            }
            parameters.update(invalid)

            with self.subTest(parameters=invalid):
                with self.assertRaises(ValueError):
                    genetic_algorithm(
                        make_population,
                        objective_1,
                        parameters,
                    )

    def test_rejects_wrong_population_count_or_invalid_state(self):
        invalid = make_state([("A", 0), ("B", 0)])

        self.assertFalse(is_valid(invalid))

        cases = [
            make_population()[:2],
            [make_state(), make_state(), invalid],
        ]

        for population in cases:
            with self.subTest(population=population):
                with self.assertRaises(ValueError):
                    genetic_algorithm(
                        lambda: population,
                        objective_1,
                        {
                            "population_size": 3,
                            "max_iterations": 0,
                        },
                    )

    def test_rejects_different_problem_definitions(self):
        for difference in ("ship", "vehicle"):
            with self.subTest(difference=difference):
                first = make_state()
                second = make_state()

                if difference == "ship":
                    second.ships[0].ship = replace(
                        second.ships[0].ship,
                        max_capacity=3,
                    )
                else:
                    second.vehicles["A"] = replace(
                        second.vehicles["A"],
                        shipping_fee=99,
                    )

                self.assertTrue(is_valid(second))

                with self.assertRaises(ValueError):
                    genetic_algorithm(
                        lambda: [first, second],
                        objective_1,
                        {
                            "population_size": 2,
                            "max_iterations": 0,
                        },
                    )


if __name__ == "__main__":
    unittest.main()
