# Algoritma pencarian

## Kontrak varian Hill Climbing

Semua varian menerima `State` awal, `objective_function(state)`,
`neighbor_generator(state)`, dan kamus parameter opsional. Nilai objective yang
lebih besar dianggap lebih baik. Hasil berisi `initial_state`, `final_state`,
`best_state`, `best_value`, `history`, `iterations`, serta `duration` dalam
detik. State awal disalin sehingga pencarian tidak mengubah objek pemanggil.
Riwayat dimulai dari nilai awal dan mencatat satu nilai untuk setiap putaran.

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

## Stochastic Hill Climbing

```python
from src.algorithms.hill_climbing import stochastic_hill_climbing
from src.core.neighbor import random_neighbor

result = stochastic_hill_climbing(
    initial_state, objective_1, random_neighbor,
    {"max_iterations": 1000, "seed": 42},
)
```

Setiap putaran mengambil satu neighbor secara acak. Jika nilainya lebih tinggi,
algoritma pindah ke neighbor tersebut. Jika nilainya sama atau lebih rendah,
algoritma bertahan pada state saat ini dan mencoba lagi pada putaran berikutnya.
Pencarian berhenti jika tidak ada neighbor atau batas iterasi tercapai.
`max_iterations` bernilai bawaan 1000 dan `seed` opsional untuk mengulang
pilihan neighbor yang sama.

Untuk masalah kapal, gunakan `random_neighbor` agar pencarian membuat satu
neighbor valid tanpa membangkitkan seluruh state tetangga. Usulan langkah
diacak lalu dicoba sampai satu penempatan valid ditemukan. Kandidat tidak
valid boleh dilewati. Pemanggilan lama dengan `generate_neighbors` tetap
diterima dan otomatis memakai sampler core yang sama.

Iterable neighbor khusus tetap didukung untuk kompatibilitas. Jika pemanggil
memberikan iterable tersebut, pemilihan acak perlu menelusuri isinya; jalur
ini tidak memiliki penghematan pembangkitan state seperti sampler core.

## Hill Climbing with Sideways Move

```python
from src.algorithms.hill_climbing import sideways_move

result = sideways_move(
    initial_state, objective_1, generate_neighbors,
    {"max_iterations": 1000, "maximum_sideways_move": 100, "seed": 42},
)
```

Jika tidak ada perbaikan, algoritma boleh memilih neighbor dengan nilai sama
secara acak. Jumlah perpindahan setara dibatasi oleh
`maximum_sideways_move` (bawaan 100, termasuk nol) dan dilaporkan pada
`sideways_moves`. Pencarian berhenti segera ketika jumlah langkah setara
mencapai batas. Perbaikan selalu dipilih sebelum langkah setara.

## Random Restart Hill Climbing

```python
from src.algorithms.hill_climbing import random_restart

def make_initial_state():
    return create_initial_state(ships, vehicles)

result = random_restart(
    make_initial_state, objective_1, generate_neighbors,
    {"max_iterations": 1000, "maximum_restart": 5},
)
```

`initial_state_fn` membuat state awal baru. Fungsi tersebut dipanggil sekali
untuk pencarian pertama, lalu sekali per restart. `maximum_restart` menghitung
restart setelah pencarian pertama (bawaan 10, termasuk nol). Algoritma memilih
solusi terbaik dari semua run dan mengembalikan jumlah restart pada `restarts`,
jumlah iterasi tiap run pada `iterations_per_restart`, serta total iterasi
pada `iterations`. `history` adalah nilai terbaik sejauh ini sepanjang seluruh
run. `history_per_restart` menyimpan riwayat tiap run secara terpisah, termasuk
nilai awal, agar perubahan nilai saat restart bisa terlihat pada grafik. Batas
`max_iterations` berlaku untuk setiap run.

Simulated Annealing dan Genetic Algorithm dikerjakan pada modul terpisah.
