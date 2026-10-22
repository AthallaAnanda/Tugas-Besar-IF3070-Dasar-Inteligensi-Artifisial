import math
import random

import pytest

from src.algorithms.genetic_algorithm import crossover, genes, genetic_algorithm, mutate, select_parent
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def make_state(placements=(), capacity=2):
    vehicles = [Vehicle("A", 1, 1, 10, 1, 0), Vehicle("B", 1, 1, 20, 1, 0)]
    loaded = [Placement(vehicle_id, "s", x, 0) for vehicle_id, x in placements]
    return State([ShipState(Ship("s", 2, 1, capacity), loaded)], {v.id: v for v in vehicles})


def make_population():
    return [make_state(), make_state([("A", 0)]), make_state([("B", 0)])]


class FixedRng:
    def __init__(self, values):
        self.values = iter(values)

    def random(self):
        return next(self.values)

    def shuffle(self, items):
        pass


@pytest.mark.parametrize("draw,expected", [(0.1, 0), (0.4, 1), (0.9, 2)])
def test_roulette_selects_fitness_interval(draw, expected):
    population = make_population()
    assert select_parent(population, [10, 20, 30], FixedRng([draw])) is population[expected]


def test_roulette_handles_zero_fitness():
    population = make_population()
    parent = select_parent(population, [0, 0, 0], random.Random(42))
    assert any(parent is individual for individual in population)
    assert select_parent(population, [0, 10, 0], FixedRng([0.0])) is population[1]


@pytest.mark.parametrize("population,fitness", [
    ([], []),
    ([1, 2, 3], [10]),
    ([1, 2, 3], [-1, 10, 20]),
    ([1, 2, 3], [math.nan, 10, 20]),
    ([1, 2, 3], [math.inf, 10, 20]),
    ([1, 2, 3], [1e308, 1e308, 0]),
])
def test_roulette_rejects_invalid_fitness(population, fitness):
    with pytest.raises(ValueError):
        select_parent(population, fitness, random.Random(42))


def test_roulette_handles_rounding_near_total_fitness():
    population = [make_state() for _ in range(11)]
    parent = select_parent(population, [1e16] + [1.0] * 10, FixedRng([math.nextafter(1.0, 0.0)]))
    assert any(parent is individual for individual in population)


@pytest.mark.parametrize("position,capacity,expected", [
    (1, 2, {"A", "B"}), (0, 2, {"A"}), (1, 1, {"A"}),
])
def test_crossover_repairs_overlap_and_capacity(position, capacity, expected):
    first = make_state([("A", 0)], capacity)
    second = make_state([("B", position)], capacity)
    before = [first.copy(), second.copy()]
    child = crossover(first, second, FixedRng([0.1, 0.9]))
    assert is_valid(child)
    assert set(genes(child)) == expected
    assert child.vehicles == first.vehicles
    assert [first, second] == before
    child.ships[0].placements.clear()
    assert [first, second] == before


def test_mutation_selects_real_neighbor_without_changing_parent():
    state = make_state([("A", 0)])
    before = state.copy()
    result = mutate(state, random.Random(42))
    assert is_valid(result)
    assert result in list(generate_neighbors(state))
    assert result is not state
    assert state == before


def test_mutation_without_neighbors_returns_independent_copy():
    state = make_state(capacity=0)
    assert list(generate_neighbors(state)) == []
    result = mutate(state, random.Random(42))
    assert result == state
    assert result is not state
    assert result.ships[0].placements is not state.ships[0].placements


def test_roulette_generations_preserve_best_record_without_elitism():
    population = make_population()[1:]
    before = [state.copy() for state in population]
    result = genetic_algorithm(lambda: population, objective_1, {
        "population_size": 2, "max_iterations": 1,
        "crossover_rate": 0, "mutation_rate": 0, "seed": 4,
    })
    assert result["history"] == [20, 10]
    assert result["best_history"] == [20, 20]
    assert result["best_value"] == objective_1(result["best_state"]) == 20
    assert result["final_state"] == result["best_state"]
    assert result["initial_state"] == population[1]
    assert result["initial_state"] is not population[1]
    assert population == before


def test_genetic_finds_both_vehicles_and_repeats_with_same_seed():
    population = make_population()
    before = [state.copy() for state in population]
    evaluated = []

    def checked_objective(state):
        assert is_valid(state)
        evaluated.append(state.copy())
        return objective_1(state)

    parameters = {
        "population_size": 3, "max_iterations": 10,
        "crossover_rate": 1, "mutation_rate": 1, "seed": 42,
    }
    first = genetic_algorithm(lambda: population, checked_objective, parameters)
    second = genetic_algorithm(lambda: population, checked_objective, parameters)
    assert first["best_value"] == objective_1(first["best_state"]) == 30
    assert first["best_state"].outside_vehicle_ids == set()
    assert first["best_state"] == second["best_state"]
    assert first["best_history"] == sorted(first["best_history"])
    assert first["best_history"][-1] == first["best_value"]
    for key in ("history", "mean_history", "best_history"):
        assert len(first[key]) == 11
        assert first[key] == second[key]
    assert all(mean <= maximum for mean, maximum in zip(first["mean_history"], first["history"]))
    assert len(evaluated) == 2 * 3 * 11
    assert population == before


def test_genetic_handles_population_without_vehicles():
    empty = State([ShipState(Ship("s", 2, 1, 2))], {})
    result = genetic_algorithm(lambda: [empty, empty.copy()], objective_1, {
        "population_size": 2, "max_iterations": 2, "mutation_rate": 1, "seed": 42,
    })
    assert is_valid(result["best_state"])
    assert result["best_value"] == 0
    assert result["history"] == result["mean_history"] == [0, 0, 0]
    assert result["iterations"] == 2
