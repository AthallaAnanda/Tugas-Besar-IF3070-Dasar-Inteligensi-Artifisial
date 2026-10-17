"""Stochastic Hill Climbing mencoba satu neighbor acak per iterasi."""

import random
from time import perf_counter

from ...core.neighbor import NoNeighborError, generate_neighbors, random_neighbor
from ._common import build_result, validate_limit


def stochastic_hill_climbing(initial_state, objective_function, neighbor_generator, parameters=None):
    """Coba satu neighbor acak per iterasi dan pindah hanya jika nilainya naik."""
    parameters = {} if parameters is None else parameters
    max_iterations = validate_limit(parameters, "max_iterations", 1000)
    rng = random.Random(parameters.get("seed"))

    started = perf_counter()
    initial_snapshot = initial_state.copy()
    current = initial_snapshot.copy()
    current_value = objective_function(current)
    history = [current_value]
    iterations = 0

    while iterations < max_iterations:
        neighbor = None
        if neighbor_generator is generate_neighbors or neighbor_generator is random_neighbor:
            try:
                neighbor = random_neighbor(current, rng)
            except NoNeighborError:
                pass
        else:
            # Tetap mendukung iterable neighbor khusus dari pemanggil lain.
            for count, candidate in enumerate(neighbor_generator(current), start=1):
                if rng.randrange(count) == 0:
                    neighbor = candidate

        iterations += 1
        if neighbor is None:
            history.append(current_value)
            break

        neighbor_value = objective_function(neighbor)
        if neighbor_value > current_value:
            current = neighbor
            current_value = neighbor_value
        history.append(current_value)

    return build_result(initial_snapshot, current, current_value, history,
                        iterations, perf_counter() - started)
