import math
import random
import time
from src.core.constraint import is_valid

def sample_neighbor(state, current_value, objective_function, neighbor_generator, rng):
    selected = None # state from neighbor_generator
    selected_value = None # objective value of selected
    count = 0
    has_improvement = False

    for candidate in neighbor_generator(state):
        value = objective_function(candidate)
        has_improvement = has_improvement or value > current_value # if any neighbor is better than current
        count += 1

        if rng.randrange(count) == 0:
            selected = candidate.copy() # value is copied to avoid mutation of the original candidate
            selected_value = value

    return selected, selected_value, has_improvement

def simulated_annealing(initial_state, objective_function, neighbor_generator, parameters = None):
    started = time.perf_counter() # function to measure the length of time taken
    p = parameters or {} # filled with default values if parameters is None

    temperature = float(p.get("initial_temperature", 1000.0)) # start at T = 1000
    cooling_rate = float(p.get("cooling_rate", 0.95)) # T = T * 0.95 each iteration
    min_temperature = float(p.get("min_temperature", 0.001)) # stop if T < 0.001
    max_iterations = p.get("max_iterations", 1000) # maximum of 1000 iterations
    rng = random.Random(p.get("seed")) # random number generator for reproducability

    if not math.isfinite(temperature) or temperature <= 0 or min_temperature <= 0:
        raise ValueError("Temperatur harus lebih besar dari 0")
    if not math.isfinite(cooling_rate) or cooling_rate <= 0 or cooling_rate >= 1:
        raise ValueError("cooling_rate harus berada di antara 0 dan 1")
    if not math.isfinite(min_temperature) or min_temperature <= 0:
        raise ValueError("min_temperature harus lebih besar dari 0")
    if type(max_iterations) is not int or max_iterations < 0:
        raise ValueError("max_iterations harus integer non-negatif")
    if not is_valid(initial_state):
        raise ValueError("initial_state tidak valid pada state ini")

    current = initial_state.copy()
    current_value = objective_function(current)
    best = current.copy()
    best_value = current_value

    history = [current_value]
    best_history = [best_value]
    temperature_history = [temperature]
    e_deltaet_history = []
    log_e_deltaet_history = []

    iterations = 0
    stuck_count = 0
    accept_worse = 0

    for iteration in range(max_iterations):
        if temperature <= min_temperature:
            break # stop if temperature is under threshold

        candidate, candidate_value, has_improvement = sample_neighbor(current, current_value, objective_function, neighbor_generator, rng)

        if not has_improvement:
            stuck_count += 1

        if candidate is None:
            break

        delta = candidate_value - current_value # delta E
        exponent = delta / temperature # delta E / T

        try:
            e_deltaet = math.exp(exponent) # e^(delta E / T)
        except OverflowError:
            e_deltaet = float("inf") if exponent > 0 else 0.0

        e_deltaet_history.append(e_deltaet)
        log_e_deltaet_history.append(exponent)

        accepted = (delta >= 0 or rng.random() < e_deltaet)

        if accepted: # fulfilling rules either better value or worse value with probability
            if delta < 0:
                accept_worse += 1
            current = candidate
            current_value = candidate_value

            if current_value > best_value:
                best = current.copy()
                best_value = current_value

        iterations += 1
        temperature *= cooling_rate
        history.append(current_value)
        best_history.append(best_value)
        temperature_history.append(temperature)

    return {
        "initial_state": initial_state.copy(),
        "best_state": best.copy(),
        "best_value": best_value,
        "final_state": best.copy(),
        "final_value": best_value,
        "terminal_state": current.copy(),
        "terminal_value": current_value,
        "history": history,
        "best_history": best_history,
        "temperature_history": temperature_history,
        "e_deltaet_history": e_deltaet_history,
        "log_e_deltaet_history": log_e_deltaet_history,
        "iterations": iterations,
        "duration": time.perf_counter() - started,
        "stuck_count": stuck_count,
        "accept_worse": accept_worse,
    }
