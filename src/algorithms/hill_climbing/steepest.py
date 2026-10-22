
from time import perf_counter

from ._common import build_result, validate_limit


def steepest_ascent(initial_state, objective_function, neighbor_generator, parameters=None):
    parameters = {} if parameters is None else parameters
    max_iterations = validate_limit(parameters, "max_iterations", 1000)

    started = perf_counter()
    initial_snapshot = initial_state.copy()
    current = initial_snapshot.copy()
    current_value = objective_function(current)
    history = [current_value]
    iterations = 0

    while iterations < max_iterations:
        best_neighbor = None
        best_neighbor_value = current_value
        for neighbor in neighbor_generator(current):
            value = objective_function(neighbor)
            if value > best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = value

        iterations += 1
        if best_neighbor is not None:
            current = best_neighbor
            current_value = best_neighbor_value
        history.append(current_value)
        if best_neighbor is None:
            break

    return build_result(initial_snapshot, current, current_value, history,
                        iterations, perf_counter() - started)
