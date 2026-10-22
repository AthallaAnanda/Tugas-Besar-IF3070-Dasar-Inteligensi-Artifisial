
import pytest

from src.app import app
from src.core.objective import objective_1, objective_2
from src.core.state import State
from src.services.optimization import ALGORITHMS, run_optimization


def configuration(algorithm):
    parameters = {"max_iterations": 3}
    if algorithm == "genetic_algorithm":
        parameters["population_size"] = 4
    if algorithm == "random_restart":
        parameters["maximum_restart"] = 2
    return {
        "algorithm": algorithm,
        "objective": "objective_2",
        "seed": 42,
        "algorithm_seed": 43,
        "parameters": parameters,
        "problem": {
            "ships": [{"id": "s", "width": 3, "length": 1, "max_capacity": 100}],
            "vehicles": [
                {"id": "A", "width": 1, "length": 1, "shipping_fee": 100, "weight": 30, "eta": 1},
                {"id": "B", "width": 1, "length": 1, "shipping_fee": 10, "weight": 30, "eta": 9},
                {"id": "C", "width": 1, "length": 1, "shipping_fee": 80, "weight": 20, "eta": 2},
            ],
        },
    }


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_all_algorithms_use_bonus_objective_and_serialize_consistently(algorithm):
    result = run_optimization(configuration(algorithm))
    initial = State.from_dict(result["initial_state"])
    final = State.from_dict(result["final_state"])
    assert result["configuration"]["objective"] == "objective_2"
    assert result["history"][0] == pytest.approx(objective_2(initial))
    assert result["initial_state"]["value"] == pytest.approx(objective_2(initial))
    assert result["objective_value"] == pytest.approx(objective_2(final))
    assert result["final_state"]["value"] == pytest.approx(result["objective_value"])
    assert result["best_history"][-1] == result["objective_value"]
    assert result["objective_value"] >= result["history"][0]
    assert len(result["history"]) == result["iterations"] + 1
    assert result["statistics"]["total_shipping_fee"] == objective_1(final)
    assert result["objective_value"] != result["statistics"]["total_shipping_fee"]
    loaded = [final.vehicles[item.vehicle_id] for item in final.ships[0].placements]
    assert result["statistics"]["ships"][0]["max_eta"] == max(vehicle.eta for vehicle in loaded)
    if algorithm == "random_restart":
        assert max(history[-1] for history in result["metrics"]["history_per_restart"]) == pytest.approx(objective_2(final))
    repeated = run_optimization(configuration(algorithm))
    for key in ("initial_state", "final_state", "history", "mean_history"):
        assert repeated[key] == result[key]


def test_bonus_objective_is_available_through_api():
    client = app.test_client()
    objectives = client.get("/api/capabilities").get_json()["objectives"]
    assert [item["id"] for item in objectives] == ["objective_1", "objective_2"]
    assert "ETA" in objectives[1]["description"]
    response = client.post("/api/optimize", json=configuration("hill_climbing"))
    assert response.status_code == 200
    result = response.get_json()
    assert result["final_state"]["value"] == result["objective_value"]
    assert result["configuration"]["objective"] == "objective_2"


@pytest.mark.parametrize("objective", ["unknown", None, [], {}])
def test_api_rejects_invalid_objective(objective):
    payload = {**configuration("hill_climbing"), "objective": objective}
    response = app.test_client().post("/api/optimize", json=payload)
    assert response.status_code == 400
    assert response.get_json()["message"] == "Objective belum tersedia"


def test_default_objective_and_state_serialization_remain_total_shipping_fee():
    payload = configuration("hill_climbing")
    del payload["objective"]
    result = run_optimization(payload)
    final = State.from_dict(result["final_state"])
    assert result["configuration"]["objective"] == "objective_1"
    assert result["objective_value"] == objective_1(final) == final.to_dict()["value"]
    assert final.to_dict(objective_2)["value"] == pytest.approx(objective_2(final))


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_bonus_objective_handles_empty_zero_capacity_problem(algorithm):
    payload = configuration(algorithm)
    payload["problem"]["vehicles"] = []
    payload["problem"]["ships"][0]["max_capacity"] = 0
    result = run_optimization(payload)
    assert result["objective_value"] == result["final_state"]["value"] == 0
    assert result["statistics"]["total_shipping_fee"] == 0
    assert result["statistics"]["ships"][0]["max_eta"] is None
