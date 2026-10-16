"""Steepest Ascent Hill Climbing untuk memaksimalkan nilai state."""

from time import perf_counter


def steepest_ascent(initial_state, objective_function, neighbor_generator, parameters=None):
    """Pilih neighbor terbaik selama nilainya meningkat."""
    parameters = {} if parameters is None else parameters
    max_iterations = parameters.get("max_iterations", 1000)
    if type(max_iterations) is not int or max_iterations <= 0:
        raise ValueError("max_iterations harus bilangan bulat positif")

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

    return {
        "initial_state": initial_snapshot,
        "final_state": current,
        "best_state": current,
        "best_value": current_value,
        "history": history,
        "iterations": iterations,
        "duration": perf_counter() - started,
    }
