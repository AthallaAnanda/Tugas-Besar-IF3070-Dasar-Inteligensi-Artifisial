"""Neighbor dibuat dengan menukar, memindah, atau memutar kendaraan"""

from dataclasses import replace
from itertools import combinations
import random

from .constraint import is_valid
from .placement import Placement
from .state import State


class NoNeighborError(ValueError):
    """State valid tidak memiliki neighbor yang bisa dipilih."""


def _signature(state):
    """Kombinasi posisi yang sama cukup dicoba sekali saja"""
    return frozenset(placement for ship in state.ships for placement in ship.placements)


def _possible_moves(state):
    """Usulkan perubahan placement tanpa membuat salinan state."""
    loaded = [placement for ship in state.ships for placement in ship.placements]

    # Menukar dua kendaraan di dalam kapal, termasuk bila kapalnya berbeda
    for a, b in combinations(loaded, 2):
        yield {a.vehicle_id: replace(b, vehicle_id=a.vehicle_id),
               b.vehicle_id: replace(a, vehicle_id=b.vehicle_id)}

    # Menukar yang di dalam dengan yang di luar juga termasuk operasi tukar
    for placement in loaded:
        for vehicle_id in sorted(state.outside_vehicle_ids):
            yield {placement.vehicle_id: None,
                   vehicle_id: replace(placement, vehicle_id=vehicle_id)}

    # Perubahan orientasi tidak mengubah posisi kendaraan.
    for placement in loaded:
        yield {placement.vehicle_id: replace(
            placement, orientation="vertical" if placement.orientation == "horizontal" else "horizontal"
        )}

    # Perpindahan mencakup kendaraan di luar yang masuk ke kapal
    for vehicle_id in state.vehicles:
        current_placement = next((p for p in loaded if p.vehicle_id == vehicle_id), None)
        for item in state.ships:
            vehicle = state.vehicles[vehicle_id]
            # Kendaraan di luar bisa masuk dengan orientasi yang sesuai ruang kosong
            orientations = (current_placement.orientation,) if current_placement else ("horizontal", "vertical")
            for facing in orientations:
                width, length = Placement(vehicle_id, item.ship.id, 0, 0, facing).occupied_size(
                    vehicle.width, vehicle.length
                )
                for x in range(item.ship.width - width + 1):
                    for y in range(item.ship.length - length + 1):
                        if current_placement and (item.ship.id, x, y) == (
                            current_placement.ship_id, current_placement.x, current_placement.y
                        ):
                            continue
                        yield {vehicle_id: Placement(vehicle_id, item.ship.id, x, y, facing)}


def _apply_move(state, changes):
    candidate = state.copy()
    for item in candidate.ships:
        item.placements = [placement for placement in item.placements
                           if placement.vehicle_id not in changes]
        item.placements.extend(placement for placement in changes.values()
                               if placement is not None and placement.ship_id == item.ship.id)
    return candidate


def generate_neighbors(state: State):
    """Menghasilkan state baru yang valid tanpa menyentuh state asal"""
    if not is_valid(state):
        raise ValueError("Neighbor membutuhkan state awal yang valid")

    seen = {_signature(state)}
    for changes in _possible_moves(state):
        candidate = _apply_move(state, changes)
        signature = _signature(candidate)
        if signature not in seen and is_valid(candidate):
            seen.add(signature)
            yield candidate


def random_neighbor(state: State, rng=None):
    """Acak usulan langkah dan kembalikan state valid pertama yang ditemukan."""
    if not is_valid(state):
        raise ValueError("Neighbor membutuhkan state awal yang valid")
    rng = rng or random
    moves = list(_possible_moves(state))
    rng.shuffle(moves)
    original = _signature(state)
    for changes in moves:
        candidate = _apply_move(state, changes)
        if _signature(candidate) != original and is_valid(candidate):
            return candidate
    raise NoNeighborError("Tidak ada neighbor valid untuk state ini")
