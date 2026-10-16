"""Satu solusi yang menyimpan kapal, kendaraan, dan posisi yang sedang dipilih"""

from copy import deepcopy
from dataclasses import dataclass, field
import json
from pathlib import Path
import random

from .placement import Placement
from .ship import Ship, ShipState
from .vehicle import Vehicle


@dataclass
class State:
    """Kendaraan tanpa placement tetap tercatat sebagai kendaraan di luar kapal"""

    ships: list[ShipState] = field(default_factory=list)
    vehicles: dict[str, Vehicle] = field(default_factory=dict)

    def copy(self):
        """Salin semua daftar placement agar perubahan neighbor tidak mengubah state asal"""
        return deepcopy(self)

    @property
    def outside_vehicle_ids(self):
        """Lihat kendaraan yang belum dimuat tanpa perlu menyimpan status secara double"""
        loaded = {placement.vehicle_id for ship in self.ships for placement in ship.placements}
        return set(self.vehicles) - loaded

    def deck_grid(self, ship_id):
        """Tampilkan grid dengan identitas kendaraan di setiap sel yang terisi"""
        ship_state = next((item for item in self.ships if item.ship.id == ship_id), None)
        if ship_state is None:
            raise KeyError(ship_id)
        from .constraint import is_valid

        if not is_valid(self):
            raise ValueError("Grid hanya bisa ditampilkan dari state valid")
        grid = [[None for _ in range(ship_state.ship.width)]
                for _ in range(ship_state.ship.length)]
        for placement in ship_state.placements:
            for x, y in placement.occupied_cells(self.vehicles[placement.vehicle_id]):
                grid[y][x] = placement.vehicle_id
        return grid

    def to_dict(self):
        """Buat data sederhana yang nanti bisa dipakai API dan visualisasi"""
        from .objective import objective_1

        return {
            "vehicles": [vars(vehicle).copy() for vehicle in self.vehicles.values()],
            "ships": [
                {
                    "ship": vars(item.ship).copy(),
                    "placements": [vars(placement).copy() for placement in item.placements],
                    "grid": self.deck_grid(item.ship.id),
                }
                for item in self.ships
            ],
            "outside_vehicle_ids": sorted(self.outside_vehicle_ids),
            "value": objective_1(self),
        }

    @classmethod
    def from_dict(cls, data):
        """Baca definisi masalah beserta placement awal bila disediakan"""
        vehicles = [Vehicle(**vehicle) for vehicle in data["vehicles"]]
        ships = []
        for item in data["ships"]:
            ship_data = item["ship"] if "ship" in item else {
                key: value for key, value in item.items() if key != "placements"
            }
            placements = [Placement(**placement) for placement in item.get("placements", [])]
            ships.append(ShipState(Ship(**ship_data), placements))
        if len({vehicle.id for vehicle in vehicles}) != len(vehicles):
            raise ValueError("Identitas kendaraan harus unik")
        if len({item.ship.id for item in ships}) != len(ships):
            raise ValueError("Identitas kapal harus unik")
        if not ships:
            raise ValueError("Minimal satu kapal diperlukan")
        state = cls(ships, {vehicle.id: vehicle for vehicle in vehicles})
        from .constraint import is_valid

        if not is_valid(state):
            raise ValueError("Placement awal tidak memenuhi aturan")
        return state


def load_problem(path):
    """Membaca kapal dan kendaraan dari berkas JSON"""
    with Path(path).open(encoding="utf-8") as file:
        return State.from_dict(json.load(file))


def create_initial_state(ships, vehicles, seed=None):
    """Mengacak urutan kendaraan dan cari posisi valid di geladak.

    Kendaraan yang tidak muat atau tidak terpilih tetap berada di luar kapal.
    Seed bisa diisi supaya hasil eksperimen dapat diulang.
    """
    rng = random.Random(seed)
    state = State([ShipState(ship) for ship in ships], {v.id: v for v in vehicles})
    if len(state.vehicles) != len(vehicles) or len({ship.id for ship in ships}) != len(ships):
        raise ValueError("Identitas kendaraan dan kapal harus unik")
    if not ships:
        raise ValueError("Minimal satu kapal diperlukan")

    from .constraint import is_valid

    pending = list(vehicles)
    rng.shuffle(pending)
    for vehicle in pending:
        # Sisakan beberapa kendaraan di luar agar pencarian punya ruang untuk memperbaiki solusi
        if rng.random() < 0.25:
            continue
        choices = []
        for ship_state in state.ships:
            for orientation in ("horizontal", "vertical"):
                width, length = Placement(vehicle.id, ship_state.ship.id, 0, 0, orientation).occupied_size(
                    vehicle.width, vehicle.length
                )
                for x in range(ship_state.ship.width - width + 1):
                    for y in range(ship_state.ship.length - length + 1):
                        choices.append((ship_state, Placement(vehicle.id, ship_state.ship.id, x, y, orientation)))
        rng.shuffle(choices)
        for ship_state, placement in choices:
            ship_state.placements.append(placement)
            if is_valid(state):
                break
            ship_state.placements.pop()
    return state
