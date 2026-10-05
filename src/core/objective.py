"""Cerita soal nilai solusi, alias seberapa bagus satu State.

objective_1 itu yang utama, kita kejar total ShippingFee sebesar mungkin.
objective_2 itu cadangan buat bonus, dikerjakan santai setelah yang wajib beres.

Cara pakainya sama, tinggal panggil fungsinya dengan satu State,
nanti keluar angkanya. Algoritma tinggal terima fungsinya sebagai parameter.
"""

from .state import State


def objective_1(state: State):
    """Hitung total ShippingFee dari kendaraan yang berhasil diangkut. Makin besar makin bagus."""
    # TODO Tahap 1 Anggota 1, jumlahkan shipping_fee dari placement yang valid ya
    raise NotImplementedError


def objective_2(state: State):
    """Objective cadangan buat bonus. Ingat ya, jangan nambah variabel di luar spek."""
    # TODO Tahap Bonus Anggota 3, definisikan setelah yang wajib stabil dulu
    raise NotImplementedError


OBJECTIVES = {
    "objective_1": objective_1,
    "objective_2": objective_2,
}
