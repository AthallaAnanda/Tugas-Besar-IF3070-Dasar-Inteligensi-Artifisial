"""Nilai solusi dihitung dari kendaraan yang berhasil diangkut"""

from .constraint import is_valid
from .state import State


def objective_1(state: State):
    """Jumlahkan ShippingFee semua kendaraan di kapal yang memenuhi aturan"""
    if not is_valid(state):
        raise ValueError("Nilai objective tidak bisa dihitung untuk state tidak valid")
    return sum(state.vehicles[placement.vehicle_id].shipping_fee
               for ship in state.ships for placement in ship.placements)


def objective_2(state: State):
    """Heuristik rancangan: pendapatan / ((1 + ETA maksimum) * (1 + berat/kapasitas)).

    ETA terlama mendekati waktu penyelesaian pengiriman, bukan deadline.
    Skor tiap kapal dijumlahkan; ini bukan perhitungan laba bersih aktual.
    """
    if not is_valid(state):
        raise ValueError("Nilai objective tidak bisa dihitung untuk state tidak valid")

    value = 0.0
    for item in state.ships:
        vehicles = [state.vehicles[placement.vehicle_id] for placement in item.placements]
        if not vehicles:
            continue
        shipping_fee = sum(vehicle.shipping_fee for vehicle in vehicles)
        weight = sum(vehicle.weight for vehicle in vehicles)
        max_eta = max(vehicle.eta for vehicle in vehicles)
        # State valid berkapasitas nol hanya boleh memuat kendaraan tanpa berat.
        weight_utilization = weight / item.ship.max_capacity if item.ship.max_capacity else 0.0
        value += shipping_fee / (1 + max_eta) / (1 + weight_utilization)
    return value


OBJECTIVES = {"objective_1": objective_1, "objective_2": objective_2}
