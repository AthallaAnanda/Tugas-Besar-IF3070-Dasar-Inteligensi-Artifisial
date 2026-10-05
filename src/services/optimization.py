"""Optimization Service, si tukang eksekusi satu optimasi.

Kerjanya runtut saja. Terima config dari API, bikin initial state,
pilih objective, pilih algoritma, jalankan, kumpulkan hasil,
lalu balikin hasilnya. Satu panggilan ya satu optimasi.
"""

from src.core.objective import OBJECTIVES


def run_optimization(config):
    """Jalankan satu optimasi dari config API.

    Contoh config ada algorithm, variant, objective, ship_count,
    sama parameters yang isinya max_iterations. Lihat contoh di bawah.
    """
    # Contoh config
    # {"algorithm": "hill_climbing", "variant": "steepest_ascent",
    #  "objective": "objective_1", "ship_count": 1,
    #  "parameters": {"max_iterations": 1000}}
    # TODO Tahap 3 Anggota 3, sambungkan ke algoritma dan balikin kontrak result ya
    raise NotImplementedError
