"""Cerita soal bikin tetangga, alias State baru yang mirip sama State sekarang.

Ada tiga jurus sesuai spek. Pertama tukar posisi dua kendaraan.
Kedua geser kendaraan ke koordinat lain. Ketiga putar orientasinya.

Setiap tetangga wajib dicek dulu valid atau tidak sebelum dikasih ke algoritma.
"""

from collections.abc import Iterator

from .state import State


def generate_neighbors(state: State):
    """Kasih daftar tetangga yang valid dari State sekarang, satu per satu."""
    # TODO Tahap 1 Anggota 1, bikin tiga operasi di atas plus validasi constraint ya
    raise NotImplementedError
    yield state  # baris ini cuma penanda biar jadi generator, nanti dihapus


def random_neighbor(state: State):
    """Ambil satu tetangga acak yang valid. Kepakai buat SA sama stochastic."""
    # TODO Tahap 1 Anggota 1
    raise NotImplementedError
