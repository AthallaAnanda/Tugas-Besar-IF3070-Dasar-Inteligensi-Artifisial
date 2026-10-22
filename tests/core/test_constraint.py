
from src.core.constraint import check_capacity, check_inside_deck, check_no_overlap, is_valid
from src.core.placement import Placement
from src.core.ship import Ship, ShipState
from src.core.state import State
from src.core.vehicle import Vehicle


def example_state():
    vehicles = [Vehicle("A", 2, 1, 10, 3, 0), Vehicle("B", 1, 1, 20, 4, 0)]
    return State([ShipState(Ship("s", 3, 2, 7), [Placement("A", "s", 0, 0)])],
                 {v.id: v for v in vehicles})


def test_no_overlap_and_capacity_boundary():
    state = example_state()
    state.ships[0].placements.append(Placement("B", "s", 2, 0))
    assert is_valid(state)
    state.ships[0].placements[-1] = Placement("B", "s", 1, 0)
    assert not check_no_overlap(state)
    assert not is_valid(state)


def test_outside_deck_and_weight_limit():
    state = example_state()
    state.ships[0].placements.append(Placement("B", "s", -1, 0))
    assert not check_inside_deck(state)
    state.ships[0].placements[-1] = Placement("B", "s", 2, 0)
    state.ships[0].ship = Ship("s", 3, 2, 6)
    assert not check_capacity(state)


def test_duplicate_vehicle_or_wrong_ship_reference_is_invalid():
    state = example_state()
    state.ships[0].placements.append(Placement("A", "s", 0, 1))
    assert not is_valid(state)
    state.ships[0].placements[-1] = Placement("B", "other", 2, 0)
    assert not is_valid(state)
    state = example_state()
    state.vehicles["A"] = Vehicle("different", 2, 1, 10, 3, 0)
    assert not is_valid(state)


def test_each_ship_has_its_own_grid_and_capacity():
    vehicles = [Vehicle("A", 1, 1, 10, 2, 0), Vehicle("B", 1, 1, 20, 2, 0)]
    state = State([
        ShipState(Ship("one", 1, 1, 2), [Placement("A", "one", 0, 0)]),
        ShipState(Ship("two", 1, 1, 2), [Placement("B", "two", 0, 0)]),
    ], {v.id: v for v in vehicles})
    assert is_valid(state)
    assert state.deck_grid("one") == [["A"]]
    assert state.deck_grid("two") == [["B"]]
    state.ships[1].placements.append(Placement("A", "two", 0, 0))
    assert not is_valid(state)
