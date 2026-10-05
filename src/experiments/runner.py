"""Experiment Runner, si pencatat rajin.

Tugasnya jalanin eksperimen otomatis berkali kali lalu simpan hasilnya
sebagai JSON biar gampang dibuka lagi buat bikin grafik.
"""

import json
import os
import time


def runner(experiment_config, output_dir="output/results"):
    """Jalankan eksperimen berulang dan simpan tiap run sebagai JSON.

    Contoh experiment_config ada algorithm, population_sizes,
    iteration_counts, sama runs. Outputnya daftar hasil tiap run.
    """
    # Contoh config
    # {"algorithm": "genetic_algorithm", "population_sizes": [20, 50, 100],
    #  "iteration_counts": [100, 500, 1000], "runs": 3}
    # TODO Tahap 3 Anggota 3, implementasi sesuai bagian 14 ya
    raise NotImplementedError
