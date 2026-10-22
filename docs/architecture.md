# Arsitektur

Aplikasi menggunakan Python/Flask untuk pencarian dan API, serta HTML, CSS, dan JavaScript untuk visualisasi. Frontend disajikan oleh Flask dan tidak membutuhkan proses build.

## Komponen

| Komponen | Tanggung jawab |
|---|---|
| `src/core/` | Kendaraan, kapal, placement, state, constraint, objective, dan neighbor. |
| `src/algorithms/` | Pencarian dan pengumpulan history numerik. |
| `src/services/optimization.py` | Registry parameter, validasi konfigurasi, inisialisasi, pemanggilan algoritma, dan penjelasan hasil. |
| `src/services/validation.py` | Validasi tipe, nilai terbatas, dan batas numerik parameter. |
| `src/services/serialization.py` | Konversi State ke JSON, statistik solusi, dan normalisasi nilai non-finite. |
| `src/services/output.py` | Penyimpanan JSON dan pembuatan grafik PNG per run menggunakan Matplotlib Agg tanpa GUI. |
| `src/app.py` | Frontend dan endpoint API. |
| `frontend/js/app.js` | Form dataset, parameter, seed, request optimasi, dan status. |
| `frontend/js/result-view.js` | Ringkasan hasil, initial state, solusi terbaik, dan grafik. |
| `frontend/js/visualization.js` | Penggambaran geladak menggunakan SVG dan ekspor JPG berlatar putih melalui canvas. |
| `frontend/js/charts.js` | Grafik history, pencarian Random Restart, dan diagnostik SA pada Canvas. |
| `frontend/js/results.js` | Seri grafik dan label iterasi/generasi. |
| `frontend/js/ui.js` | Elemen form, format angka, daftar nilai, dan unduhan. |

## Representasi

`Vehicle` menyimpan ID, width, length, ShippingFee, weight, dan ETA. `Ship` menyimpan ID, ukuran geladak, dan kapasitas berat. Keduanya merupakan dataclass frozen.

`Placement` menyimpan kendaraan, kapal, koordinat integer x/y, serta orientasi. Koordinat menunjuk sel kiri atas. Orientasi horizontal memakai dimensi asli; vertical menukar width dan length.

`State` menyimpan daftar `ShipState` dan kamus kendaraan. Kendaraan yang tidak diangkut tidak memiliki placement dan tersedia melalui `outside_vehicle_ids`. `deck_grid()` membentuk grid; `copy()` membuat salinan terpisah.

`is_valid()` memeriksa referensi, keunikan placement, batas geladak, overlap, dan kapasitas per kapal. `objective_1()` menjumlahkan ShippingFee kendaraan yang dimuat pada state valid. `objective_2()` menjumlahkan skor efisiensi pendapatan–waktu–berat per kapal. Service memilih fungsi dari registry `OBJECTIVES` dan meneruskannya ke algoritma serta serialisasi state agar seluruh nilai hasil konsisten. `State.to_dict()` tanpa argumen tetap memakai objective utama. Rumus bonus dijelaskan di [dokumentasi objective](objective.md).

`generate_neighbors()` menghasilkan pertukaran kendaraan, perpindahan koordinat, dan perubahan orientasi. Kendaraan di luar dapat dimuat atau ditukar dengan kendaraan di dalam. Pengeluaran kendaraan tanpa pertukaran tidak disediakan sebagai langkah tersendiri. Kandidat divalidasi dan dideduplikasi.

`_possible_moves()` menyusun usulan perubahan placement, lalu `_apply_move()` membentuk State kandidat. `random_neighbor()` mengacak daftar usulan dan berhenti pada kandidat valid pertama, tanpa memanggil enumerasi semua state dari `generate_neighbors()`. State valid tanpa kandidat menghasilkan `NoNeighborError`. Stochastic HC menggunakan jalur ini; SA dan mutasi GA tetap memakai generator seluruh neighbor melalui kontrak algoritma asalnya.

## Alur satu pencarian

1. API menerima dataset, algoritma, parameter, dan seed.
2. Service memvalidasi input dan membentuk initial state atau populasi awal.
3. Service memanggil algoritma dengan kontrak dari branch sumbernya.
4. Algoritma mengembalikan solusi, objective, history, jumlah langkah, dan durasi.
5. Service menambahkan konfigurasi, statistik solusi, serta penjelasan penghentian, lalu menyerialisasi hasil.
6. API memanggil service output untuk menyimpan grafik PNG dan JSON lengkap dengan metadata lokasi file.
7. Frontend menggambar initial state, solusi terbaik, grafik, serta status penyimpanan. Unduhan dibuat dari hasil yang diterima browser.

Direktori output ditetapkan melalui `app.config["OUTPUT_DIR"]`, default `<root repository>/output`. Setiap run menggunakan waktu UTC dan ID acak untuk nama unik. Grafik menggunakan `Figure` dan `FigureCanvasAgg` tanpa state global `pyplot`; rendering dilindungi lock untuk request bersamaan. JSON dipublikasikan melalui rename file sementara setelah seluruh grafik selesai. Jika gagal, service membersihkan file run tersebut dan API mengembalikan hasil optimasi dengan metadata kegagalan penyimpanan. Pemanggilan langsung `run_optimization()` tetap hanya menghitung hasil. Pengujian service/API memakai direktori output sementara.

Stochastic HC, Sideways, SA, dan GA menggunakan seed algoritma yang terpisah dari seed inisialisasi. Registry capabilities menandai kebutuhan seed ini melalui `uses_algorithm_seed`. GA membentuk seed individu melalui generator lokal; ukuran populasi yang lebih besar memperpanjang urutan seed dengan prefix konsisten.

Random Restart menerima factory yang menyediakan `maximum_restart + 1` initial state yang disiapkan service. Seed dimulai dari seed initial state dan bertambah satu per pencarian. Serialisasi meneruskan history dan jumlah iterasi per pencarian; frontend menampilkan tabel serta grafik lokal terpisah dari best-so-far global. Nilai form disimpan per ID algoritma.

`duration` berasal langsung dari algoritma. Pembentukan kondisi awal diukur terpisah sebagai `initialization_duration`, termasuk seluruh initial state Random Restart. Serialisasi, penyimpanan file, serta penggambaran grafik backend/browser bukan bagian durasi pencarian.

## Referensi implementasi

Seluruh modul HC serta `src/core/neighbor.py` berasal dari `origin/feature/hc-chia-fix` commit `6e74807`. Perubahan neighbor berasal dari commit core `062caa8`. SA dan GA berasal dari `origin/feature/metaheuristic` commit `6b13b2f`. Kebutuhan API dan visualisasi ditangani di luar algoritma. Perubahan urutan enumerasi core dapat mengubah hasil seeded dibanding versi core sebelumnya; reproduksibilitas diperiksa dengan kode dan lingkungan yang sama.
