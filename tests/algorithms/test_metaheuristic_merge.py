import math

import pytest

from src.algorithms.genetic_algorithm import genetic_algorithm
from src.algorithms.simulated_annealing import simulated_annealing
from src.core.constraint import is_valid
from src.core.objective import objective_1
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle
from src.services.trace import TraceRecorder


def state_with(vehicle_id):
    vehicles = {
        "A": Vehicle("A", 1, 1, 10, 1, 0),
        "B": Vehicle("B", 1, 1, 20, 1, 0),
    }
    return State([
        ShipState(Ship("s", 1, 1, 1), [Placement(vehicle_id, "s", 0, 0)])
    ], vehicles)


@pytest.mark.parametrize("source,target,temperature,decision", [
    ("A", "B", 2.0, "improved"),
    ("B", "A", 2.0, "rejected"),
    ("B", "A", 1e9, "accepted_worse"),
    ("A", "B", 0.001, "improved"),
])
def test_annealing_exponent_history_and_replay_share_decision(
    source, target, temperature, decision
):
    initial = state_with(source)
    before = initial.to_dict()
    candidate = state_with(target)
    recorder = TraceRecorder()

    def neighbors(state):
        yield candidate.copy()

    parameters = {
        "max_iterations": 1,
        "initial_temperature": temperature,
        "min_temperature": 1e-9,
        "cooling_rate": 0.5,
        "seed": 42,
    }
    result = simulated_annealing(
        initial, objective_1, neighbors, parameters, on_step=recorder
    )
    without_replay = simulated_annealing(
        initial, objective_1, neighbors, parameters
    )
    frames = recorder.finish()
    exponent = (objective_1(candidate) - objective_1(initial)) / temperature

    assert result["log_e_deltaet_history"] == [exponent]
    if exponent == 10000:
        assert result["e_deltaet_history"] == [math.inf]
    else:
        assert result["e_deltaet_history"] == pytest.approx([math.exp(exponent)])
    assert len(result["e_deltaet_history"]) == result["iterations"] == 1
    assert len(result["log_e_deltaet_history"]) == 1
    assert len(result["history"]) == len(frames) == 2
    assert frames[1]["decision"] == decision
    assert frames[1]["temperature"] == temperature
    assert frames[1]["next_temperature"] == temperature * 0.5
    assert frames[1]["objective_value"] == result["history"][-1]
    assert frames[1]["best_value"] == result["best_value"]
    assert result["stop_reason"] == "max_iterations"
    assert initial.to_dict() == result["initial_state"].to_dict() == before
    assert is_valid(result["best_state"])
    assert result["history"] == without_replay["history"]
    assert result["e_deltaet_history"] == without_replay["e_deltaet_history"]
    assert result["terminal_state"].to_dict() == without_replay["terminal_state"].to_dict()


@pytest.mark.parametrize("parameters,reason", [
    ({"max_iterations": 0}, "max_iterations"),
    ({"initial_temperature": 1, "min_temperature": 1}, "min_temperature"),
    ({}, "no_neighbors"),
])
def test_annealing_does_not_record_exponent_without_candidate(parameters, reason):
    recorder = TraceRecorder()

    def no_neighbors(state):
        return iter(())

    result = simulated_annealing(
        state_with("A"), objective_1, no_neighbors, parameters, on_step=recorder
    )
    assert result["iterations"] == 0
    assert result["e_deltaet_history"] == []
    assert result["log_e_deltaet_history"] == []
    assert result["stop_reason"] == reason
    assert len(recorder.finish()) == 1


def test_merged_genetic_algorithm_runs_with_shared_core_and_preserves_population():
    population = [state_with("A"), state_with("B"), state_with("A"), state_with("B")]
    before = [state.to_dict() for state in population]

    def initial_population():
        return population

    parameters = {
        "population_size": 4,
        "max_iterations": 3,
        "crossover_rate": 1.0,
        "mutation_rate": 1.0,
        "seed": 42,
    }
    result = genetic_algorithm(initial_population, objective_1, parameters)
    repeated = genetic_algorithm(initial_population, objective_1, parameters)

    assert result["population_size"] == 4
    assert result["iterations"] == 3
    assert len(result["history"]) == len(result["mean_history"]) == len(result["best_history"]) == 4
    assert result["history"] == repeated["history"]
    assert result["mean_history"] == repeated["mean_history"]
    assert result["best_value"] == objective_1(result["best_state"]) == 20
    assert is_valid(result["best_state"])
    assert is_valid(result["initial_state"])
    assert is_valid(result["final_state"])
    assert all(average <= maximum for average, maximum in zip(result["mean_history"], result["history"]))
    assert [state.to_dict() for state in population] == before
