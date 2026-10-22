
import json
from pathlib import Path

import pytest

from src.core.constraint import is_valid
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State, create_initial_state, load_problem
from src.core.vehicle import Vehicle


SAMPLE = Path(__file__).resolve().parents[2] / "data/sample/small.json"


def test_sample_and_grid_keep_vehicles_outside():
    state = load_problem(SAMPLE)
    assert len(state.vehicles) == 25
    assert state.outside_vehicle_ids == set("ABCDEFGHIJKLMNOPQRSTUVWXY")
    assert (state.ships[0].ship.width, state.ships[0].ship.length, state.ships[0].ship.max_capacity) == (7, 6, 15)
    state.ships[0].placements.append(Placement("A", "ship_1", 0, 0))
    assert is_valid(state)
    assert state.deck_grid("ship_1")[0][:3] == ["A", "A", None]
    assert state.outside_vehicle_ids == set("BCDEFGHIJKLMNOPQRSTUVWXY")
    data = state.to_dict()
    assert data["value"] == 60
    assert data["ships"][0]["grid"][1][1] == "A"
    assert json.loads(json.dumps(data))["outside_vehicle_ids"] == list("BCDEFGHIJKLMNOPQRSTUVWXY")


def test_copy_does_not_modify_original():
    state = load_problem(SAMPLE)
    copied = state.copy()
    copied.ships[0].placements.append(Placement("A", "ship_1", 0, 0))
    assert not state.ships[0].placements


def test_seeded_initial_state_is_random_valid_and_reproducible():
    data = load_problem(SAMPLE)
    first = create_initial_state([item.ship for item in data.ships], list(data.vehicles.values()), seed=123)
    second = create_initial_state([item.ship for item in data.ships], list(data.vehicles.values()), seed=123)
    assert is_valid(first)
    assert first.to_dict() == second.to_dict()
    assert len(first.outside_vehicle_ids) + len(first.ships[0].placements) == len(first.vehicles)


def test_reject_duplicate_ids_and_non_integer_coordinates():
    with pytest.raises(ValueError):
        State.from_dict({"ships": [{"id": "s", "width": 2, "length": 2, "max_capacity": 1}],
                         "vehicles": [vars(Vehicle("A", 1, 1, 1, 1, 0))] * 2})
    with pytest.raises(ValueError):
        Placement("A", "ship_1", 0.5, 0)
    with pytest.raises(ValueError):
        Vehicle("A", 0, 1, 1, 1, 0)


def test_from_dict_rejects_invalid_placement():
    with pytest.raises(ValueError):
        State.from_dict({
            "vehicles": [vars(Vehicle("A", 2, 2, 10, 1, 0))],
            "ships": [{"ship": vars(Ship("s", 2, 2, 2)),
                       "placements": [vars(Placement("A", "s", 1, 1))]}],
        })


def test_from_dict_accepts_both_ship_shapes_with_placements():
    vehicle = vars(Vehicle("A", 1, 1, 10, 1, 0))
    ship = vars(Ship("s", 2, 1, 1))
    placement = vars(Placement("A", "s", 1, 0))
    direct = State.from_dict({
        "vehicles": [vehicle],
        "ships": [{**ship, "placements": [placement]}],
    })
    nested = State.from_dict({
        "vehicles": [vehicle],
        "ships": [{"ship": ship, "placements": [placement]}],
    })
    assert direct.to_dict() == nested.to_dict()
    assert direct.deck_grid("s") == [[None, "A"]]
    assert direct.outside_vehicle_ids == set()


def test_numeric_fields_reject_non_finite_values():
    with pytest.raises(ValueError):
        Vehicle("A", 1, 1, float("nan"), 1, 0)
    with pytest.raises(ValueError):
        Vehicle("A", 1, 1, 1, float("inf"), 0)
    with pytest.raises(ValueError):
        Ship("s", 1, 1, float("nan"))
