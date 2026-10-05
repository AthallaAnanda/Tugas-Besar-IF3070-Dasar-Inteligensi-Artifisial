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
    """Objective alternatif disiapkan untuk tahap bonus"""
    raise NotImplementedError


OBJECTIVES = {"objective_1": objective_1, "objective_2": objective_2}
