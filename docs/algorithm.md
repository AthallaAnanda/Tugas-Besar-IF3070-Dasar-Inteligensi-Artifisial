# Algoritma Local Search

Seluruh algoritma memaksimalkan objective dengan input State valid. Algoritma mengembalikan initial state, solusi terbaik, nilai terbaik, history, jumlah langkah, dan durasi.

Service meneruskan fungsi sesuai pilihan `objective_1` (total ShippingFee, default) atau `objective_2` (efisiensi pendapatan–waktu–berat) ke seluruh algoritma tanpa mengubah mekanisme pencariannya. Rumus, asumsi, dan interpretasi hasil dijelaskan pada [dokumentasi objective](objective.md).

## Steepest Ascent Hill Climbing

Sumber seluruh varian HC: `origin/feature/hc-chia-fix`, commit `6e74807`. Helper internal berada di `_common.py`.

Pada setiap iterasi, algoritma mengevaluasi semua neighbor dan memilih neighbor dengan nilai tertinggi yang lebih besar dari state saat ini. Pencarian berhenti jika tidak ada perbaikan atau batas iterasi tercapai. Jika beberapa kandidat sama baik, kandidat pertama dipilih.

Parameter `max_iterations` harus integer positif. Default fungsi adalah 1000, sedangkan default form/API adalah 100. Satu pemeriksaan neighborhood dihitung sebagai satu iterasi, termasuk pemeriksaan terakhir tanpa perbaikan. `history` mencakup nilai awal dan setiap iterasi.

```python
result = steepest_ascent(initial_state, objective_1, generate_neighbors, {
    "max_iterations": 100,
})
```

## Stochastic Hill Climbing

Pada setiap iterasi algoritma mencoba satu neighbor acak. Kandidat hanya diterima jika objective meningkat. Percobaan tanpa perbaikan tetap dihitung dan tidak langsung menghentikan pencarian. Pencarian berjalan sampai batas iterasi atau tidak ada neighbor valid.

Parameter `max_iterations` harus integer positif. `seed` mengatur pengacakan. Pemanggilan dengan generator core menggunakan `random_neighbor()`, yang mengacak usulan perubahan placement lalu membentuk kandidat sampai menemukan state valid pertama. Pemanggilan dengan generator kustom menggunakan reservoir sampling terhadap iterable tersebut.

`NoNeighborError` menandai state valid tanpa neighbor. State tidak valid tetap menghasilkan `ValueError` biasa. Keduanya dibedakan agar kesalahan input tidak dianggap sebagai kondisi pencarian selesai.

## Hill Climbing with Sideways Move

Algoritma mengevaluasi seluruh neighbor dan memprioritaskan perbaikan terbaik. Jika tidak ada perbaikan, satu neighbor setara dipilih secara acak selama batas sideways move belum tercapai.

- `max_iterations`: integer positif.
- `maximum_sideways_move`: integer tidak negatif, default fungsi/API 100.
- `seed`: mengatur pemilihan neighbor setara.

Jumlah sideways move bersifat kumulatif selama pencarian, termasuk sebelum dan sesudah perbaikan. Setelah mencapai batas positif, pencarian berhenti. Batas nol hanya mengizinkan perbaikan strict. Hasil tambahan adalah `sideways_moves` dan `maximum_sideways_move`.

## Random Restart Hill Climbing

Random Restart menjalankan Steepest Ascent dari beberapa initial state. Input berupa factory `initial_state_fn` yang dipanggil sekali untuk pencarian awal dan sekali untuk setiap restart.

- `max_iterations`: batas integer positif untuk setiap pencarian Steepest Ascent.
- `maximum_restart`: jumlah pengulangan setelah pencarian awal, integer tidak negatif. Default fungsi/API 10.

Maksimum restart 2 berarti tiga pencarian. Maksimum restart 0 tetap menjalankan pencarian awal. Hasil menyimpan initial state pertama, solusi terbaik seluruh pencarian, total iterasi, `restarts`, `iterations_per_restart`, dan `history_per_restart`.

`history` agregat adalah best-so-far global terhadap total iterasi. Nilainya tidak turun saat pencarian baru dimulai, meskipun initial state baru lebih buruk. `history_per_restart` menyimpan perjalanan objective sebenarnya untuk setiap pencarian, masing-masing termasuk langkah nol.

Service web menyiapkan initial state dengan seed `seed_initial + indeks_pencarian` sebelum memanggil algoritma. Waktu pembentukan semua initial state masuk `initialization_duration`; `duration` tetap berasal langsung dari algoritma. Seed dicatat dalam hasil JSON dan tabel frontend.

## Simulated Annealing

Sumber: `origin/feature/metaheuristic`, commit `6b13b2f`.

Algoritma memilih satu neighbor secara uniform melalui reservoir sampling. Nilai semua neighbor tetap dievaluasi agar algoritma dapat mendeteksi apakah ada perbaikan di neighborhood.

Dengan `delta = nilai_kandidat - nilai_saat_ini`, kandidat dengan delta non-negatif diterima. Kandidat lebih buruk diterima dengan probabilitas `exp(delta / temperature)`. Temperatur dikalikan `cooling_rate` setelah setiap iterasi. Solusi terbaik disimpan terpisah dari state saat ini.

| Parameter | Ketentuan |
|---|---|
| `max_iterations` | Integer tidak negatif. |
| `initial_temperature` | Angka positif dan terbatas. |
| `cooling_rate` | Angka di antara 0 dan 1, eksklusif. |
| `min_temperature` | Angka positif dan terbatas. |
| `seed` | Seed keputusan acak di dalam algoritma. |

Pencarian berhenti ketika temperatur mencapai batas minimum, tidak ada neighbor, atau batas iterasi tercapai. `history`, `best_history`, dan `temperature_history` mencakup langkah nol. `e_deltaet_history` dan `log_e_deltaet_history` hanya berisi langkah yang memiliki kandidat.

Panel analisis SA menampilkan dua grafik bersamaan. Grafik merah adalah probabilitas penerimaan `min(1, exp(ΔE/T))` terhadap iterasi dengan sumbu Y tetap 0–1. Iterasi kandidat dimulai dari 1; tidak dibuat probabilitas palsu pada iterasi nol. Faktor eksponensial yang overflow akibat delta positif menghasilkan probabilitas 1, sedangkan underflow menghasilkan 0. Nilai `null` tanpa penanda overflow tetap dianggap tidak tersedia.

Grafik oranye adalah temperatur setelah setiap iterasi, termasuk temperatur awal pada iterasi nol. Kedua grafik memakai rentang sumbu X yang sama dan bisa diunduh bersama sebagai satu PNG. Bagian **Grafik tambahan** menyediakan temperatur, eksponen mentah `ΔE/T`, dan faktor mentah `exp(ΔE/T)` yang dapat melebihi 1; faktor mentah ini dibedakan dari probabilitas penerimaan. Grafik diturunkan dari history hasil algoritma tanpa mengubah proses pencarian.

`stuck_count` bertambah pada pemeriksaan neighborhood tanpa neighbor bernilai lebih tinggi, termasuk plateau dan keadaan tanpa neighbor. Ini bukan jumlah episode stuck yang terpisah. `accept_worse` adalah jumlah perpindahan ke solusi bernilai lebih rendah.

Hasil mentah SA juga memuat `terminal_state` dan `terminal_value`, yaitu keadaan terakhir yang dapat berbeda dari solusi terbaik. Service web menyajikan solusi terbaik sebagai `final_state`.

## Genetic Algorithm

Sumber perbaikan: `origin/feature/ga-fix`, commit `a986a3e`.

Input awal berupa fungsi yang mengembalikan populasi State valid. Seluruh individu harus memakai definisi kapal dan kendaraan yang sama.

Seleksi parent menggunakan roulette wheel selection dengan peluang sebanding dengan fitness. Fitness harus berhingga dan tidak negatif, dengan jumlah yang tetap berhingga. Jika seluruh fitness nol, parent dipilih secara acak uniform. Crossover memilih gene placement dari salah satu parent dengan peluang sama. Gene yang membuat child melanggar constraint dibatalkan. Mutasi memilih satu neighbor valid secara uniform. Setiap generasi baru dimulai dari populasi kosong dan diisi seluruhnya melalui seleksi parent, crossover atau penyalinan parent, dan mutasi, tanpa elitisme.

| Parameter | Ketentuan |
|---|---|
| `population_size` | Integer minimal 2. |
| `max_iterations` | Jumlah generasi, integer tidak negatif. |
| `crossover_rate` | Angka 0 sampai 1. |
| `mutation_rate` | Angka 0 sampai 1. |
| `seed` | Seed keputusan acak di dalam algoritma. |

`history` menyimpan maksimum populasi, `mean_history` menyimpan rata-rata populasi, dan `best_history` menyimpan objective terbaik sepanjang pencarian. Ketiganya mencakup generasi nol dan memiliki panjang `max_iterations + 1`.

`initial_state` adalah individu terbaik populasi awal. `final_state` adalah solusi terbaik sepanjang pencarian, yang disimpan terpisah dari populasi. Maksimum generasi terakhir dapat lebih rendah dari nilai solusi terbaik.
