"""Ketiga jenis perubahan harus menghasilkan state valid yang baru."""

from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors, random_neighbor
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def test_swap_move_rotate_and_load_outside_without_mutating_source():
    vehicles = [Vehicle("A", 2, 1, 10, 1, 0), Vehicle("B", 1, 1, 20, 1, 0),
                Vehicle("C", 1, 1, 30, 1, 0)]
    state = State([ShipState(Ship("s", 4, 3, 3), [
        Placement("A", "s", 0, 0), Placement("B", "s", 2, 0)
    ])], {v.id: v for v in vehicles})
    neighbors = list(generate_neighbors(state))
    assert neighbors and all(is_valid(candidate) for candidate in neighbors)
    assert all(candidate is not state for candidate in neighbors)
    assert len({tuple(sorted(str(p) for p in c.ships[0].placements)) for c in neighbors}) == len(neighbors)
    assert any({p.vehicle_id for p in c.ships[0].placements} == {"A", "B", "C"}
               for c in neighbors)
    assert any({p.vehicle_id for p in c.ships[0].placements} == {"A", "C"} for c in neighbors)
    assert any({p.vehicle_id for p in c.ships[0].placements} == {"A", "B"}
               and next(p for p in c.ships[0].placements if p.vehicle_id == "A").x == 2
               for c in neighbors)
    assert all(len(c.ships[0].placements) >= 2 for c in neighbors)
    assert any(any(p.vehicle_id == "A" and p.orientation == "vertical"
                   for p in c.ships[0].placements) for c in neighbors)
    assert any(any(p.vehicle_id == "A" and p.x == 1
                   for p in c.ships[0].placements) for c in neighbors)
    assert state.outside_vehicle_ids == {"C"}
    assert [(p.vehicle_id, p.x, p.y) for p in state.ships[0].placements] == [
        ("A", 0, 0), ("B", 2, 0)
    ]
    assert is_valid(random_neighbor(state))
