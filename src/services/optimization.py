import math
import secrets

from src.algorithms.hill_climbing import steepest_ascent
from src.algorithms.simulated_annealing import simulated_annealing
from src.core.neighbor import generate_neighbors
from src.core.objective import objective_1
from src.core.state import State, create_initial_state
from src.services.serialization import serialize_result, state_statistics
from src.services.trace import TraceRecorder


ALGORITHMS = {
    "hill_climbing": {
        "label": "Steepest Ascent Hill Climbing",
        "variant": "steepest_ascent",
        "parameters": {
            "max_iterations": {
                "label": "Maksimum iterasi",
                "type": "integer",
                "default": 100,
                "min": 1,
            },
        },
    },
    "simulated_annealing": {
        "label": "Simulated Annealing",
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
}

FUNCTIONS = {
    "hill_climbing": steepest_ascent,
    "simulated_annealing": simulated_annealing,
}


def capabilities():
    return {
        "algorithms": ALGORITHMS,
        "objectives": [
            {
                "id": "objective_1",
                "label": "Total ShippingFee",
            }
        ],
    }


def read_seed(value, name):
    if value is None:
        return secrets.randbits(32)

    if type(value) is not int or value < 0:
        raise ValueError(f"{name} harus bilangan bulat tidak negatif")

    return value


def validate_parameters(algorithm, supplied):
    if not isinstance(supplied, dict):
        raise ValueError("parameters harus berupa object")

    specification = ALGORITHMS[algorithm]["parameters"]
    unknown = set(supplied) - set(specification)

    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Parameter tidak dikenal: {names}")

    parameters = {}

    for name, rules in specification.items():
        value = supplied.get(name, rules["default"])

        if rules["type"] == "integer":
            valid_type = type(value) is int
        else:
            valid_type = type(value) in (int, float)

        if not valid_type or not math.isfinite(value):
            raise ValueError(f"{name} harus berupa angka yang valid")

        if "min" in rules and value < rules["min"]:
            raise ValueError(f"{name} minimal {rules['min']}")

        if "exclusive_min" in rules and value <= rules["exclusive_min"]:
            raise ValueError(
                f"{name} harus lebih besar dari {rules['exclusive_min']}"
            )

        if "exclusive_max" in rules and value >= rules["exclusive_max"]:
            raise ValueError(
                f"{name} harus lebih kecil dari {rules['exclusive_max']}"
            )

        parameters[name] = value

    return parameters


def run_optimization(config):
    if not isinstance(config, dict):
        raise ValueError("Konfigurasi harus berupa object")

    algorithm = config.get("algorithm", "hill_climbing")

    if algorithm not in ALGORITHMS:
        raise ValueError("Algoritma belum tersedia")

    objective = config.get("objective", "objective_1")

    if objective != "objective_1":
        raise ValueError("Objective belum tersedia")

    if algorithm == "hill_climbing":
        if config.get("variant", "steepest_ascent") != "steepest_ascent":
            raise ValueError("Varian Hill Climbing belum tersedia")

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

    record_steps = config.get("record_steps", False)

    if type(record_steps) is not bool:
        raise ValueError("record_steps harus berupa boolean")

    interval = config.get("trace_interval", 1)

    if type(interval) is not int or interval < 1:
        raise ValueError("trace_interval harus bilangan bulat positif")

    initial = create_initial_state(
        [item.ship for item in problem.ships],
        list(problem.vehicles.values()),
        seed=initial_seed,
    )

    recorder = TraceRecorder(interval) if record_steps else None
    execution_parameters = dict(parameters)

    if algorithm == "simulated_annealing":
        execution_parameters["seed"] = algorithm_seed

    raw = FUNCTIONS[algorithm](
        initial,
        objective_1,
        generate_neighbors,
        execution_parameters,
        on_step=recorder,
    )

    output = serialize_result(raw)
    recording_duration = recorder.duration if recorder else 0.0

    output["duration"] = max(0.0, raw["duration"] - recording_duration)
    output["recording_duration"] = recording_duration
    output["algorithm"] = algorithm
    output["statistics"] = state_statistics(raw["best_state"])

    output["configuration"] = {
        "algorithm": algorithm,
        "variant": ALGORITHMS[algorithm].get("variant"),
        "objective": objective,
        "seed": initial_seed,
        "algorithm_seed": algorithm_seed,
        "parameters": parameters,
    }

    output["trace"] = {
        "enabled": record_steps,
        "interval": interval,
        "frames": recorder.finish() if recorder else [],
    }

    return output