"""Genetic Algorithm, si main keroyokan.

Dia tidak jalan sendirian, tapi bawa satu populasi solusi.
Tiap generasi ada seleksi, kawin silang, mutasi, plus elitisme
biar yang terbaik tidak hilang. Lalu dibentuk generasi baru.

Penting, tiap individu di populasi harus tetap bisa dibaca sebagai State yang valid.
"""

import time


def genetic_algorithm(initial_population_fn, objective_function, parameters=None):
    """Jalankan genetic algorithm.

    initial_population_fn itu fungsi yang bikin daftar State awal.
    Contoh parameters ada population_size, max_iterations,
    crossover_rate, mutation_rate, sama elitism.
    Hasilnya paket result standar plus info max dan rata rata populasi.
    """
    # TODO Tahap 2 Anggota 2, implementasi sesuai bagian 12 plus eksperimen 13.2 ya
    raise NotImplementedError
