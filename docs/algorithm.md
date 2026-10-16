# Algoritma pencarian

## Steepest Ascent Hill Climbing

```python
from src.algorithms.hill_climbing import steepest_ascent
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1

result = steepest_ascent(initial_state, objective_1, generate_neighbors,
                         {"max_iterations": 1000})
```

`initial_state` adalah `State` valid, `objective_function(state)` mengembalikan
angka yang semakin besar semakin baik, dan `neighbor_generator(state)`
menghasilkan iterable berisi state tetangga. Generator harus menjaga state
asal. `max_iterations` adalah bilangan bulat positif; nilai bawaan 1000.

Pada setiap iterasi, algoritma menilai semua tetangga dan memilih yang bernilai
tertinggi. Perpindahan hanya terjadi jika nilainya meningkat. Pencarian berhenti
ketika tidak ada perbaikan atau batas iterasi tercapai.

Hasil adalah kamus dengan `initial_state`, `final_state`, `best_state`,
`best_value`, `history`, `iterations`, dan `duration`. Ketiga state adalah objek
`State`; `final_state` dan `best_state` menunjuk solusi yang sama. `history[0]`
adalah nilai awal, diikuti nilai setelah setiap putaran pencarian. Putaran
terakhir tanpa perbaikan tetap dihitung dan nilainya tetap dicatat. `duration`
dalam detik. Untuk keluaran JSON, ubah state dengan `State.to_dict()`.

## Simulated Annealing

```python
from src.algorithms.simulated_annealing import simulated_annealing

result = simulated_annealing(initial_state, objective_1, generate_neighbors, {
    "initial_temperature": 1000.0,
    "cooling_rate": 0.95,
    "min_temperature": 0.001,
    "max_iterations": 1000,
    "seed": 42,
})
```

State awal harus valid. Temperatur awal dan minimum harus positif dan terbatas,
cooling rate berada di antara nol dan satu, dan max_iterations berupa bilangan
bulat tidak negatif. Seed bersifat opsional untuk mengulang hasil eksperimen.

Setiap putaran meninjau seluruh neighbor dan memilih satu secara acak memakai
reservoir sampling. Solusi dengan nilai sama atau lebih baik selalu diterima.
Solusi lebih buruk diterima dengan probabilitas `exp(delta / temperature)`,
dengan delta berupa nilai kandidat dikurangi nilai saat ini. Temperatur
dikalikan cooling rate pada setiap putaran. Pencarian berhenti ketika batas
iterasi tercapai, temperatur mencapai minimum, atau tidak ada neighbor.

Hasil memakai kontrak umum `best_state`, `best_value`, `history`, `iterations`,
dan `duration`, ditambah `initial_state`, `final_state`, dan `final_value`.
`final_state` berisi solusi terbaik yang ditemukan. `terminal_state` dan
`terminal_value` menunjukkan posisi terakhir pencarian, yang bisa lebih buruk.
Semua state masih berupa objek Python.

`history` mencatat nilai state saat ini, sedangkan `best_history` menyimpan nilai
terbaik sampai setiap putaran. `temperature_history` mencatat temperatur.
Ketiganya dimulai dari kondisi awal sehingga panjangnya adalah iterations + 1.
`stuck_count` menghitung putaran yang tidak menemukan neighbor bernilai lebih
baik, termasuk pemeriksaan terakhir ketika tidak ada neighbor. `accept_worse`
menghitung perpindahan ke solusi yang lebih buruk dan benar-benar diterima.

## Status algoritma lainnya

Stochastic Hill Climbing, Sideways Move, Random Restart,
dan Genetic Algorithm belum diimplementasikan pada checkout ini. Tiga varian
Hill Climbing bonus dikerjakan setelah seluruh komponen wajib proyek teruji.
