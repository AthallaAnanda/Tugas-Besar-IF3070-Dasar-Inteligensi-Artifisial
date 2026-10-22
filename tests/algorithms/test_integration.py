
from pathlib import Path

import pytest

from src.algorithms.hill_climbing import steepest_ascent
from src.algorithms.simulated_annealing import simulated_annealing
from src.app import app
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State, create_initial_state, load_problem
from src.core.vehicle import Vehicle


@pytest.mark.parametrize("algorithm", [steepest_ascent, simulated_annealing])
def test_algorithm_uses_shared_core_on_sample(algorithm):
    problem = load_problem(Path(__file__).resolve().parents[2] / "data/sample/small.json")
    initial = create_initial_state(
        [item.ship for item in problem.ships], list(problem.vehicles.values()), seed=42
    )
    before = initial.to_dict()
    result = algorithm(initial, objective_1, generate_neighbors,
                       {"max_iterations": 20, "seed": 42})

    assert initial.to_dict() == before
    assert result["initial_state"].to_dict() == before
    assert is_valid(result["best_state"])
    assert is_valid(result["final_state"])
    assert objective_1(result["best_state"]) == result["best_value"]
    assert result["best_value"] >= objective_1(initial)
    assert len(result["history"]) == result["iterations"] + 1
    assert result["duration"] >= 0
    if algorithm is simulated_annealing:
        assert is_valid(result["terminal_state"])
        assert objective_1(result["terminal_state"]) == result["terminal_value"]
        assert result["terminal_value"] == result["history"][-1]
        assert len(result["best_history"]) == len(result["temperature_history"]) == len(result["history"])
        assert result["best_history"] == sorted(result["best_history"])
        assert result["best_history"][-1] == result["best_value"]


def test_annealing_preserves_best_when_accepting_worse_state():
    vehicles = {v.id: v for v in [Vehicle("A", 1, 1, 10, 1, 0), Vehicle("B", 1, 1, 1, 1, 0)]}
    initial = State([ShipState(Ship("s", 1, 1, 1), [Placement("A", "s", 0, 0)])], vehicles)
    parameters = {"max_iterations": 1, "initial_temperature": 1e9, "seed": 42}

    def worse_neighbors(state):
        for candidate in generate_neighbors(state):
            if objective_1(candidate) < objective_1(state):
                yield candidate

    first = simulated_annealing(initial, objective_1, worse_neighbors, parameters)
    second = simulated_annealing(initial, objective_1, worse_neighbors, parameters)

    assert first["accept_worse"] == 1
    assert first["best_value"] == 10
    assert first["terminal_value"] == 1
    assert first["history"] == second["history"] == [10, 1]
    assert first["best_state"].to_dict() == second["best_state"].to_dict()
    assert objective_1(initial) == 10


@pytest.mark.parametrize("parameters", [
    {"max_iterations": 0},
    {"initial_temperature": 1, "min_temperature": 1},
])
def test_annealing_can_stop_before_first_iteration(parameters):
    initial = State([ShipState(Ship("s", 1, 1, 1))], {})
    result = simulated_annealing(initial, objective_1, generate_neighbors, parameters)
    assert result["iterations"] == 0
    assert result["history"] == [0]


def test_health_endpoint_after_merge():
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "success", "message": "Backend Connected"}
