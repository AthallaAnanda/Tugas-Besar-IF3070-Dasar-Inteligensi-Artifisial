"""Experiment Service, si tukang lembur.

Kalau optimization itu sekali jalan, yang ini jalannya berkali kali
buat kebutuhan eksperimen. Dia yang atur pengulangan, atur parameter,
kumpulkan hasil, hitung metrik, simpan, dan siapkan data buat grafik.

Buat non GA kita ulang 3 kali. Buat GA ada Skenario A dan B,
tiap config diulang 3 kali juga.
"""

from .optimization import run_optimization


def run_experiment(config):
    """Jalankan eksperimen sesuai file src/experiments/config.py."""
    # TODO Tahap 3 Anggota 3
    raise NotImplementedError
