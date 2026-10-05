"""Aturan penempatan kendaraan pada grid geladak dan batas berat kapal"""

from .state import State


def _references_are_valid(state):
    """Satu kendaraan hanya boleh dimuat sekali pada kapal yang tepat"""
    ship_ids = [item.ship.id for item in state.ships]
    if not ship_ids or len(ship_ids) != len(set(ship_ids)):
        return False
    if any(vehicle_id != vehicle.id for vehicle_id, vehicle in state.vehicles.items()):
        return False
    seen = set()
    for item in state.ships:
        for placement in item.placements:
            if placement.ship_id != item.ship.id or placement.vehicle_id not in state.vehicles:
                return False
            if placement.vehicle_id in seen:
                return False
            seen.add(placement.vehicle_id)
    return True


def is_valid(state: State):
    """State valid bila referensi, posisi, sel, dan beratnya aman"""
    return (_references_are_valid(state) and check_inside_deck(state)
            and check_no_overlap(state) and check_capacity(state))


def check_no_overlap(state: State):
    """Satu sel grid tidak boleh dipakai lebih dari satu kendaraan"""
    for item in state.ships:
        occupied = set()
        for placement in item.placements:
            vehicle = state.vehicles.get(placement.vehicle_id)
            if vehicle is None:
                return False
            cells = placement.occupied_cells(vehicle)
            if occupied & cells:
                return False
            occupied.update(cells)
    return True


def check_inside_deck(state: State):
    """Tidak boleh ada bagian kendaraan yang berada di luar batas geladak"""
    for item in state.ships:
        for placement in item.placements:
            vehicle = state.vehicles.get(placement.vehicle_id)
            if vehicle is None or placement.ship_id != item.ship.id:
                return False
            width, length = placement.occupied_size(vehicle.width, vehicle.length)
            if (placement.x < 0 or placement.y < 0
                    or placement.x + width > item.ship.width
                    or placement.y + length > item.ship.length):
                return False
    return True


def check_capacity(state: State):
    """Jumlah berat kendaraan per kapal tidak boleh melebihi max_capacity"""
    for item in state.ships:
        weight = 0
        for placement in item.placements:
            vehicle = state.vehicles.get(placement.vehicle_id)
            if vehicle is None:
                return False
            weight += vehicle.weight
        if weight > item.ship.max_capacity:
            return False
    return True
