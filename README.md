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
- Result isinya best_state, best_value, history, iterations, duration.
