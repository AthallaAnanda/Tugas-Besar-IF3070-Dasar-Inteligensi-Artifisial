
import random
from time import perf_counter

from ._common import build_result, validate_limit


def sideways_move(initial_state, objective_function, neighbor_generator, parameters=None):
    parameters = {} if parameters is None else parameters
    max_iterations = validate_limit(parameters, "max_iterations", 1000)
    maximum_sideways_move = validate_limit(
        parameters, "maximum_sideways_move", 100, minimum=0
    )
    rng = random.Random(parameters.get("seed"))

    started = perf_counter()
    initial_snapshot = initial_state.copy()
    current = initial_snapshot.copy()
    current_value = objective_function(current)
    history = [current_value]
    iterations = 0
    sideways_moves = 0

    while iterations < max_iterations:
        improving = []
        equal = []
        for neighbor in neighbor_generator(current):
            value = objective_function(neighbor)
            if value > current_value:
                improving.append((value, neighbor))
            elif value == current_value:
                equal.append(neighbor)

        iterations += 1
        if improving:
            current_value, current = max(improving, key=lambda item: item[0])
        elif equal and sideways_moves < maximum_sideways_move:
            current = rng.choice(equal)
            sideways_moves += 1
        else:
            history.append(current_value)
            break

        history.append(current_value)
        if sideways_moves == maximum_sideways_move and maximum_sideways_move > 0:
            break

    return build_result(
        initial_snapshot, current, current_value, history, iterations,
        perf_counter() - started, sideways_moves=sideways_moves,
        maximum_sideways_move=maximum_sideways_move,
    )
