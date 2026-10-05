"""Neighbor dibuat dengan menukar, memindah, atau memutar kendaraan"""

from dataclasses import replace
from itertools import combinations
import random

from .constraint import is_valid
from .placement import Placement
from .state import State


def _signature(state):
    """Kombinasi posisi yang sama cukup dicoba sekali saja"""
    return frozenset(placement for ship in state.ships for placement in ship.placements)


def generate_neighbors(state: State):
    """Menghasilkan state baru yang valid tanpa menyentuh state asal"""
    if not is_valid(state):
        raise ValueError("Neighbor membutuhkan state awal yang valid")

    seen = {_signature(state)}

    def unique(candidate):
        signature = _signature(candidate)
        if signature in seen or not is_valid(candidate):
            return False
        seen.add(signature)
        return True

    loaded = [(ship_index, index, placement)
              for ship_index, ship in enumerate(state.ships)
              for index, placement in enumerate(ship.placements)]

    # Menukar dua kendaraan di dalam kapal, termasuk bila kapalnya berbeda
    for (ship_a, index_a, a), (ship_b, index_b, b) in combinations(loaded, 2):
        candidate = state.copy()
        candidate.ships[ship_a].placements[index_a] = replace(a, vehicle_id=b.vehicle_id)
        candidate.ships[ship_b].placements[index_b] = replace(b, vehicle_id=a.vehicle_id)
        if unique(candidate):
            yield candidate

    # Menukar yang di dalam dengan yang di luar juga termasuk operasi tukar
    for ship_index, index, placement in loaded:
        for vehicle_id in sorted(state.outside_vehicle_ids):
            candidate = state.copy()
            candidate.ships[ship_index].placements[index] = replace(placement, vehicle_id=vehicle_id)
            if unique(candidate):
                yield candidate

    # Kendaraan di dalam boleh digeser, keluar kapal, atau berubah orientasi
    for ship_index, index, placement in loaded:
        candidate = state.copy()
        candidate.ships[ship_index].placements.pop(index)
        if unique(candidate):
            yield candidate

        candidate = state.copy()
        candidate.ships[ship_index].placements[index] = replace(
            placement, orientation="vertical" if placement.orientation == "horizontal" else "horizontal"
        )
        if unique(candidate):
            yield candidate

    # Perpindahan mencakup kendaraan di luar yang masuk ke kapal
    for vehicle_id in state.vehicles:
        current = next(((ship_index, index) for ship_index, index, placement in loaded
                        if placement.vehicle_id == vehicle_id), None)
        current_placement = next((p for _, _, p in loaded if p.vehicle_id == vehicle_id), None)
        for ship_index, item in enumerate(state.ships):
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
                        candidate = state.copy()
                        if current is not None:
                            old_ship, old_index = current
                            candidate.ships[old_ship].placements.pop(old_index)
                        candidate.ships[ship_index].placements.append(
                            Placement(vehicle_id, item.ship.id, x, y, facing)
                        )
                        if unique(candidate):
                            yield candidate


def random_neighbor(state: State, rng=None):
    """Memilih satu neighbor secara acak tanpa menyimpan semuanya di memori"""
    rng = rng or random
    selected = None
    for count, candidate in enumerate(generate_neighbors(state), start=1):
        if rng.randrange(count) == 0:
            selected = candidate
    if selected is None:
        raise ValueError("Tidak ada neighbor valid untuk state ini")
    return selected
