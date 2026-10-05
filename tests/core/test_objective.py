"""Nilai solusi hanya berasal dari kendaraan yang betul-betul diangkut."""

import pytest

from src.core.objective import objective_1
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
