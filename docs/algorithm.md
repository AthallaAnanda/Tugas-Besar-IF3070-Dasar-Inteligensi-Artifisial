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

Stochastic Hill Climbing, Sideways Move, Random Restart, Simulated Annealing,
dan Genetic Algorithm belum diimplementasikan pada checkout ini. Tiga varian
Hill Climbing bonus dikerjakan setelah seluruh komponen wajib proyek teruji.
