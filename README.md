# Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027: Optimasi Muatan Kapal Menggunakan *Local Search*

Program ini dikembangkan untuk menentukan pemilihan dan penempatan kendaraan pada geladak kapal menggunakan algoritma *local search*. Geladak dan kendaraan direpresentasikan dalam bentuk grid dua dimensi. Setiap susunan kendaraan harus memenuhi batas geladak, larangan tumpang tindih, serta kapasitas berat maksimum kapal. Kendaraan yang tidak terpilih tetap tercatat sebagai kendaraan di luar kapal.

Tujuan utama pencarian adalah memaksimalkan total tarif pengiriman (*ShippingFee*) dari kendaraan yang berhasil dimuat. Selain fungsi objektif utama, program menyediakan fungsi objektif bonus yang mempertimbangkan pendapatan pengangkutan, estimasi waktu pengiriman, dan penggunaan kapasitas berat. Program juga mendukung penempatan kendaraan pada lebih dari satu kapal.

Program ini disusun oleh **Kelompok 25 - tengahtengah** untuk memenuhi Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial.

## Algoritma Pencarian

Antarmuka menyediakan enam pilihan algoritma, yaitu:

1. *Steepest Ascent Hill Climbing*.
2. *Stochastic Hill Climbing*.
3. *Hill Climbing with Sideways Move*.
4. *Random Restart Hill Climbing*.
5. *Simulated Annealing*.
6. *Genetic Algorithm*.

Setiap pencarian menghasilkan keadaan awal (*initial state*), solusi terbaik, nilai objektif, jumlah iterasi atau generasi, durasi pencarian, serta grafik perkembangan nilai objektif.

Steepest Ascent memilih neighbor terbaik yang meningkatkan nilai objektif. Stochastic HC mencoba satu neighbor acak pada setiap iterasi dan hanya menerima peningkatan. Sideways Move juga mengizinkan perpindahan bernilai sama dengan jumlah terbatas. Random Restart menjalankan Steepest Ascent dari beberapa keadaan awal, kemudian mempertahankan solusi terbaik seluruh pencarian.

SA dapat menerima perpindahan ke solusi yang lebih buruk berdasarkan temperatur dan probabilitas penerimaan. GA menggunakan populasi kandidat yang diperbarui melalui seleksi, crossover, dan mutasi. Seluruh algoritma menggunakan fungsi objektif yang dipilih dan hanya mengevaluasi susunan yang memenuhi batasan persoalan.

| Algoritma | Parameter pada antarmuka |
|---|---|
| Steepest Ascent dan Stochastic HC | `max_iterations`, bilangan bulat positif. |
| Sideways Move | `max_iterations` positif dan `maximum_sideways_move` berupa bilangan bulat tidak negatif. |
| Random Restart | `max_iterations` positif per pencarian dan `maximum_restart` berupa bilangan bulat tidak negatif. |
| SA | `max_iterations` tidak negatif, temperatur awal dan minimum positif, serta `cooling_rate` lebih besar dari nol dan lebih kecil dari satu. |
| GA | `population_size` minimal dua, `max_iterations` tidak negatif, serta `crossover_rate` dan `mutation_rate` pada rentang nol hingga satu. |

## Tata Cara Menjalankan Kode Program

Program membutuhkan Python 3.10 atau versi yang lebih baru. Jalankan perintah berikut dari direktori utama repositori untuk membuat lingkungan virtual, memasang dependensi, dan menjalankan aplikasi.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.app
```

Setelah server berjalan, buka **http://127.0.0.1:5000/** melalui peramban. Antarmuka disajikan langsung oleh Flask sehingga tidak memerlukan proses kompilasi frontend.

## Tata Cara Penggunaan Program

1. Gunakan data sampel atau unggah berkas JSON yang memuat data kapal dan kendaraan. Data juga dapat diubah melalui kolom penyuntingan dataset.
2. Pilih algoritma, fungsi objektif, mode pengacakan, dan parameter pencarian.
3. Tekan tombol **Jalankan optimasi** untuk memulai pencarian.
4. Periksa susunan awal dan solusi terbaik, kendaraan di dalam maupun di luar kapal, nilai objektif, durasi, serta statistik pencarian.
5. Unduh hasil lengkap dalam format JSON, grafik dalam format PNG, atau visualisasi geladak dalam format JPG melalui tombol yang tersedia.

Data sampel pada `data/sample/small.json` memuat satu kapal dengan geladak berukuran 7 × 6, kapasitas berat 15 unit, dan 25 kendaraan.

### Representasi Persoalan dan Format Masukan

Kelas `Vehicle` menyimpan data kendaraan, sedangkan `Ship` menyimpan dimensi geladak dan kapasitas kapal. `Placement` menyatakan posisi serta orientasi kendaraan, `ShipState` menggabungkan kapal dengan daftar penempatannya, dan `State` merepresentasikan keseluruhan solusi. Kendaraan tanpa placement tetap tercatat sebagai kendaraan di luar kapal.

Koordinat `(x, y)` berupa bilangan bulat dan menunjuk sel kiri atas kendaraan. Titik `(0, 0)` berada pada sudut kiri atas geladak; nilai x bertambah ke kanan dan y bertambah ke bawah. Orientasi horizontal menggunakan dimensi asli, sedangkan orientasi vertikal menukar lebar dan panjang. Neighbor dibentuk melalui pertukaran kendaraan, perpindahan posisi, atau perubahan orientasi. Pertukaran dapat melibatkan kendaraan di dalam dan di luar kapal; pengeluaran kendaraan tanpa pertukaran tidak disediakan sebagai langkah tersendiri.

Masukan menggunakan JSON dengan komponen `ships` dan `vehicles`. Contoh minimalnya adalah sebagai berikut.

```json
{
  "ships": [
    {"id": "ship_1", "width": 7, "length": 6, "max_capacity": 15}
  ],
  "vehicles": [
    {"id": "A", "width": 2, "length": 2, "shipping_fee": 60, "weight": 3, "eta": 2}
  ]
}
```

Ukuran kendaraan dan kapal harus berupa bilangan bulat positif. Berat, tarif pengiriman, serta kapasitas merupakan bilangan tidak negatif yang berhingga, sedangkan ETA berupa bilangan bulat tidak negatif. Setiap identitas kendaraan dan kapal harus unik. Untuk persoalan multi-kapal, tambahkan definisi kapal lain pada daftar `ships`. Setiap kendaraan hanya dapat dimuat satu kali pada seluruh armada.

Program membentuk keadaan awal secara acak dari definisi persoalan. Penempatan yang disertakan pada dataset harus valid, tetapi tidak digunakan sebagai titik awal pencarian. Inisialisasi mengacak urutan kendaraan dan kemungkinan penempatannya, dengan peluang 25% bagi setiap kendaraan untuk tetap berada di luar tanpa percobaan penempatan.

### Pengaturan Pengacakan pada Program

Program menyediakan mode **Acak** dan **Manual**. Pada mode Acak, server membangkitkan nilai *seed* inisialisasi dan seed algoritma secara terpisah pada setiap permintaan. Pada mode Manual, pengguna dapat memasukkan kedua nilai tersebut untuk mengulang suatu pencarian. Seed aktual dicatat melalui `configuration.seed` dan `configuration.algorithm_seed` dalam hasil JSON.

Seed inisialisasi mengatur pembentukan susunan awal atau populasi awal. Seed algoritma mengatur keputusan acak pada Stochastic HC, Sideways Move, SA, dan GA. Steepest Ascent bersifat deterministik setelah keadaan awal ditentukan, sedangkan Random Restart membentuk urutan seed dari seed inisialisasi ditambah indeks pencarian.

Penggunaan dataset, parameter, seed, kode, dan lingkungan yang sama memungkinkan susunan serta riwayat pencarian diulang. Durasi tetap dapat berbeda. Untuk tiga pengulangan eksperimen, pengguna dapat menentukan pasangan seed, misalnya `(42, 142)`, `(43, 143)`, dan `(44, 144)`, lalu menggunakan daftar yang sama pada konfigurasi yang dibandingkan.

Pada GA, seed inisialisasi menentukan seluruh populasi awal. Keadaan awal yang ditampilkan merupakan individu terbaik dari populasi tersebut. Oleh karena itu, perubahan jumlah populasi atau fungsi objektif dapat menghasilkan tampilan keadaan awal yang berbeda meskipun seed inisialisasinya sama.

### Penyajian Hasil Pencarian

Pada Sideways Move, program menampilkan jumlah perpindahan bernilai sama beserta batas `maximum_sideways_move`. Penghitungannya bersifat kumulatif selama pencarian. Batas nol tetap memungkinkan perpindahan yang meningkatkan nilai objektif.

Pada Random Restart, parameter `maximum_restart` menyatakan jumlah pengulangan setelah pencarian awal. Sebagai contoh, batas dua restart menghasilkan tiga pencarian. Antarmuka menampilkan tabel seed, jumlah iterasi, serta nilai objektif awal dan akhir untuk setiap pencarian. Grafik utama menunjukkan nilai terbaik sepanjang seluruh pencarian, sedangkan grafik per pencarian dapat dipilih dan diunduh secara terpisah.

Pada SA, panel analisis menampilkan faktor `exp(ΔE/T)`, probabilitas penerimaan `min(1, exp(ΔE/T))`, dan temperatur terhadap iterasi. Setiap grafik memiliki tombol unduh PNG tersendiri. Faktor eksponensial dapat bernilai lebih dari satu, sedangkan probabilitas penerimaan berada pada rentang nol hingga satu. Statistik juga memuat frekuensi pemeriksaan tanpa neighbor yang lebih baik serta jumlah penerimaan solusi yang lebih buruk.

Pada GA, seleksi induk menggunakan *roulette wheel selection* dengan peluang sebanding dengan nilai *fitness*. Jika seluruh fitness bernilai nol, induk dipilih secara acak. Generasi berikutnya dibentuk melalui seleksi, persilangan (*crossover*) atau penyalinan induk, serta mutasi, tanpa elitisme. Grafik menampilkan nilai maksimum dan rata-rata populasi serta nilai terbaik sepanjang pencarian. Solusi terbaik disimpan terpisah sehingga dapat berbeda dari individu terbaik pada generasi terakhir.

## Penyimpanan Hasil Output Optimasi

Setiap permintaan optimasi yang berhasil melalui `POST /api/optimize` secara otomatis menyimpan hasil pada struktur berikut.

```text
output/
├── results/
│   └── <run-id>.json
└── plots/
    ├── <run-id>-objective.png
    ├── <run-id>-sa-analysis.png       # khusus SA
    └── <run-id>-sa-exponential.png    # khusus SA
```

Nama `run-id` memuat waktu UTC, identitas algoritma, dan identitas acak agar hasil setiap eksekusi memiliki nama yang berbeda. Direktori penyimpanan ditentukan relatif terhadap direktori utama repositori.

Berkas JSON memuat hasil lengkap, termasuk susunan awal dan solusi terbaik, riwayat nilai objektif, statistik, konfigurasi, seed, serta lokasi berkas keluaran. Seluruh algoritma menyimpan grafik objektif. Pada GA, grafik mencakup maksimum dan rata-rata populasi serta nilai terbaik sepanjang pencarian. Pada SA, dua PNG tambahan menyimpan analisis probabilitas dan temperatur serta faktor eksponensial. Random Restart menyimpan satu grafik objektif global secara otomatis.

Grafik PNG dibuat menggunakan Matplotlib di server. Pembentukan keadaan awal diukur terpisah sebagai `initialization_duration`, sedangkan `duration` hanya mencakup proses pencarian algoritma. Pembuatan grafik dan penyimpanan berkas tidak termasuk dalam durasi pencarian. Pemanggilan langsung `run_optimization()` hanya menghitung hasil; penyimpanan otomatis dilakukan oleh endpoint API.

Status penyimpanan tersedia pada field `output` dalam respons JSON dan tidak ditampilkan pada antarmuka. Apabila penyimpanan gagal, hasil pencarian tetap dapat ditampilkan serta diunduh. Rincian kesalahan dicatat pada log server.

Repositori telah menyertakan hasil eksperimen dalam `output/`. Hasil baru yang belum dilacak tetap mengikuti aturan `.gitignore`. Untuk menyertakan hasil tambahan, gunakan `git add -f` dengan path berkas yang dipilih.

## Objective Function

Fungsi utama `objective_1` menjumlahkan tarif pengiriman seluruh kendaraan yang dimuat. Fungsi bonus `objective_2`, dengan label **Efisiensi Pendapatan, Waktu, dan Berat**, menghitung skor setiap kapal melalui rumus berikut.

```text
skor kapal = total ShippingFee / ((1 + ETA terlama) × (1 + total berat / kapasitas))
```

Skor seluruh kapal kemudian dijumlahkan. Kapal kosong memperoleh skor nol. Pada state valid dengan kapasitas nol, rasio penggunaan berat didefinisikan sebagai nol. ETA terlama digunakan sebagai pendekatan waktu penyelesaian pengiriman, sedangkan rasio berat menyatakan penggunaan kapasitas kapal. Skor bonus merupakan ukuran penilaian model, bukan perhitungan laba bersih atau pendapatan per hari.

Seluruh algoritma dapat menggunakan kedua fungsi tersebut. Nilai pada state, grafik, dan hasil JSON mengikuti fungsi yang dipilih. Total tarif pengiriman tetap dicatat secara terpisah dalam statistik.

Sebagai contoh, pada kapal berkapasitas 100, muatan dengan tarif 200, ETA maksimum empat hari, dan berat 100 memperoleh skor bonus 20. Muatan dengan tarif 180, ETA maksimum dua hari, dan berat 50 memperoleh skor 40. Fungsi utama memilih muatan pertama, sedangkan fungsi bonus memilih muatan kedua. Nilai numerik kedua fungsi tidak dibandingkan secara langsung karena maknanya berbeda. Pada SA, perbedaan skala fungsi objektif juga memengaruhi probabilitas penerimaan pada temperatur yang sama.

## Layanan API

Flask menyajikan antarmuka dan API pada alamat asal yang sama. Permintaan POST menggunakan `Content-Type: application/json`.

| Endpoint | Keterangan |
|---|---|
| `GET /` | Halaman aplikasi. |
| `GET /api/health` | Status koneksi server. |
| `GET /api/capabilities` | Pilihan algoritma, fungsi objektif, skema parameter, dan nilai bawaan. |
| `GET /api/sample` | Dataset contoh. |
| `POST /api/optimize` | Pelaksanaan pencarian dan penyimpanan hasil. |

Permintaan optimasi memuat `problem` dengan format dataset di atas, serta `algorithm`, `objective`, `parameters`, `seed`, dan `algorithm_seed`. Identitas algoritma yang tersedia adalah `hill_climbing`, `stochastic_hill_climbing`, `sideways_move`, `random_restart`, `simulated_annealing`, dan `genetic_algorithm`. Nilai bawaan algoritma adalah `hill_climbing`, sedangkan fungsi objektif bawaan adalah `objective_1`.

Seed yang diberikan harus berupa bilangan bulat tidak negatif. Nilai `null` meminta server membangkitkan seed baru. Jika `algorithm_seed` tidak disertakan, nilainya mengikuti seed inisialisasi aktual ditambah satu. Parameter yang tidak diisi menggunakan nilai bawaan pada skema; parameter tidak dikenal ditolak, termasuk `elitism` dan `tour_size` pada GA.

Respons berhasil memuat state awal dan akhir, `objective_value`, `history`, `best_history`, `mean_history`, jumlah iterasi, durasi, konfigurasi, statistik, kondisi berhenti, dan metadata keluaran. Pada GA, `history` memuat maksimum populasi dan `mean_history` memuat rata-rata populasi. Pada Random Restart, `history` memuat nilai terbaik global, sedangkan `metrics.history_per_restart` menyimpan riwayat setiap pencarian. Nilai numerik tidak berhingga diserialisasi sebagai `null`; overflow faktor SA ditandai melalui `metrics.e_deltaet_overflow_history`.

Masukan tidak valid menghasilkan HTTP 400 dan jenis konten yang tidak didukung menghasilkan HTTP 415. Kesalahan penyimpanan tidak membatalkan hasil pencarian yang sudah berhasil; rincian tersedia melalui field `output` dan log server.

## Struktur Program

| Direktori atau berkas | Keterangan |
|---|---|
| `src/core/` | Representasi persoalan, batasan, fungsi objektif, dan pembentukan neighbor. |
| `src/algorithms/` | Implementasi algoritma local search. |
| `src/services/` | Validasi konfigurasi, pelaksanaan optimasi, penyusunan hasil, dan penyimpanan keluaran. |
| `src/app.py` | Server Flask dan endpoint API. |
| `frontend/` | Antarmuka dan visualisasi menggunakan HTML, CSS, dan JavaScript. |
| `data/sample/` | Dataset contoh yang dapat dimuat melalui aplikasi. |
| `output/` | Hasil eksperimen dalam format JSON dan PNG. |
| `tests/` | Pengujian representasi persoalan, algoritma, layanan, dan antarmuka. |
| `docs/` | Direktori untuk laporan tugas besar dalam format PDF. |

## Pengujian Program

Jalankan pengujian Python dan pengolahan data grafik frontend melalui perintah berikut.

```bash
python -m pytest -q
node --test tests/frontend/results.test.mjs
```

Pengujian peramban membutuhkan Node.js 22 atau versi yang lebih baru, Playwright, Chromium, dan aplikasi yang sedang berjalan. Contoh persiapan adalah sebagai berikut.

```bash
npm install --prefix /tmp/if3070-browser-check --no-package-lock playwright
PLAYWRIGHT_MODULE=/tmp/if3070-browser-check/node_modules/playwright/index.mjs CHROMIUM_PATH=/usr/bin/chromium-browser APP_URL=http://127.0.0.1:5000 node tests/frontend/browser-smoke.mjs
```

Lokasi Chromium perlu disesuaikan dengan lingkungan yang digunakan. Pengujian peramban mencakup keenam algoritma, validasi masukan, pengaturan seed, penyajian hasil, unduhan, dan tampilan pada layar kecil.

Pemeriksaan manual dapat dilakukan dengan menjalankan setiap algoritma, membandingkan hasil antarmuka dengan JSON dan PNG yang tersimpan, serta mengulang konfigurasi menggunakan seed yang sama. Periksa juga masukan tidak valid, GA nol generasi, SA nol iterasi, batas sideways dan restart nol, dataset multi-kapal, serta tampilan pada layar kecil. Pada GA nol generasi, state awal dan akhir harus sama. Pada SA nol iterasi, temperatur awal tetap ditampilkan tanpa membentuk probabilitas kandidat buatan.

## Pembagian Tugas

| Nama | NIM | Tanggung jawab |
|---|---|---|
| Abel Gani | 18224016 | Implementasi algoritma *Simulated Annealing* dan *Genetic Algorithm*. |
| Kayta Rechia Mazaya | 18224022 | Implementasi seluruh varian *Hill Climbing* termasuk yang tercantum pada spesifikasi bonus. |
| R. Athalla Ananda Putra | 18224060 | Perancangan arsitektur program, implementasi representasi persoalan (*core*), fungsi objektif utama dan bonus, validasi konfigurasi, serta integrasi sistem. |
