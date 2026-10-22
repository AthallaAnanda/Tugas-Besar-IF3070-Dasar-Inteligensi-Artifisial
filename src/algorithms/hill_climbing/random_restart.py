
from time import perf_counter

from ._common import build_result, validate_limit
from .steepest import steepest_ascent


def random_restart(initial_state_fn, objective_function, neighbor_generator, parameters=None):
    parameters = {} if parameters is None else parameters
    maximum_restart = validate_limit(parameters, "maximum_restart", 10, minimum=0)
    max_iterations = validate_limit(parameters, "max_iterations", 1000)
    if not callable(initial_state_fn):
        raise ValueError("initial_state_fn harus berupa fungsi")

    started = perf_counter()
    first_state = initial_state_fn()
    initial_snapshot = first_state.copy()
    best_state = None
    best_value = None
    history = []
    history_per_restart = []
    iterations_per_restart = []
    total_iterations = 0

    for run_index in range(maximum_restart + 1):
        start_state = first_state if run_index == 0 else initial_state_fn()
        result = steepest_ascent(
            start_state, objective_function, neighbor_generator,
            {"max_iterations": max_iterations},
        )
        iterations_per_restart.append(result["iterations"])
        history_per_restart.append(result["history"])
        total_iterations += result["iterations"]

        if best_value is None or result["best_value"] > best_value:
            best_state = result["best_state"]
            best_value = result["best_value"]

        if not history:
            history.append(objective_function(initial_snapshot))
        history.extend(max(history[-1], value) for value in result["history"][1:])

    return build_result(
        initial_snapshot, best_state, best_value, history, total_iterations,
        perf_counter() - started, restarts=len(iterations_per_restart) - 1,
        iterations_per_restart=iterations_per_restart,
        history_per_restart=history_per_restart,
    )
