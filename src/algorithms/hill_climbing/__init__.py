"""Kumpulan varian Hill Climbing kita.

Isinya ada steepest, stochastic, sideways, sama random restart.
Kalau bonus 7 poin mau diambil, keempatnya harus beres.
Pengerjaannya dipegang Anggota 1 ya.

File ini cuma pintu masuk biar importnya gampang.
"""
from .steepest import steepest_ascent
from .stochastic import stochastic_hill_climbing
from .sideways import sideways_move
from .random_restart import random_restart

__all__ = ["steepest_ascent", "stochastic_hill_climbing", "sideways_move", "random_restart"]
