# Pengujian Manual

Jalankan `python -m src.app`, lalu buka `http://127.0.0.1:5000/`.

## Konfigurasi

1. Gunakan data sampel. Periksa dataset yang dimuat melalui bagian Edit dataset.
2. Unggah dataset JSON atau edit dataset langsung. Data tersebut harus digunakan saat optimasi dijalankan.
3. Ganti algoritma. Parameter harus sesuai dan nilai yang sudah diisi dipertahankan ketika kembali ke algoritma sebelumnya.
   Dropdown memuat empat varian HC, SA, dan GA. Pada mode seed Manual, seed algoritma aktif pada Stochastic, Sideways, SA, dan GA.
4. Uji JSON tidak valid, batas iterasi negatif, populasi kurang dari dua, elite yang sama dengan populasi, dan mutation rate di luar 0 sampai 1. Pesan kesalahan harus terlihat dan form kembali dapat digunakan.

## Seed

1. Saat halaman dibuka, pilihan seed adalah Acak dan input seed manual disembunyikan.
2. Jalankan pencarian dua kali, lalu unduh JSON setiap hasil. Request Acak mengirim kedua seed sebagai `null`; respons mencatat seed aktual baru pada setiap run. Objective akhir tetap boleh sama.
3. Pilih Manual, masukkan seed dari salah satu hasil tersebut, lalu gunakan dataset/parameter yang sama. Initial State, Final State, dan history dapat direproduksi.
4. Isi seed manual, ganti ke Acak lalu kembali ke Manual. Nilai manual tetap tersimpan. Seed 0 adalah nilai manual yang valid.
5. Kosongkan input manual, lalu pilih Acak. Form tetap dapat dijalankan karena field manual tidak dipakai pada mode ini.

## Hasil pencarian

1. Jalankan HC dengan maksimum dua iterasi. Periksa initial state, solusi terbaik, objective, durasi, dan grafik.
2. Jalankan SA dengan maksimum tiga iterasi. Periksa statistik stuck/accept-worse, grafik probabilitas penerimaan merah (0–1), dan grafik temperatur oranye yang tampil bersamaan. Buka **Grafik tambahan** untuk temperatur, ΔE/T, dan faktor eksponensial mentah.
3. Jalankan GA dengan populasi empat dan tiga generasi. Grafik memuat maksimum, rata-rata, dan terbaik sepanjang pencarian; visualisasi awal berlabel individu terbaik populasi awal.
4. Jalankan GA dengan nol generasi. Hasil awal dan akhir sama; grafik tetap menampilkan satu titik.
5. Periksa parameter dan seed dalam unduhan JSON. Ulangi dengan konfigurasi yang sama; solusi/history harus konsisten meskipun durasi berbeda.

## Varian Hill Climbing

1. Jalankan Stochastic HC dengan lima iterasi. Percobaan yang tidak membaik tidak otomatis menghentikan pencarian; hasil tetap reproducible dengan kedua seed yang sama.
2. Jalankan Sideways dengan maksimum empat iterasi dan batas satu sideways move. Jumlah sideways move pada statistik tidak boleh melebihi satu. Ubah batas menjadi nol; perbaikan strict tetap diperbolehkan.
3. Pilih seed Manual 42, lalu jalankan Random Restart dengan dua iterasi per pencarian dan maksimum dua restart. Hasil memuat tiga pencarian, dengan seed awal 42/43/44. Total iterasi adalah jumlah iterasi dalam tabel.
4. Pilih setiap pencarian pada dropdown grafik. Grafik lokal dimulai dari objective awal baris tersebut, sedangkan grafik utama menunjukkan best-so-far seluruh pencarian.
5. Ubah maksimum restart menjadi nol. Tabel memuat tepat satu pencarian awal dan jumlah restart nol. Uji juga batas negatif atau pecahan; request harus ditolak.
6. Ganti kembali ke SA atau GA. Tabel dan grafik Random Restart disembunyikan, sedangkan parameter yang sebelumnya diisi dipertahankan.

## Unduhan dan tampilan

1. Unduh JSON. Periksa konfigurasi, initial state, solusi terbaik, history, dan statistik.
2. Unduh grafik objective dan diagnostik sebagai PNG. Tombol utama pada analisis SA menghasilkan satu PNG berisi grafik probabilitas dan temperatur. Uji SA nol iterasi: temperatur awal tersedia dan probabilitas menjelaskan bahwa belum ada kandidat yang dievaluasi.
3. Unduh state sebagai SVG dan buka berkasnya.
4. Periksa desktop dan layar 390 px. Label, form, statistik, serta visualisasi tetap terbaca tanpa membuat halaman melebar.

## Penyimpanan otomatis

1. Jalankan optimasi dan periksa pesan **Tersimpan otomatis** beserta path JSON pada halaman hasil. Buka JSON di `output/results/` dan grafik objective di `output/plots/`; konfigurasi, seed, history, serta statistik harus sama dengan unduhan browser.
2. Ulangi konfigurasi dan seed yang sama. Nama file harus berbeda dan hasil run sebelumnya tetap tersedia.
3. Jalankan SA, termasuk nol iterasi. PNG `-sa-analysis.png` berisi probabilitas penerimaan dan temperatur; saat nol iterasi, tidak ada probabilitas buatan. Jalankan GA nol generasi dan periksa grafik satu titik.
4. Jalankan Random Restart dengan maksimum dua restart. Tersimpan satu grafik objective global dan tiga grafik `-restart-0.png` sampai `-restart-2.png`.
5. Kirim input tidak valid. Tidak ada file hasil baru. Pada lingkungan uji dengan folder output tidak bisa ditulis, hasil optimasi tetap tampil dan bisa diunduh, pesan kegagalan penyimpanan terlihat, dan log server mencatat detailnya.
