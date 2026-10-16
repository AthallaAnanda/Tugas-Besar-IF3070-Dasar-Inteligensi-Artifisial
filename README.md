# Tugas Besar 1 IF3070 - Local Search untuk Optimasi Penempatan Kendaraan pada Kapal

## Struktur Proyek

```text
src/          # Flask API plus core plus algorithms plus services plus experiments
frontend/     # HTML plus CSS plus Vanilla JS
data/         # input dan sample
output/       # results dan plots
tests/        # core, algorithms, services
docs/         # architecture, api, algorithm, experiment
```

## Quickstart Stage 0

```bash
pip install -r requirements.txt
python -m src.app
# Buka http://localhost:5000/api/health di browser.
# Harusnya jawab status success dengan pesan Backend Connected.
```

Buka `frontend/index.html` di browser untuk GUI dasar.

Contoh data: `data/sample/small.json`. Struktur State dan cara memakai
problem core dijelaskan di `docs/architecture.md`.

## Kontrak Antarmuka

- State dipakai bareng sama semua algoritma, tidak bikin sendiri sendiri.
- Fungsi objective dipanggil dengan satu State, keluarnya angka nilai.
- Pembikin neighbor dipanggil dengan satu State, keluarnya daftar tetangga.
- Steepest Ascent menerima State awal, fungsi objective, generator neighbor,
  dan parameter `max_iterations` (bawaan 1000).
- Result Steepest Ascent berisi initial_state, final_state, best_state,
  best_value, history, iterations, duration. State dalam result masih objek
  Python; gunakan `State.to_dict()` saat menyajikannya sebagai JSON.

## Pembagian Tugas

- Anggota 1: problem core dan Hill Climbing.
- Anggota 2: Simulated Annealing dan Genetic Algorithm.
- Anggota 3: layanan optimasi, eksperimen, API, dan frontend.

Steepest Ascent dan Simulated Annealing sudah tersedia di branch integrasi
`develop`. Cara pemakaian dan hasil keduanya dijelaskan di `docs/algorithm.md`.
Varian Hill Climbing lain merupakan bonus setelah seluruh bagian wajib proyek
selesai dan teruji. Endpoint optimasi dan eksperimen serta Genetic Algorithm
masih menunggu implementasi anggota terkait.
