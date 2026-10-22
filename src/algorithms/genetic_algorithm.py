import math
import random
import time
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors

def genes(state):
    result = {}

    for item in state.ships:
        for placement in item.placements:
            result[placement.vehicle_id] = placement 

    return result

def crossover(parent_a, parent_b, rng):
    child = parent_a.copy()
    for item in child.ships:
        item.placements.clear()

    genes_a = genes(parent_a)
    genes_b = genes(parent_b)
    
    ships = {}
    for item in child.ships:
        ships[item.ship.id] = item 

    vehicle_ids = sorted(child.vehicles)
    rng.shuffle(vehicle_ids)

    for vehicle_id in vehicle_ids:
        if rng.random() < 0.5: 
            source = genes_a
        else:
            source = genes_b
        
        placement = source.get(vehicle_id)
        if placement is None:
            continue

        target = ships[placement.ship_id]
        target.placements.append(placement)

        if not is_valid(child):
            target.placements.pop()

    return child

def mutate(state, rng):
    selected = None
    for count, candidate in enumerate(generate_neighbors(state), start = 1):
        if rng.randrange(count) == 0:
            selected = candidate.copy()

    if selected:
        return selected
    else:
        return state.copy()

def select_parent(population, scores, tour_size, rng):
    participants = rng.sample(range(len(population)), tour_size)
    winner = max(participants, key = lambda index: scores[index])
    return population[winner]

def genetic_algorithm(initial_population, objective_function, parameters = None):
    started = time.perf_counter()
    p = parameters or {}

    population_size = p.get("population_size", 50)
    max_iterations = p.get("max_iterations", 100)
    crossover_rate = float(p.get("crossover_rate", 0.8))
    mutation_rate = float(p.get("mutation_rate", 0.2))
    elitism = p.get("elitism", 1)
    tour_size = p.get("tour_size", 2)
    rng = random.Random(p.get("seed"))

    if type(population_size) is not int or population_size < 2:
        raise ValueError("population_size minimal bernilai 2")
    if type(max_iterations) is not int or max_iterations < 0:
        raise ValueError("max_iterations harus integer non-negatif") 
    if type(elitism) is not int or not 0 <= elitism < population_size:
        raise ValueError("elitism harus integer minimal 0 dan lebih kecil dari population_size")
    if (type(tour_size) is not int or not 1 <= tour_size <= population_size):
        raise ValueError("tour_size harus integer bernilai antara 1 dan population_size")
    if any(not math.isfinite(rate) or not 0 <= rate <= 1
           for rate in (crossover_rate, mutation_rate)):
        raise ValueError("Probabilitas harus berhingga dan bernilai antara 0 dan 1")

    population = [state.copy() for state in initial_population()]
    if len(population) != population_size:
        raise ValueError("Jumlah state awal harus sama dengan population_size")
    if not all(is_valid(state) for state in population):
        raise ValueError("Semua state awal harus valid")

    reference = population[0]
    reference_ships = {} 
    for item in reference.ships:
        reference_ships[item.ship.id] = item.ship
        
    for state in population:
        ships = {}
        for item in state.ships:
            ships[item.ship.id] = item.ship
        if state.vehicles != reference.vehicles or ships != reference_ships:
            raise ValueError("Semua individu harus memakai acuan yang sama")

    scores = [objective_function(state) for state in population]
    best_index = max(range(population_size), key = lambda i: scores[i])
    best = population[best_index].copy()
    best_value = scores[best_index]
    initial_best = best.copy()

    history = [max(scores)]
    mean_history = [sum(scores) / population_size]
    best_history = [best_value]

    for iteration in range(max_iterations):
        ranked = sorted(range(population_size), key = lambda i: scores[i], reverse = True)
        next_population = [population[index].copy() for index in ranked[:elitism]]

        while len(next_population) < population_size: 
            parent_a = select_parent(population, scores, tour_size, rng)
            parent_b = select_parent(population, scores, tour_size, rng)

            if rng.random() < crossover_rate:
                child = crossover(parent_a, parent_b, rng)
            else:
                child = parent_a.copy() 

            if rng.random() < mutation_rate:
                child = mutate(child, rng)

            next_population.append(child)

        population = next_population
        scores = [objective_function(state) for state in population]
        best_index = max(range(population_size), key = lambda i: scores[i])

        if scores[best_index] > best_value:
            best = population[best_index].copy()
            best_value = scores[best_index]

        history.append(max(scores))
        mean_history.append(sum(scores) / population_size)
        best_history.append(best_value)

    return {
        "initial_state": initial_best,
        "best_state": best.copy(),
        "best_value": best_value,
        "final_state": best.copy(),
        "final_value": best_value,
        "history": history,
        "mean_history": mean_history,
        "best_history": best_history,
        "population_size": population_size,
        "iterations": max_iterations,
        "duration": time.perf_counter() - started,
    }
