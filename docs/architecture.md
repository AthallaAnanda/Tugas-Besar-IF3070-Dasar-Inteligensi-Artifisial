# Arsitektur dan kontrak problem core

Kode Python ada di `src/`. `src/core/` menyediakan representasi masalah untuk
algoritma di `src/algorithms/`. Service di `src/services/` menghubungkan algoritma
dengan API Flask di `src/app.py`. Visualisasi web tetap ada di `frontend/`.

## Data masalah

- `Vehicle(id, width, length, shipping_fee, weight, eta)` menyimpan ukuran dalam
  satuan grid. `weight` memakai satuan kapasitas pada data soal.
- `Ship(id, width, length, max_capacity)` menyimpan ukuran geladak dan batas
  total berat kendaraan.
- `Placement(vehicle_id, ship_id, x, y, orientation)` menyimpan sel kiri atas
  kendaraan. `orientation` bernilai `horizontal` atau `vertical`.
- `State(ships, vehicles)` menyimpan `ships` sebagai daftar `ShipState` dan
  `vehicles` sebagai kamus berdasarkan ID. Kendaraan tanpa placement tetap
  tercatat di `vehicles` dan bisa dilihat lewat `outside_vehicle_ids`.

Koordinat dimulai dari nol. Nilai x bertambah ke kanan dan y bertambah ke bawah.
Kendaraan yang diangkut harus berada sepenuhnya di dalam geladak. Kendaraan
yang tidak diangkut tidak memiliki placement sama sekali.

## Pemakaian core

```python
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.state import create_initial_state, load_problem

problem = load_problem("data/sample/small.json")
initial_state = create_initial_state(
    [item.ship for item in problem.ships], list(problem.vehicles.values()), seed=42
)
assert is_valid(initial_state)
print(objective_1(initial_state))
print(initial_state.to_dict())
neighbors = generate_neighbors(initial_state)
```

`generate_neighbors` memberi state baru yang valid lewat operasi tukar,
pindah ke koordinat lain, dan putar. Kendaraan di luar dapat ditukar dengan
kendaraan di kapal atau dipindahkan ke suatu koordinat di geladak. Mengeluarkan
kendaraan tanpa pertukaran bukan satu langkah neighbor. State asal tidak berubah.
`random_neighbor` memilih satu
dari hasil tersebut dan menerima generator angka acak opsional untuk eksperimen.
`State.copy()` membuat salinan yang dapat diubah secara mandiri.

`State.from_dict(data)` menerima `vehicles` dan `ships`. Setiap kapal bisa
langsung ditulis dengan atribut kapal, atau memakai objek `ship` beserta
`placements`. Kedua bentuk menerima `placements` sebagai daftar opsional.
`load_problem(path)` membaca format ini dari JSON. Fungsi
`create_initial_state(ships, vehicles, seed)` membuat penempatan awal acak;
kendaraan yang tidak berhasil ditempatkan tetap berada di luar.

`is_valid(state)` memeriksa referensi ID, satu penempatan per kendaraan,
batas geladak, sel yang bertumpuk, dan jumlah berat per kapal. `objective_1`
menghitung jumlah ShippingFee kendaraan yang diangkut, dan menolak state tidak
valid. `State.to_dict()` menyediakan daftar kendaraan, kapal, placement, grid,
kendaraan di luar, dan nilai untuk API atau visualisasi.

## Kontrak algoritma

Algoritma menerima State, fungsi objective, pembuat neighbor, dan parameter.
Hasilnya disepakati berisi `best_state`, `best_value`, `history`, `iterations`,
dan `duration`. Steepest Ascent juga menyertakan `initial_state` dan
`final_state`; keduanya berupa objek `State`, dan `final_state` adalah solusi
terbaik. Integrasi service merupakan tahap berikutnya.
