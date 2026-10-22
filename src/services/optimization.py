import random
import secrets
from time import perf_counter

from src.algorithms.genetic_algorithm import genetic_algorithm
from src.algorithms.hill_climbing import random_restart, sideways_move, steepest_ascent, stochastic_hill_climbing
from src.algorithms.simulated_annealing import simulated_annealing
from src.core.neighbor import generate_neighbors
from src.core.objective import OBJECTIVES
from src.core.state import State, create_initial_state
from src.services.serialization import json_safe, serialize_result, state_statistics
from src.services.validation import validate_fields


HC_ITERATIONS = {"label": "Maksimum iterasi", "type": "integer", "default": 100, "min": 1}

ALGORITHMS = {
    "hill_climbing": {
        "label": "Steepest Ascent Hill Climbing",
        "variant": "steepest_ascent",
        "parameters": {"max_iterations": HC_ITERATIONS},
    },
    "stochastic_hill_climbing": {
        "label": "Stochastic Hill Climbing",
        "variant": "stochastic",
        "uses_algorithm_seed": True,
        "parameters": {"max_iterations": HC_ITERATIONS},
    },
    "sideways_move": {
        "label": "Hill Climbing with Sideways Move",
        "variant": "sideways_move",
        "uses_algorithm_seed": True,
        "parameters": {
            "max_iterations": HC_ITERATIONS,
            "maximum_sideways_move": {"label": "Maksimum sideways move", "type": "integer", "default": 100, "min": 0},
        },
    },
    "random_restart": {
        "label": "Random Restart Hill Climbing",
        "variant": "random_restart",
        "parameters": {
            "max_iterations": {**HC_ITERATIONS, "label": "Maksimum iterasi per pencarian"},
            "maximum_restart": {"label": "Maksimum restart", "type": "integer", "default": 10, "min": 0},
        },
    },
    "simulated_annealing": {
        "label": "Simulated Annealing",
        "uses_algorithm_seed": True,
        "parameters": {
            "max_iterations": {
                "label": "Maksimum iterasi",
                "type": "integer",
                "default": 100,
                "min": 0,
            },
            "initial_temperature": {
                "label": "Temperatur awal",
                "type": "number",
                "default": 1000.0,
                "exclusive_min": 0,
            },
            "cooling_rate": {
                "label": "Cooling rate",
                "type": "number",
                "default": 0.95,
                "exclusive_min": 0,
                "exclusive_max": 1,
            },
            "min_temperature": {
                "label": "Temperatur minimum",
                "type": "number",
                "default": 0.001,
                "exclusive_min": 0,
            },
        },
    },
    "genetic_algorithm": {
        "label": "Genetic Algorithm",
        "uses_algorithm_seed": True,
        "parameters": {
            "max_iterations": {"label": "Maksimum generasi", "type": "integer", "default": 100, "min": 0},
            "population_size": {"label": "Jumlah populasi", "type": "integer", "default": 50, "min": 2},
            "crossover_rate": {"label": "Crossover rate", "type": "number", "default": 0.8, "min": 0, "max": 1},
            "mutation_rate": {"label": "Mutation rate", "type": "number", "default": 0.2, "min": 0, "max": 1},
            "elitism": {"label": "Jumlah elite", "type": "integer", "default": 1, "min": 0},
            "tour_size": {"label": "Tournament size", "type": "integer", "default": 2, "min": 1},
        },
    },
}

FUNCTIONS = {
    "hill_climbing": steepest_ascent,
    "stochastic_hill_climbing": stochastic_hill_climbing,
    "sideways_move": sideways_move,
    "simulated_annealing": simulated_annealing,
}


def capabilities():
    return {
        "algorithms": ALGORITHMS,
        "objectives": [
            {
                "id": "objective_1",
                "label": "Total ShippingFee",
                "description": "Memaksimalkan total tarif pengiriman kendaraan yang diangkut (juta rupiah).",
            },
            {
                "id": "objective_2",
                "label": "Efisiensi Pendapatan, Waktu, dan Berat",
                "description": (
                    "Skor per kapal = total ShippingFee / ((1 + ETA terlama) × "
                    "(1 + total berat / kapasitas)). Skor seluruh kapal dijumlahkan. "
                    "ETA terlama mendekati waktu penyelesaian pengiriman; "
                    "skor ini bukan laba bersih atau pendapatan per hari aktual."
                ),
            },
        ],
    }


def read_seed(value, name):
    if value is None:
        return secrets.randbits(32)

    if type(value) is not int or value < 0:
        raise ValueError(f"{name} harus bilangan bulat tidak negatif")

    return value


def validate_parameters(algorithm, supplied):
    parameters = validate_fields(supplied, ALGORITHMS[algorithm]["parameters"])
    if algorithm == "genetic_algorithm":
        if parameters["elitism"] >= parameters["population_size"]:
            raise ValueError("Jumlah elite harus lebih kecil daripada jumlah populasi")
        if parameters["tour_size"] > parameters["population_size"]:
            raise ValueError("Tournament size tidak boleh melebihi jumlah populasi")
    return parameters


def prepare_optimization(config):
    if not isinstance(config, dict):
        raise ValueError("Konfigurasi harus berupa object")

    algorithm = config.get("algorithm", "hill_climbing")

    if not isinstance(algorithm, str) or algorithm not in ALGORITHMS:
        raise ValueError("Algoritma belum tersedia")

    objective = config.get("objective", "objective_1")

    if not isinstance(objective, str) or objective not in OBJECTIVES:
        raise ValueError("Objective belum tersedia")

    variant = ALGORITHMS[algorithm].get("variant")
    if variant and config.get("variant", variant) != variant:
        raise ValueError("Varian tidak sesuai dengan algoritma yang dipilih")

    try:
        problem = State.from_dict(config["problem"])
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise ValueError(f"Data masalah tidak valid: {error}") from error

    initial_seed = read_seed(config.get("seed"), "seed")
    algorithm_seed = read_seed(
        config.get("algorithm_seed", initial_seed + 1),
        "algorithm_seed",
    )

    parameters = validate_parameters(
        algorithm,
        config.get("parameters", {}),
    )

    return problem, {
        "algorithm": algorithm,
        "variant": variant,
        "objective": objective,
        "seed": initial_seed,
        "algorithm_seed": algorithm_seed,
        "parameters": parameters,
    }


def run_optimization(config):
    problem, configuration = prepare_optimization(config)
    algorithm = configuration["algorithm"]
    objective_function = OBJECTIVES[configuration["objective"]]
    parameters = configuration["parameters"]
    initial_seed = configuration["seed"]
    algorithm_seed = configuration["algorithm_seed"]
    ships = [item.ship for item in problem.ships]
    vehicles = list(problem.vehicles.values())
    initialization_started = perf_counter()

    if algorithm == "genetic_algorithm":
        population_rng = random.Random(initial_seed)
        population_seeds = [population_rng.getrandbits(32) for _ in range(parameters["population_size"])]
        population = [create_initial_state(ships, vehicles, seed=seed) for seed in population_seeds]

        def initial_population():
            return population
    elif algorithm == "random_restart":
        restart_seeds = [initial_seed + index for index in range(parameters["maximum_restart"] + 1)]
        initial_states = iter([create_initial_state(ships, vehicles, seed=seed) for seed in restart_seeds])

        def initial_state_factory():
            return next(initial_states)
    else:
        initial = create_initial_state(ships, vehicles, seed=initial_seed)

    initialization_duration = perf_counter() - initialization_started

    execution_parameters = dict(parameters)

    if ALGORITHMS[algorithm].get("uses_algorithm_seed", False):
        execution_parameters["seed"] = algorithm_seed

    if algorithm == "genetic_algorithm":
        raw = genetic_algorithm(initial_population, objective_function, execution_parameters)
    elif algorithm == "random_restart":
        raw = random_restart(initial_state_factory, objective_function, generate_neighbors, execution_parameters)
    else:
        raw = FUNCTIONS[algorithm](initial, objective_function, generate_neighbors, execution_parameters)

    output = serialize_result(raw, objective_function)
    output["initialization_duration"] = initialization_duration
    output["algorithm"] = algorithm
    output["step_type"] = "generation" if algorithm == "genetic_algorithm" else "iteration"
    output["stop_reason"] = stop_reason(algorithm, raw, parameters)
    output["statistics"] = state_statistics(raw["best_state"])

    output["configuration"] = configuration
    if algorithm == "genetic_algorithm":
        output["configuration"]["population_seeds"] = population_seeds
    elif algorithm == "random_restart":
        output["configuration"]["restart_seeds"] = restart_seeds

    return json_safe(output)


def stop_reason(algorithm, result, parameters):
    if algorithm == "genetic_algorithm":
        return "max_iterations"
    if algorithm == "random_restart":
        return "max_restarts"
    if algorithm == "stochastic_hill_climbing":
        return "no_neighbors" if result["iterations"] < parameters["max_iterations"] else "max_iterations"
    if algorithm == "sideways_move":
        if parameters["maximum_sideways_move"] > 0 and result["sideways_moves"] >= parameters["maximum_sideways_move"]:
            return "max_sideways_moves"
        return "max_iterations" if result["iterations"] >= parameters["max_iterations"] else "no_admissible_move"
    if algorithm == "hill_climbing":
        return "no_improvement" if result["history"][-1] == result["history"][-2] else "max_iterations"
    if result["temperature_history"][-1] <= parameters["min_temperature"] and result["iterations"] < parameters["max_iterations"]:
        return "min_temperature"
    if result["iterations"] < parameters["max_iterations"]:
        return "no_neighbors"
    return "max_iterations"
