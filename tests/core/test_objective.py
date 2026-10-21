"""Nilai solusi hanya berasal dari kendaraan yang betul-betul diangkut."""

import pytest

from src.core.objective import objective_1, objective_2
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def test_shipping_fee_counts_only_loaded_vehicles():
    vehicles = [Vehicle("A", 1, 1, 60, 2, 1), Vehicle("B", 1, 1, 40, 2, 0)]
    state = State([ShipState(Ship("s", 2, 1, 2))], {v.id: v for v in vehicles})
    assert objective_1(state) == 0
    state.ships[0].placements.append(Placement("A", "s", 0, 0))
    assert objective_1(state) == 60
    state.ships[0].placements.append(Placement("B", "s", 1, 0))
    with pytest.raises(ValueError):
        objective_1(state)


def loaded_state(vehicles, capacity=100):
    return State(
        [ShipState(Ship("s", len(vehicles) or 1, 1, capacity), [
            Placement(vehicle.id, "s", index, 0) for index, vehicle in enumerate(vehicles)
        ])],
        {vehicle.id: vehicle for vehicle in vehicles},
    )


def test_efficiency_prefers_shorter_lighter_load_over_more_revenue():
    high_revenue = loaded_state([Vehicle("A", 1, 1, 200, 100, 4)])
    lighter = loaded_state([Vehicle("B", 1, 1, 180, 50, 4)])
    faster = loaded_state([Vehicle("C", 1, 1, 180, 50, 2)])
    assert objective_1(high_revenue) > objective_1(lighter)
    assert objective_2(high_revenue) == pytest.approx(20)
    assert objective_2(lighter) == pytest.approx(24)
    assert objective_2(faster) == pytest.approx(40)


def test_efficiency_uses_shared_trip_and_can_reject_slow_additional_cargo():
    state = loaded_state([Vehicle("A", 1, 1, 100, 10, 1)])
    previous = objective_2(state)
    state.ships[0] = ShipState(Ship("s", 2, 1, 100), state.ships[0].placements)
    state.vehicles["B"] = Vehicle("B", 1, 1, 10, 10, 9)
    state.ships[0].placements.append(Placement("B", "s", 1, 0))
    state.vehicles["outside"] = Vehicle("outside", 1, 1, 1000, 1, 100)
    assert objective_1(state) == 110
    assert objective_2(state) == pytest.approx(110 / (10 * 1.2))
    assert objective_2(state) < previous


def test_efficiency_is_independent_of_weight_units():
    kilograms = loaded_state([Vehicle("A", 1, 1, 180, 500, 2)], capacity=1000)
    tonnes = loaded_state([Vehicle("A", 1, 1, 180, 0.5, 2)], capacity=1)
    assert objective_2(kilograms) == pytest.approx(objective_2(tonnes))


def test_efficiency_sums_independent_ship_scores():
    state = loaded_state([Vehicle("A", 1, 1, 180, 50, 2)])
    state.vehicles["B"] = Vehicle("B", 1, 1, 200, 200, 4)
    state.ships.extend([
        ShipState(Ship("second", 1, 1, 200), [Placement("B", "second", 0, 0)]),
        ShipState(Ship("empty", 1, 1, 0)),
    ])
    assert objective_2(state) == pytest.approx(60)


def test_efficiency_handles_empty_ship_and_zero_eta_weight_capacity():
    assert objective_2(loaded_state([], capacity=0)) == 0
    assert objective_2(loaded_state([Vehicle("A", 1, 1, 60, 0, 0)], capacity=0)) == 60
    assert objective_2(loaded_state([Vehicle("A", 1, 1, 0, 10, 0)])) == 0


@pytest.mark.parametrize("invalidity", ["capacity", "overlap", "bounds"])
def test_efficiency_rejects_invalid_states(invalidity):
    state = loaded_state([Vehicle("A", 1, 1, 60, 10, 1)])
    if invalidity == "capacity":
        state.ships[0].ship = Ship("s", 1, 1, 0)
    elif invalidity == "overlap":
        state.vehicles["B"] = Vehicle("B", 1, 1, 40, 1, 0)
        state.ships[0].placements.append(Placement("B", "s", 0, 0))
    else:
        state.ships[0].placements[0] = Placement("A", "s", 1, 0)
    with pytest.raises(ValueError, match="state tidak valid"):
        objective_2(state)
