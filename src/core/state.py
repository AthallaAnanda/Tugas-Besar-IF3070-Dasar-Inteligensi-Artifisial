"""Cerita soal State, alias satu solusi utuh.

Satu State itu isinya daftar kapal. Kalau main satu kapal ya isinya satu aja.
Kalau main multi ship ya tinggal tambah. Algoritmanya tidak perlu diubah
karena bentuknya sama saja.
"""

from dataclasses import dataclass, field

from .ship import ShipState


@dataclass
class State:
    """Satu solusi yang diterima sama semua algoritma. Ini kontrak pentingnya."""

    ships: list[ShipState] = field(default_factory=list)

    def copy(self):
        """Bikin salinan State biar aman waktu bikin neighbor. Jangan sampai yang asli ikut berubah."""
        # TODO Tahap 1 Anggota 1, bikin deep copy di sini ya
        raise NotImplementedError

    # TODO Tahap 1 Anggota 1, bikin factory create_initial_state di sini
