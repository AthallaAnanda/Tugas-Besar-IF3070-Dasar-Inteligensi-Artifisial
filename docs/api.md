# API Optimasi

API disajikan oleh Flask pada origin yang sama dengan frontend. Request POST menggunakan `Content-Type: application/json`.

| Endpoint | Fungsi |
|---|---|
| `GET /` | Halaman aplikasi. |
| `GET /api/health` | Status koneksi server. |
| `GET /api/capabilities` | Algoritma, objective, schema parameter, dan nilai default. |
| `GET /api/sample` | Dataset contoh. |
| `POST /api/optimize` | Menjalankan satu pencarian, menyimpan JSON/grafik ke `output/`, dan mengembalikan hasil lengkap. |

## Request

```json
{
  "algorithm": "genetic_algorithm",
  "objective": "objective_1",
  "seed": 42,
  "algorithm_seed": 43,
  "problem": {
    "ships": [{"id": "s", "width": 2, "length": 1, "max_capacity": 2}],
    "vehicles": [
      {"id": "A", "width": 1, "length": 1, "shipping_fee": 10, "weight": 1, "eta": 0},
      {"id": "B", "width": 1, "length": 1, "shipping_fee": 20, "weight": 1, "eta": 0}
    ]
  },
  "parameters": {
    "population_size": 4,
    "max_iterations": 3,
    "crossover_rate": 0.8,
    "mutation_rate": 0.2,
    "elitism": 1,
    "tour_size": 2
  }
}
```

- `problem` wajib diisi. Service membaca data melalui `State.from_dict()` lalu membentuk initial state atau populasi baru secara acak. Placement pada input harus valid, tetapi bukan titik awal pencarian.
- `algorithm`: salah satu ID pada tabel berikut. Default `hill_climbing` menggunakan Steepest Ascent.
- `objective`: `objective_1` (default, total ShippingFee) atau `objective_2` (efisiensi pendapatan–waktu–berat). Skor bonus per kapal adalah `total ShippingFee / ((1 + ETA terlama) × (1 + total berat / kapasitas))`, lalu dijumlahkan untuk seluruh kapal. Lihat [asumsi dan kasus khusus](objective.md).
- `seed` dan `algorithm_seed`: integer tidak negatif. Jika `seed` tidak diisi, service menghasilkan seed baru. Default `algorithm_seed` adalah `seed + 1`; nilai `null` meminta seed baru.
- `parameters`: object sesuai schema algoritma dari `/api/capabilities`. Parameter yang tidak diisi menggunakan default. Parameter tidak dikenal ditolak.

Frontend menyediakan pilihan seed **Acak** (default) dan **Manual**. Pilihan Acak mengirim `"seed": null` dan `"algorithm_seed": null` pada setiap request; kedua seed dibangkitkan secara terpisah oleh backend. Pilihan Manual mengirim nilai integer dari form. `configuration.seed` dan `configuration.algorithm_seed` pada respons/unduhan JSON selalu menyimpan nilai aktual yang digunakan, sehingga hasil acak dapat dijalankan kembali secara manual.

Setiap item `objectives` pada `/api/capabilities` menyertakan `id`, `label`, dan `description`. Seluruh algoritma mendukung kedua pilihan objective.

GA memvalidasi bahwa elite lebih kecil dari populasi dan tournament size tidak melebihi populasi. Seed individu populasi awal dicatat dalam `configuration.population_seeds`.

### Pilihan algoritma HC

| ID | Algoritma | Parameter |
|---|---|---|
| `hill_climbing` | Steepest Ascent | `max_iterations`, integer positif. |
| `stochastic_hill_climbing` | Stochastic HC | `max_iterations`, integer positif. |
| `sideways_move` | HC with Sideways Move | `max_iterations` positif; `maximum_sideways_move` integer tidak negatif. |
| `random_restart` | Random Restart HC | `max_iterations` positif per pencarian; `maximum_restart` integer tidak negatif. |
| `simulated_annealing` | SA | Parameter temperatur dan iterasi. |
| `genetic_algorithm` | GA | Parameter populasi, generasi, seleksi, crossover, mutasi, dan elitisme. |

Schema pada `/api/capabilities` menyertakan `uses_algorithm_seed: true` untuk Stochastic HC, Sideways, SA, dan GA. Seed algoritma diteruskan ke parameter `seed` fungsi algoritma. Steepest Ascent bersifat deterministik; Random Restart menggunakan seed initial state untuk urutan initial state-nya.

Jika `variant` disertakan untuk HC, nilainya harus sesuai ID algoritma: `steepest_ascent`, `stochastic`, `sideways_move`, atau `random_restart`.

Untuk Random Restart, contoh pilihan algoritma/parameter adalah:

```json
{
  "algorithm": "random_restart",
  "seed": 42,
  "parameters": {"max_iterations": 100, "maximum_restart": 2}
}
```

Tambahkan `problem` seperti pada contoh request lengkap. Konfigurasi ini membentuk tiga pencarian dengan seed `[42, 43, 44]`. Service membentuk semua initial state sebelum mengukur pencarian, lalu memasoknya melalui factory. `maximum_restart: 0` menjalankan satu pencarian awal.

## Respons

| Field | Isi |
|---|---|
| `status` | `success`. |
| `algorithm` | ID algoritma. |
| `step_type` | `iteration` atau `generation`. |
| `objective_value` | Objective terbaik sepanjang pencarian. |
| `iterations` | Jumlah iterasi atau generasi; pada Random Restart merupakan total iterasi seluruh pencarian. |
| `duration` | Durasi pencarian dari algoritma dalam detik. |
| `initialization_duration` | Durasi pembentukan initial state, populasi GA, atau seluruh initial state Random Restart. |
| `initial_state` | State awal; pada GA individu terbaik populasi awal, pada Random Restart state pencarian pertama. |
| `final_state` | Solusi terbaik sepanjang pencarian. |
| `history` | Objective saat ini pada HC satu state/SA, maksimum populasi pada GA, atau best-so-far global pada Random Restart. Termasuk langkah nol. |
| `best_history` | Objective terbaik sampai setiap langkah. |
| `mean_history` | Rata-rata objective populasi GA; `null` pada algoritma lain. |
| `metrics` | Statistik dan history khusus algoritma. |
| `statistics` | Total ShippingFee aktual (`total_shipping_fee`), jumlah kendaraan dimuat/di luar, serta statistik per kapal. Setiap kapal memuat `shipping_fee`, `max_eta` (hari; `null` jika kosong), berat muatan, kapasitas, dan utilisasi geladak. |
| `configuration` | Parameter dan seed yang digunakan. |
| `stop_reason` | Penjelasan service mengenai kondisi penghentian. |
| `output` | Status penyimpanan otomatis dan lokasi file hasil/grafik. |

State JSON menyertakan kendaraan, kapal, placement, grid, kendaraan di luar, dan `value` sesuai objective terpilih pada `configuration.objective`. Untuk bonus, `value` merupakan skor efisiensi, bukan total ShippingFee; pendapatan aktual tersedia pada `statistics.total_shipping_fee`. `stop_reason` dihitung service dari ringkasan hasil/history: `no_improvement`, `min_temperature`, `no_neighbors`, `max_iterations`, `max_sideways_moves`, `no_admissible_move`, atau `max_restarts`. Stochastic tidak dihentikan atau dilabeli berhenti hanya karena satu percobaan tidak membaik. Implementasi algoritma tidak memerlukan parameter tambahan untuk integrasi web.

Metrik SA memuat `stuck_count`, `accept_worse`, `temperature_history`, `e_deltaet_history`, dan `log_e_deltaet_history`. Faktor eksponensial yang overflow diserialisasi sebagai `null` dan ditandai dalam `e_deltaet_overflow_history`. Metrik GA memuat `population_size`.

Metrik Sideways memuat `sideways_moves` dan `maximum_sideways_move`. Penghitungan bersifat kumulatif, bukan hanya rentetan perpindahan setara terakhir.

Metrik Random Restart memuat `restarts`, `iterations_per_restart`, dan `history_per_restart`. Indeks nol mengacu pada pencarian awal. Jumlah pencarian adalah `restarts + 1`; jumlah langkah setiap history adalah iterasi pencarian tersebut ditambah satu. `configuration.restart_seeds` mencatat seed dengan indeks yang sama. Solusi terbaik berasal dari maksimum objective akhir seluruh pencarian. `history` agregat tidak menunjukkan objective aktual state setelah restart; gunakan `history_per_restart` untuk itu.

### Penyimpanan otomatis

Setelah optimasi berhasil, backend menyimpan JSON dan PNG tanpa request tambahan. Nama unik memuat waktu UTC, algoritma, dan ID acak. Contoh metadata (run-id disingkat):

```json
{
  "output": {
    "status": "saved",
    "run_id": "<run-id>",
    "result": "output/results/<run-id>.json",
    "plots": ["output/plots/<run-id>-objective.png"]
  }
}
```

Path menunjuk file lokal di server, relatif terhadap root repository; bukan URL unduhan. JSON yang tersimpan memuat respons lengkap termasuk metadata ini. Setiap algoritma menyimpan grafik objective, GA dengan rata-rata populasi. SA menambahkan `<run-id>-sa-analysis.png` berisi probabilitas penerimaan dan temperatur. Random Restart menambahkan `<run-id>-restart-<n>.png` untuk setiap pencarian, termasuk pencarian awal (`n = 0`). `duration` dan `initialization_duration` tidak mencakup penyimpanan atau rendering grafik.

Jika penyimpanan gagal, API tetap mengembalikan HTTP 200 dengan hasil optimasi `status: "success"`, tetapi `output` berisi `status: "error"` dan `message`. Frontend menampilkan pesan tersebut dan tetap menyediakan unduhan. Detail kegagalan dicatat ke log server. File parsial dari run yang gagal dibersihkan jika filesystem mengizinkan; hasil run lain tetap dipertahankan. Request tidak valid tidak menghasilkan file output.

## Kesalahan

Input tidak valid menghasilkan HTTP 400. Content type tidak didukung menghasilkan HTTP 415.

```json
{
  "status": "error",
  "message": "Jumlah elite harus lebih kecil daripada jumlah populasi"
}
```
