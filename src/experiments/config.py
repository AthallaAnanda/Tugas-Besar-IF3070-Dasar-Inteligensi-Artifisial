"""Config eksperimen, biar tidak setting manual tiap kali.

Di bawah ada config default sama dua config khusus GA.
Skenario A itu iterasi yang diubah ubah, populasinya tetap.
Skenario B sebaliknya, populasi yang diubah ubah, iterasinya tetap.
Masing masing diulang 3 kali biar adil.
"""

DEFAULT_EXPERIMENT = {
    "algorithm": "hill_climbing",
    "runs": 3,
    "parameters": {"max_iterations": 1000},
}

# GA Skenario A, populasi tetap, iterasi diganti ganti
GA_EXPERIMENT_A = {
    "algorithm": "genetic_algorithm",
    "population_size": 50,
    "iteration_counts": [100, 500, 1000],
    "runs": 3,
}

# GA Skenario B, iterasi tetap, populasi diganti ganti
GA_EXPERIMENT_B = {
    "algorithm": "genetic_algorithm",
    "iterations": 500,
    "population_sizes": [20, 50, 100],
    "runs": 3,
}
