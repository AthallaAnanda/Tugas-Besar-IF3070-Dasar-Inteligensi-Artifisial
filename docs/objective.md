# Objective Function

Kedua objective memaksimalkan skor dan hanya menerima state valid: kendaraan berada di dalam geladak, tidak bertumpuk, dan tidak melebihi kapasitas berat. Implementasi berada di `src/core/objective.py`; seluruh algoritma menerima fungsi objective terpilih dari service.

## Objective utama: Total ShippingFee

`objective_1` menjumlahkan tarif seluruh kendaraan yang diangkut. Kendaraan di luar kapal tidak berkontribusi. Nilainya adalah total tarif pengiriman dalam juta rupiah.

## Objective bonus: Efisiensi Pendapatan–Waktu–Berat

Untuk kapal ke-j, hitung:

- `P_j`: jumlah ShippingFee kendaraan yang dimuat.
- `W_j`: jumlah berat kendaraan yang dimuat.
- `T_j`: ETA terbesar di antara kendaraan yang dimuat.
- `C_j`: kapasitas berat maksimum kapal.

Objective alternatif adalah:

```text
f_2(S) = jumlah skor_j untuk seluruh kapal
skor_j = P_j / ((1 + T_j) × (1 + W_j / C_j))
```

`P_j`, `W_j`, dan `T_j` adalah besaran turunan dari state, bukan atribut input baru. Tidak diperlukan perubahan format dataset. Kendaraan di luar kapal tidak memengaruhi total tarif, total berat, atau ETA maksimum.

### Asal dan interpretasi model

Rumus ini merupakan heuristik rancangan untuk proyek ini, disusun dengan bantuan AI, bukan adaptasi dari rumus baku atau paper tertentu. Pendapatan diberi penalti berdasarkan waktu penyelesaian pengiriman dan proporsi kapasitas berat yang digunakan:

- Tarif lebih tinggi menaikkan skor jika komponen lain tetap.
- ETA maksimum lebih kecil menaikkan skor jika komponen lain tetap.
- Total berat lebih kecil menaikkan skor jika komponen lain tetap.

ETA diperlakukan sebagai estimasi waktu kedatangan dari acuan keberangkatan yang sama, bukan sisa hari menuju deadline. ETA terbesar mendekati waktu selesainya pengiriman seluruh muatan dalam satu perjalanan kapal. Perhitungan di tingkat kapal dipilih karena semua kendaraan di kapal berbagi perjalanan: kendaraan baru dengan ETA besar dapat memperpanjang perjalanan, sehingga tambahan tarifnya belum tentu meningkatkan efisiensi.

Hubungan dengan perputaran kapal mengasumsikan waktu kembali sebanding dengan waktu pengiriman atau diabaikan dalam pendekatan. Model tidak menghitung rute, waktu kembali sebenarnya, bongkar-muat, biaya bahan bakar, atau pendapatan keberangkatan berikutnya. Karena itu, skor bukan laba bersih maupun pendapatan per hari aktual. Tidak ada klaim bahwa berat secara langsung menentukan durasi atau biaya perjalanan.

Normalisasi berat `W_j / C_j` menyatakan proporsi kapasitas terpakai. Skor tidak berubah ketika satuan berat dan kapasitas dikonversi bersama, misalnya dari kilogram ke ton. Pada state valid dengan kapasitas positif, faktor `1 + W_j / C_j` berada di antara 1 dan 2. Menganggap penggunaan kapasitas lebih kecil sebagai preferensi adalah keputusan pemodelan; kapasitas kosong tidak otomatis berarti pendapatan masa depan bertambah.

Konstanta `1` pada faktor ETA menggunakan skala satu hari dan membuat ETA nol tetap terdefinisi. Konstanta `1` pada faktor berat juga menjaga penyebut positif. Keduanya merupakan keputusan desain yang memengaruhi kekuatan penalti, bukan data biaya operasional. Bentuk ini harus dievaluasi melalui eksperimen, bukan diasumsikan optimal untuk semua kebutuhan bisnis.

### Kasus khusus

- Kapal tanpa muatan memberi skor `0`.
- ETA `0` memberikan faktor waktu `1`.
- Berat total `0` memberikan faktor berat `1`.
- Model kapal mengizinkan kapasitas `0`. State valid berkapasitas nol hanya dapat memuat kendaraan berberat nol; dalam kasus ini rasio penggunaan berat didefinisikan `0`.
- Tarif total `0` memberikan skor `0`.
- State tidak valid ditolak dengan `ValueError`, termasuk muatan berberat positif pada kapal berkapasitas nol.
- Pada beberapa kapal, skor setiap kapal dihitung dengan ETA dan kapasitasnya sendiri lalu dijumlahkan. Jumlah ini adalah skor gabungan armada, bukan perhitungan pendapatan armada per satu durasi global.

### Contoh

Kapasitas kapal adalah 100 unit berat:

| Solusi | Total ShippingFee | ETA terlama | Berat muatan | Skor bonus |
|---|---:|---:|---:|---:|
| A | 200 | 4 | 100 | 20 |
| B | 180 | 4 | 50 | 24 |
| C | 180 | 2 | 50 | 40 |

Objective utama memilih A, sedangkan objective bonus memilih C. B mengungguli A karena menggunakan kapasitas lebih sedikit, sementara C mengungguli B karena waktu penyelesaian pengirimannya lebih singkat.

### Integrasi dan eksperimen

- Request API menerima `"objective": "objective_2"`. Jika objective tidak diisi, default tetap `objective_1`.
- Semua varian HC, SA, dan GA memakai fungsi terpilih untuk evaluasi, pemilihan solusi, serta history.
- `initial_state.value`, `final_state.value`, `objective_value`, dan grafik menggunakan objective terpilih. `State.to_dict()` tanpa argumen tetap menggunakan objective utama; berikan fungsi sebagai `State.to_dict(objective_2)` untuk memilih bonus.
- `statistics.total_shipping_fee` tetap menyimpan pendapatan pengiriman aktual. `statistics.ships` memuat `shipping_fee`, `max_eta`, berat, dan kapasitas setiap kapal. `max_eta` bernilai `null` untuk kapal kosong.
- Label objective dan deskripsi tersedia pada `/api/capabilities` serta ditampilkan pada form. Label hasil mengikuti objective saat run dijalankan.

Bandingkan kedua objective dengan dataset, seed, dan batas pencarian yang sama. Evaluasi total ShippingFee, skor bonus, jumlah kendaraan, ETA maksimum, serta penggunaan berat per kapal. Jangan membandingkan besar angka objective utama dan bonus secara langsung karena maknanya berbeda. Pada SA, perubahan skala objective juga memengaruhi probabilitas penerimaan untuk temperatur yang sama; analisis atau penyesuaian temperatur dapat diperlukan dalam eksperimen.
