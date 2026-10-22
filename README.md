# Optimasi Muatan Kapal

Program mencari penempatan kendaraan pada geladak kapal untuk memaksimalkan total ShippingFee atau objective bonus efisiensi pendapatan–waktu–berat. Solusi harus memenuhi batas geladak, larangan tumpang tindih, dan kapasitas berat kapal.

Antarmuka menyediakan enam pilihan algoritma:

- Steepest Ascent Hill Climbing.
- Stochastic Hill Climbing.
- Hill Climbing with Sideways Move.
- Random Restart Hill Climbing.
- Simulated Annealing.
- Genetic Algorithm.

Setiap pencarian menghasilkan initial state, solusi terbaik, statistik, serta grafik objective.

## Menjalankan aplikasi

Gunakan Python 3.10 atau versi lebih baru. Jalankan perintah dari direktori repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.app
```

Buka **http://127.0.0.1:5000/** melalui browser.

## Penggunaan

1. Gunakan data sampel atau unggah JSON kapal dan kendaraan. Dataset juga bisa diedit langsung.
2. Pilih algoritma, objective, mode seed **Acak** atau **Manual**, dan parameter pencarian.
3. Klik **Jalankan optimasi**.
4. Periksa initial state, solusi terbaik, nilai objective, jumlah langkah, durasi, dan statistik algoritma.
5. Hasil JSON dan grafik PNG otomatis disimpan ke `output/`. Lokasi JSON ditampilkan pada hasil pencarian. Hasil JSON, grafik PNG, atau visualisasi state SVG juga dapat diunduh melalui browser.

Mode **Acak** adalah default. Setiap eksekusi meminta seed initial state dan seed algoritma baru dari backend. Mode **Manual** menampilkan input seed untuk mengulang run tertentu atau menentukan seed pengulangan secara terkontrol. Nilai manual dipertahankan ketika berganti mode. Seed aktual selalu dicatat pada `configuration.seed` dan `configuration.algorithm_seed` dalam unduhan JSON.

Seed initial state mengatur pembentukan penempatan awal atau populasi awal. Seed algoritma mengatur keputusan acak Stochastic HC, Sideways Move, SA, dan GA; input manual ini dinonaktifkan untuk Steepest Ascent dan Random Restart. Seed yang sama dengan data, parameter, kode, dan lingkungan yang sama dapat mereproduksi hasil; durasi bisa berbeda. Seed berbeda tidak menjamin objective akhir berbeda.

Untuk tiga pengulangan laporan, gunakan misalnya seed initial state `42`, `43`, `44` dan seed algoritma `142`, `143`, `144`, dengan dataset serta parameter tetap. Gunakan daftar seed pengulangan yang sama pada konfigurasi/algoritma yang dibandingkan. Pada GA, seed initial state mengatur populasi awal, bukan satu state yang identik dengan HC/SA.

Sideways Move menerima parameter **Maksimum sideways move** dan menampilkan jumlah perpindahan setara yang dilakukan. Batas nol tetap mengizinkan perpindahan yang meningkatkan objective. Penghitungan sideways move bersifat kumulatif selama pencarian.

Random Restart menerima **Maksimum iterasi per pencarian** dan **Maksimum restart**. Restart dihitung setelah pencarian awal: maksimum restart 2 menghasilkan 3 pencarian. Seed pencarian adalah seed initial state ditambah indeks pencarian, mulai nol. Hasil menampilkan seed, jumlah iterasi, objective awal/akhir, dan grafik setiap pencarian. Grafik utama menampilkan objective terbaik seluruh pencarian terhadap total iterasi.

Pada GA, visualisasi awal adalah individu terbaik populasi awal. Grafik menampilkan maksimum dan rata-rata populasi serta nilai terbaik sepanjang pencarian. Solusi terbaik dapat berbeda dari individu terbaik generasi terakhir jika elitisme dinonaktifkan.

Pada SA, panel analisis menampilkan grafik probabilitas penerimaan `min(1, exp(ΔE/T))` berwarna merah dan temperatur setelah iterasi berwarna oranye. Keduanya dapat diunduh dalam satu PNG. Bagian **Grafik tambahan** menyediakan eksponen dan faktor eksponensial mentah untuk analisis lebih lanjut.

## Penyimpanan hasil otomatis

Setiap request optimasi yang berhasil melalui aplikasi atau `POST /api/optimize` menyimpan:

```text
output/
├── results/
│   └── <run-id>.json
└── plots/
    ├── <run-id>-objective.png
    ├── <run-id>-sa-analysis.png       # khusus SA
    └── <run-id>-restart-<n>.png       # khusus Random Restart
```

`run-id` memuat waktu UTC, ID algoritma, dan ID acak agar run berulang memiliki file berbeda. Indeks restart 0 adalah pencarian awal. Folder dibuat otomatis relatif terhadap root repository, bukan direktori terminal saat program dijalankan.

JSON menyimpan hasil lengkap yang sama dengan respons API: state awal/terbaik, statistik, history, konfigurasi, seed aktual, serta metadata `output` berisi lokasi file. Grafik objective GA mencakup maksimum dan rata-rata populasi serta best-so-far. SA menambahkan satu PNG berisi probabilitas penerimaan dan temperatur; Random Restart menambahkan grafik setiap pencarian.

Grafik dibuat di backend menggunakan Matplotlib tanpa GUI. Perbarui dependensi dengan `python -m pip install -r requirements.txt` jika memakai virtual environment lama. Waktu penyimpanan/pembuatan grafik tidak masuk ke durasi pencarian. Pemanggilan langsung `run_optimization()` hanya menghitung hasil; penyimpanan otomatis diintegrasikan pada endpoint API.

Jika penyimpanan gagal, hasil optimasi tetap ditampilkan dan dapat diunduh, disertai pesan kegagalan. Detail kesalahan tersedia pada log server.

Isi `output/results/` dan `output/plots/` diabaikan Git. Untuk menyertakan hasil eksperimen terpilih pada pengumpulan, gunakan `git add -f` dengan path file yang dipilih, misalnya `git add -f output/results/<run-id>.json output/plots/<run-id>-objective.png`.

## Objective bonus

Pilihan **Efisiensi Pendapatan, Waktu, dan Berat** (`objective_2`) memakai skor per kapal:

```text
total ShippingFee / ((1 + ETA terlama) × (1 + total berat / kapasitas kapal))
```

Skor seluruh kapal dijumlahkan. Kapal kosong mendapat skor nol. ETA adalah estimasi waktu kedatangan, bukan deadline; ETA terlama dipakai sebagai pendekatan waktu penyelesaian pengiriman kapal. Objective ini merupakan heuristik rancangan untuk menyeimbangkan pendapatan, waktu, dan penggunaan kapasitas berat, bukan laba bersih atau pendapatan per hari aktual.

Seluruh algoritma dapat memakai kedua objective. Nilai pada state, grafik, dan unduhan JSON mengikuti pilihan objective. Total ShippingFee aktual tetap ditampilkan terpisah dalam statistik, bersama ETA terlama dan berat muatan per kapal. Penjelasan rumus, asumsi, contoh, serta kasus nol ada di [dokumentasi objective](docs/objective.md).

## Struktur

| Direktori | Isi |
|---|---|
| `src/core/` | Representasi masalah, objective, constraint, dan neighbor. |
| `src/algorithms/` | Implementasi algoritma local search. |
| `src/services/` | Validasi konfigurasi, eksekusi optimasi, dan serialisasi hasil. |
| `src/app.py` | Server Flask dan API optimasi. |
| `frontend/` | HTML, CSS, dan JavaScript tanpa proses build. |
| `data/sample/` | Dataset contoh. |
| `output/` | Hasil JSON dan grafik PNG yang disimpan otomatis per run. |
| `tests/` | Pengujian core, algoritma, service, dan frontend. |
| `docs/` | Dokumentasi teknis dan panduan pengujian. |

Seluruh varian HC dan `src/core/neighbor.py` mengikuti `origin/feature/hc-chia-fix` pada commit `6e74807`, yang mencakup pembaruan core `062caa8`. SA dan GA mengikuti `origin/feature/metaheuristic` pada commit `6b13b2f`. Integrasi web berada di service dan frontend. Pembaruan urutan neighbor dapat menghasilkan history berbeda dari versi core lama, meskipun seed sama.

## Pengujian

```bash
python -m pytest -q
node --test tests/frontend/results.test.mjs
```

Pengujian browser membutuhkan Node.js 22+, Playwright, Chromium, dan aplikasi yang sudah berjalan:

```bash
npm install --prefix /tmp/if3070-browser-check --no-package-lock playwright
PLAYWRIGHT_MODULE=/tmp/if3070-browser-check/node_modules/playwright/index.mjs CHROMIUM_PATH=/usr/bin/chromium-browser APP_URL=http://127.0.0.1:5000 node tests/frontend/browser-smoke.mjs
```

Sesuaikan lokasi Chromium pada komputer yang digunakan. Pengujian browser menjalankan keenam pilihan algoritma dengan parameter kecil, memeriksa hasil per pencarian, batas nol, ekspor, validasi, dan layout mobile.

## Pembagian tugas

- Anggota 1: problem core dan Hill Climbing.
- Anggota 2: Simulated Annealing dan Genetic Algorithm.
- Anggota 3: service, API, integrasi algoritma, dan frontend.

Dokumentasi: [arsitektur](docs/architecture.md), [API](docs/api.md), [algoritma](docs/algorithm.md), dan [pengujian manual](docs/manual-testing.md).
