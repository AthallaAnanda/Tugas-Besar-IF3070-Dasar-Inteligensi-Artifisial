from time import perf_counter


def steepest_ascent(
    initial_state,
    objective_function,
    neighbor_generator,
    parameters=None,
    on_step=None, # callback untuk ngerekam kondisi setiap langkah
):
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
    stop_reason = "max_iterations" # alasan berhenti default (karena mencapai batas iterasi), fungsinya untuk nyertain alasan berhenti dalam hasil akhir

    # Ngerekam kondisi awal sebelum iterasi dimulai biar bisa dilacak dari awal
    if on_step is not None:
        on_step(
            current,
            0,
            current_value,
            current_value,
            decision="initial",
        )

    while iterations < max_iterations:
        best_neighbor = None
        best_neighbor_value = current_value

        for neighbor in neighbor_generator(current):
            value = objective_function(neighbor)

            if value > best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = value

        iterations += 1

        # ngecatet apakah pencarian berpindah ke solusi yang lebih baik atau berhenti kalo ga ada perbaikan
        if best_neighbor is not None:
            current = best_neighbor
            current_value = best_neighbor_value
            decision = "improved"
        else:
            decision = "no_improvement"
            stop_reason = "no_improvement"

        history.append(current_value) # ngerekam state setiap iterasi ke dalam history biar bisa dilacak. kalo ga ada perbaikan, historynya tetep dicatet biar bisa dilacak

        if on_step is not None:
            on_step(
                current,
                iterations,
                current_value,
                current_value,
                decision=decision,
            )

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
        "stop_reason": stop_reason, # nyertain alasan berhenti dalam hasil akhir biar bisa dilacak dan dicek
    }