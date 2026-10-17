import pytest

from src.algorithms.hill_climbing import random_restart, sideways_move, stochastic_hill_climbing
from src.core.constraint import is_valid
from src.core.objective import objective_1
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def state_with(vehicle_id):
    fees = {"A": 10, "B": 10, "C": 20, "D": 20, "E": 5}
    vehicles = {key: Vehicle(key, 1, 1, fee, 1, 0) for key, fee in fees.items()}
    return State([ShipState(Ship("s", 1, 1, 1), [Placement(vehicle_id, "s", 0, 0)])], vehicles)


def test_stochastic_continues_after_a_rejected_candidate_and_preserves_input():
    initial = state_with("A")
    original = initial.to_dict()
    candidates = iter([state_with("E"), state_with("C"), None])
    visited = []

    def neighbors(state):
        visited.append(objective_1(state))
        candidate = next(candidates)
        return iter([] if candidate is None else [candidate])

    result = stochastic_hill_climbing(initial, objective_1, neighbors, {"max_iterations": 5, "seed": 42})
    assert result["history"] == [10, 10, 20, 20]
    assert result["iterations"] == 3
    assert visited == [10, 10, 20]
    assert initial.to_dict() == original
    assert is_valid(result["final_state"])


def plateau_neighbors(state):
    vehicle_id = state.ships[0].placements[0].vehicle_id
    target = {"A": "B", "B": "C", "C": "D"}.get(vehicle_id)
    return iter([state_with(target)] if target else [])


def test_sideways_limit_is_cumulative_even_after_an_improvement():
    initial = state_with("A")
    result = sideways_move(initial, objective_1, plateau_neighbors, {
        "max_iterations": 10, "maximum_sideways_move": 2, "seed": 42,
    })
    assert result["history"] == [10, 10, 20, 20]
    assert result["iterations"] == 3
    assert result["sideways_moves"] == 2
    assert initial.ships[0].placements[0].vehicle_id == "A"
    assert is_valid(result["final_state"])


@pytest.mark.parametrize("start,history", [("A", [10, 10]), ("B", [10, 20, 20])])
def test_zero_sideways_limit_still_allows_strict_improvements(start, history):
    result = sideways_move(state_with(start), objective_1, plateau_neighbors, {
        "max_iterations": 10, "maximum_sideways_move": 0,
    })
    assert result["history"] == history
    assert result["sideways_moves"] == 0


@pytest.mark.parametrize("maximum_restart", [0, 2])
def test_restart_factory_count_histories_and_global_best(maximum_restart):
    states = [state_with(name) for name in ("A", "C", "E")][:maximum_restart + 1]
    original = [state.to_dict() for state in states]
    calls = []

    def factory():
        state = states[len(calls)]
        calls.append(state)
        return state

    result = random_restart(factory, objective_1, lambda state: iter([]), {
        "maximum_restart": maximum_restart, "max_iterations": 2,
    })
    assert len(calls) == maximum_restart + 1
    assert result["restarts"] == maximum_restart
    assert result["iterations_per_restart"] == [1] * len(states)
    assert result["iterations"] == sum(result["iterations_per_restart"])
    assert result["history_per_restart"] == [[objective_1(state)] * 2 for state in states]
    assert result["history"] == ([10, 10] if maximum_restart == 0 else [10, 10, 20, 20])
    assert result["best_value"] == max(objective_1(state) for state in states)
    assert result["initial_state"].to_dict() == original[0]
    assert [state.to_dict() for state in states] == original


@pytest.mark.parametrize("algorithm,parameters", [
    (stochastic_hill_climbing, {"max_iterations": 0}),
    (sideways_move, {"maximum_sideways_move": -1}),
    (sideways_move, {"maximum_sideways_move": True}),
])
def test_variants_reject_invalid_limits(algorithm, parameters):
    with pytest.raises(ValueError):
        algorithm(state_with("A"), objective_1, plateau_neighbors, parameters)
