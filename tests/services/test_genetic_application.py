import json
from importlib import import_module
import random

import pytest

from src.app import app
from src.core.constraint import is_valid
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle
from src.services.optimization import run_optimization


def problem_data():
    return {
        "ships": [{"id": "s", "width": 2, "length": 1, "max_capacity": 2}],
        "vehicles": [
            {"id": "A", "width": 1, "length": 1, "shipping_fee": 10, "weight": 1, "eta": 0},
            {"id": "B", "width": 1, "length": 1, "shipping_fee": 20, "weight": 1, "eta": 0},
        ],
    }


def ga_config(**parameters):
    return {"algorithm": "genetic_algorithm", "problem": problem_data(), "seed": 42,
            "algorithm_seed": 81,
            "parameters": {"population_size": 4, "max_iterations": 3, **parameters}}


def test_genetic_api_reproducibility_and_population_seeds():
    client = app.test_client()
    first = client.post("/api/optimize", json=ga_config()).get_json()
    second = client.post("/api/optimize", json=ga_config()).get_json()
    assert first["status"] == "success"
    assert first["step_type"] == "generation"
    for name in ("history", "mean_history", "best_history", "initial_state", "final_state"):
        assert first[name] == second[name]
    assert len(first["configuration"]["population_seeds"]) == 4
    larger = run_optimization(ga_config(population_size=6, max_iterations=0))
    assert larger["configuration"]["population_seeds"][:4] == first["configuration"]["population_seeds"]
    assert first["initialization_duration"] >= 0
    assert is_valid(State.from_dict(first["final_state"]))


@pytest.mark.parametrize("parameters", [
    {"population_size": 1}, {"population_size": True}, {"elitism": 1},
    {"population_size": 2, "tour_size": 3}, {"crossover_rate": 1.1}, {"mutation_rate": -0.1},
    {"tour_size": 0}, {"max_iterations": -1},
])
def test_genetic_api_rejects_invalid_parameters(parameters):
    response = app.test_client().post("/api/optimize", json=ga_config(**parameters))
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_genetic_zero_generations_returns_initial_population_best():
    config = ga_config(max_iterations=0)
    result = run_optimization(config)
    assert result["iterations"] == 0
    assert len(result["history"]) == len(result["mean_history"]) == 1
    assert result["initial_state"] == result["final_state"]


def test_genetic_capabilities_and_result_omit_elitism():
    client = app.test_client()
    capabilities = client.get("/api/capabilities").get_json()
    assert "elitism" not in capabilities["algorithms"]["genetic_algorithm"]["parameters"]
    result = client.post("/api/optimize", json=ga_config(max_iterations=0)).get_json()
    assert "elitism" not in result["configuration"]["parameters"]


def test_genetic_preserves_best_when_last_generation_is_worse(monkeypatch):
    module = import_module("src.algorithms.genetic_algorithm")
    from src.core.objective import objective_1

    vehicles = {v.id: v for v in [Vehicle("A", 1, 1, 10, 1, 0), Vehicle("B", 1, 1, 20, 1, 0)]}
    def state_with(vehicle_id):
        return State([ShipState(Ship("s", 1, 1, 1), [Placement(vehicle_id, "s", 0, 0)])], vehicles)

    initial = [state_with("B"), state_with("B")]
    before = [state.to_dict() for state in initial]
    def lower_child(parent_a, parent_b, rng):
        return state_with("A")
    monkeypatch.setattr(module, "crossover", lower_child)
    result = module.genetic_algorithm(lambda: initial, objective_1, {
        "population_size": 2, "max_iterations": 1,
        "crossover_rate": 1, "mutation_rate": 0, "seed": 42,
    })
    assert result["history"] == [20, 10]
    assert result["best_history"] == [20, 20]
    assert objective_1(result["final_state"]) == 20
    assert result["mean_history"][-1] == 10
    assert [state.to_dict() for state in initial] == before


def test_crossover_and_mutation_preserve_constraints_and_parents():
    module = import_module("src.algorithms.genetic_algorithm")
    first = State.from_dict(problem_data())
    second = first.copy()
    first.ships[0].placements = [Placement("A", "s", 0, 0)]
    second.ships[0].placements = [Placement("B", "s", 0, 0)]
    before = [first.to_dict(), second.to_dict()]
    for seed in range(10):
        rng = random.Random(seed)
        child = module.crossover(first, second, rng)
        assert is_valid(child)
        mutated = module.mutate(child, rng)
        assert is_valid(mutated)
        assert [first.to_dict(), second.to_dict()] == before


def test_sa_exponential_overflow_remains_json_safe(monkeypatch):
    module = import_module("src.services.optimization")

    initial = State.from_dict(problem_data())
    initial.ships[0].placements = [Placement("A", "s", 0, 0)]
    candidate = initial.copy()
    candidate.ships[0].placements = [Placement("B", "s", 0, 0)]
    monkeypatch.setattr(module, "create_initial_state", lambda *args, **kwargs: initial.copy())
    monkeypatch.setattr(module, "generate_neighbors", lambda state: iter([candidate.copy()]))
    parameters = {"max_iterations": 1, "initial_temperature": 0.001, "min_temperature": 1e-9}
    payload = {"problem": problem_data(), "algorithm": "simulated_annealing",
               "seed": 42, "parameters": parameters}
    response = app.test_client().post("/api/optimize", json=payload)
    assert response.status_code == 200
    result = response.get_json()
    assert result["metrics"]["e_deltaet_history"] == [None]
    assert result["metrics"]["e_deltaet_overflow_history"] == [True]
    assert result["metrics"]["log_e_deltaet_history"] == [10000]
    json.dumps(result, allow_nan=False)
