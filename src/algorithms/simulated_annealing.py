import math
import random
import time

from src.core.constraint import is_valid


def sample_neighbor(
    state,
    current_value,
    objective_function,
    neighbor_generator,
    rng,
):
    selected = None
    selected_value = None
    count = 0
    has_improvement = False

    for candidate in neighbor_generator(state):
        value = objective_function(candidate)
        has_improvement = has_improvement or value > current_value
        count += 1

        if rng.randrange(count) == 0:
            selected = candidate.copy()
            selected_value = value

    return selected, selected_value, has_improvement


def simulated_annealing(
    initial_state,
    objective_function,
    neighbor_generator,
    parameters=None,
    on_step=None, # callback untuk ngerekam kondisi setiap langkah
):
    started = time.perf_counter()
    parameters = {} if parameters is None else parameters

    temperature = float(parameters.get("initial_temperature", 1000.0))
    cooling_rate = float(parameters.get("cooling_rate", 0.95))
    min_temperature = float(parameters.get("min_temperature", 0.001))
    max_iterations = parameters.get("max_iterations", 1000)
    rng = random.Random(parameters.get("seed"))

    # validasi temperatur awal, cooling rate, temperatur minimum
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("Temperatur awal harus positif dan terbatas")

    if not math.isfinite(cooling_rate) or not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate harus berada di antara 0 dan 1")

    if not math.isfinite(min_temperature) or min_temperature <= 0:
        raise ValueError("min_temperature harus positif dan terbatas")

    if type(max_iterations) is not int or max_iterations < 0:
        raise ValueError("max_iterations harus bilangan bulat tidak negatif")

    if not is_valid(initial_state):
        raise ValueError("initial_state tidak valid")

    initial_snapshot = initial_state.copy() # nyimpen snapshot dari state awal biar bisa dilacak dan dicek
    current = initial_snapshot.copy()
    current_value = objective_function(current)
    best = current.copy()
    best_value = current_value

    history = [current_value]
    best_history = [best_value]
    temperature_history = [temperature]

    iterations = 0
    stuck_count = 0
    accept_worse = 0
    stop_reason = "max_iterations" # alasan berhenti default (karena mencapai batas iterasi), fungsinya untuk nyertain alasan berhenti dalam hasil akhir

    # ngerekam state awal sama temperatur awal sebelum iterasi dimulai biar bisa dilacak dari awal
    if on_step is not None:
        on_step(
            current,
            0,
            current_value,
            best_value,
            decision="initial",
            temperature=temperature,
            next_temperature=temperature,
        )

    for _ in range(max_iterations):
        if temperature <= min_temperature:
            stop_reason = "min_temperature" # alasan berhenti karena temperatur udah di bawah batas minimum, fungsinya untuk nyertain alasan berhenti dalam hasil akhir
            break

        candidate, candidate_value, has_improvement = sample_neighbor(
            current,
            current_value,
            objective_function,
            neighbor_generator,
            rng,
        )

        if not has_improvement:
            stuck_count += 1

        if candidate is None:
            stop_reason = "no_neighbors" # alasan berhenti karena ga ada neighbor yang valid, fungsinya untuk nyertain alasan berhenti dalam hasil akhir
            break

        used_temperature = temperature # nyimpen temperatur yang dipake buat nentuin probabilitas penerimaan solusi yang lebih buruk, dan yap biar bisa dilacak dan dicek
        delta = candidate_value - current_value
        accepted = delta >= 0 or rng.random() < math.exp(
            delta / used_temperature
        )

        # ngecatet apakah pencarian berpindah ke solusi yang lebih baik, solusi yang sama, solusi yang lebih buruk, atau ditolak (cuma jadi metadata)
        if accepted:
            if delta < 0:
                accept_worse += 1
                decision = "accepted_worse"
            elif delta > 0:
                decision = "improved"
            else:
                decision = "accepted_equal"

            current = candidate
            current_value = candidate_value

            if current_value > best_value:
                best = current.copy()
                best_value = current_value
        else:
            decision = "rejected"

        iterations += 1
        temperature *= cooling_rate

        history.append(current_value)
        best_history.append(best_value)
        temperature_history.append(temperature)

        # ngerekam kondisi setiap langkah iterasi biar bisa dilacak dan dicek, termasuk state saat ini, nilai objektif saat ini, nilai objektif terbaik, keputusan yang diambil, nilai kandidat, apakah diterima atau ditolak, temperatur yang dipake buat nentuin probabilitas penerimaan solusi yang lebih buruk, dan temperatur berikutnya
        if on_step is not None:
            on_step(
                current,
                iterations,
                current_value,
                best_value,
                decision=decision,
                candidate_value=candidate_value,
                accepted=accepted,
                temperature=used_temperature,
                next_temperature=temperature,
            )

    return {
        "initial_state": initial_snapshot, # pake snapshot yang dibuat sebelumnya biar bisa dilacak dan dicek
        "best_state": best.copy(),
        "best_value": best_value,
        "final_state": best.copy(),
        "final_value": best_value,
        "terminal_state": current.copy(),
        "terminal_value": current_value,
        "history": history,
        "best_history": best_history,
        "temperature_history": temperature_history,
        "iterations": iterations,
        "duration": time.perf_counter() - started,
        "stuck_count": stuck_count,
        "accept_worse": accept_worse,
        "stop_reason": stop_reason, # nyertain alasan berhenti dalam hasil akhir biar bisa dilacak dan dicek
    }