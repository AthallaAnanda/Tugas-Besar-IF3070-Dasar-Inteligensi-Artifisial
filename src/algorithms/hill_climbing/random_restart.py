"""Random Restart Hill Climbing, si pantang menyerah.

Idenya sederhana, kalau mentok ya ulangi lagi dari awal yang baru.
Diulang beberapa kali sesuai maximum_restart, lalu ambil yang paling bagus.

Yang dicatat ada jumlah restart, iterasi tiap restart, total iterasi,
nilai terbaik, sama durasi.
"""

import time


def random_restart(initial_state_fn, objective_function, neighbor_generator, parameters=None):
    """Jalankan random restart.

    initial_state_fn itu fungsi yang tiap dipanggil bikin State awal baru.
    """
    # TODO Tahap 2 Bonus Anggota 1, implementasi sesuai bagian 10.4 ya
    raise NotImplementedError
