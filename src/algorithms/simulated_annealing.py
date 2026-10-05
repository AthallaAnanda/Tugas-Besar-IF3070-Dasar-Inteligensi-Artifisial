"""Simulated Annealing, si pemberani.

Dia berani terima solusi yang sedikit lebih jelek di awal, biar tidak
cepat kejebak di local optimum. Keberaniannya diatur sama temperatur.
Makin dingin makin kalem, makin tidak mau ambil yang jelek.

Parameternya ada temperatur awal, cooling rate, temperatur minimal,
sama jumlah iterasi. Semua bisa diatur dari config.

Yang dicatat ada state awal, state akhir, nilai akhir, history,
durasi, sama seberapa sering dia mentok.
"""

import time


def simulated_annealing(initial_state, objective_function, neighbor_generator, parameters=None):
    """Jalankan simulated annealing.

    Contoh parameters itu ada initial_temperature, cooling_rate,
    min_temperature, sama max_iterations. Lihat contoh di bawah ya.
    """
    # Contoh isi parameters
    # {"initial_temperature": 1000.0, "cooling_rate": 0.95,
    #  "min_temperature": 0.001, "max_iterations": 1000}
    # TODO Tahap 2 Anggota 2, implementasi sesuai bagian 11 ya
    raise NotImplementedError
