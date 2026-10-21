import math
import random
import time
from src.core.constraint import is_valid
from src.core.neighbor import generate_neighbors

def select_parent(population, fitness_scores, rng):
    if not population or len(population) != len(fitness_scores):
        raise ValueError("population and fitness_scores harus memiliki panjang yang sama dan tidak kosong")

    for fitness in fitness_scores:
        if not math.isfinite(fitness) or fitness < 0:
            raise ValueError("fitness_scores harus berhingga dan non-negatif")

    total_fitness = sum(fitness_scores)

    if not math.isfinite(total_fitness):
        raise ValueError("total_fitness harus berhingga")

    if total_fitness == 0:
        return rng.choice(population) # if all fitness scores are zero, select randomly

    spin = rng.random() * total_fitness
    cumulative = 0.0
    last_positive = None

    for index, fitness in enumerate(fitness_scores):
        if fitness > 0:
            last_positive = index
            cumulative += fitness
            
            if cumulative >= spin:
                return population[index]
            
    return population[last_positive]
            
def crossover(parent_a, parent_b, rng):
    child = parent_a.copy() # copy of state from parent a
    for item in child.ships:
        item.placements.clear()

    genes_a = genes(parent_a) # dictionary of vehicle_id to placement for parent a
    genes_b = genes(parent_b)
    
    ships = {}
    for item in child.ships:
        ships[item.ship.id] = item 

    vehicle_ids = sorted(child.vehicles) # list of vehicle ids in child state
    rng.shuffle(vehicle_ids)

    for vehicle_id in vehicle_ids:
        if rng.random() < 0.5: 
            source = genes_a # choose parent's gene with 50% probability
        else:
            source = genes_b
        
        placement = source.get(vehicle_id)
        if placement is None:
            continue # condition when the vehicle_id is outside the ship

        target = ships[placement.ship_id]
        target.placements.append(placement)

        if not is_valid(child):
            target.placements.pop() # erase the placement if it makes the child invalid

    return child

def genes(state):
    result = {}

    for item in state.ships: # consists of ships, each ship has placements
        for placement in item.placements: # each placement is a gene
            result[placement.vehicle_id] = placement 

    return result

def mutate(state, rng):
    selected = None
    for count, candidate in enumerate(generate_neighbors(state), start = 1): # iterate count while generating neighbors
        if rng.randrange(count) == 0: # randomly select a neighbor with uniform probability
            selected = candidate.copy()

    if selected:
        return selected
    else:
        return state.copy()

def genetic_algorithm(initial_population, objective_function, parameters = None):
    started = time.perf_counter() # function to measure the length of time taken
    p = parameters or {}

    population_size = p.get("population_size", 50)
    max_iterations = p.get("max_iterations", 100)
    crossover_rate = float(p.get("crossover_rate", 0.8))
    mutation_rate = float(p.get("mutation_rate", 0.2))
    elitism = p.get("elitism", 1)
    rng = random.Random(p.get("seed"))

    if type(population_size) is not int or population_size < 2:
        raise ValueError("population_size minimal bernilai 2") # need minimum of 2 population to select parents
    if type(max_iterations) is not int or max_iterations < 0:
        raise ValueError("max_iterations harus integer non-negatif") 
    if type(elitism) is not int or not 0 <= elitism < population_size:
        raise ValueError("elitism harus integer minimal 0 dan lebih kecil dari population_size")
    if any(not math.isfinite(rate) or not 0 <= rate <= 1
           for rate in (crossover_rate, mutation_rate)):
        raise ValueError("Probabilitas harus berhingga dan bernilai antara 0 dan 1")

    population = [state.copy() for state in initial_population()] # copy the initial population to avoid mutation of the original states
    if len(population) != population_size:
        raise ValueError("Jumlah state awal harus sama dengan population_size")
    if not all(is_valid(state) for state in population):
        raise ValueError("Semua state awal harus valid")

    reference = population[0] # first state as reference
    reference_ships = {} 
    for item in reference.ships:
        reference_ships[item.ship.id] = item.ship # define a dictionary of ship id of first state
        
    for state in population:
        ships = {}
        for item in state.ships:
            ships[item.ship.id] = item.ship # define a dictionary of ship id for each state
        if state.vehicles != reference.vehicles or ships != reference_ships:
            raise ValueError("Semua individu harus memakai acuan yang sama")

    scores = [objective_function(state) for state in population] # calculate the objective function for each state 
    best_index = max(range(population_size), key = lambda i: scores[i])
    best = population[best_index].copy()
    best_value = scores[best_index]
    initial_best = best.copy()

    history = [max(scores)]
    mean_history = [sum(scores) / population_size]
    best_history = [best_value]

    for iteration in range(max_iterations):
        ranked = sorted(range(population_size), key = lambda i: scores[i], reverse = True) # sort the indices of the population based on their scores (descending)
        next_population = [population[index].copy() for index in ranked[:elitism]] # keep the best individuals based on elitism

        while len(next_population) < population_size: 
            parent_a = select_parent(population, scores, rng) # pick from the population based on tournament selection
            parent_b = select_parent(population, scores, rng)

            if rng.random() < crossover_rate: # crossover with probability crossover_rate
                child = crossover(parent_a, parent_b, rng)
            else:
                child = parent_a.copy() 

            if rng.random() < mutation_rate: # mutate with probability mutation_rate
                child = mutate(child, rng)

            next_population.append(child) # add the child to the next population

        population = next_population
        scores = [objective_function(state) for state in population]
        best_index = max(range(population_size), key = lambda i: scores[i]) # find the index of the best individual

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
