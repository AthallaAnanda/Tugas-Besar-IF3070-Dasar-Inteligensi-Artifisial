"""Cerita soal aturan main. Setiap calon State harus lolos semua cek di sini.

Urutannya gampang saja. Pertama cek tidak numpuk, lalu cek masih di dalam geladak,
terakhir cek kapasitas masih cukup. Kalau satu saja gagal ya berarti tidak valid.
"""

from .state import State


def is_valid(state: State):
    """Cek apakah satu State sudah memenuhi semua aturan. True kalau aman semua."""
    # TODO Tahap 1 Anggota 1, gabungkan tiga cek wajib di sini
    raise NotImplementedError


def check_no_overlap(state: State):
    """Pastikan tidak ada kendaraan yang saling tindih. Kasihan kalau penyok."""
    # TODO Tahap 1 Anggota 1
    raise NotImplementedError


def check_inside_deck(state: State):
    """Pastikan semua kendaraan masih di dalam petak geladak, tidak ada yang nongol keluar."""
    # TODO Tahap 1 Anggota 1
    raise NotImplementedError


def check_capacity(state: State):
    """Pastikan muatan tidak melebihi kapasitas yang diizinkan."""
    # TODO Tahap 1 Anggota 1
    raise NotImplementedError
