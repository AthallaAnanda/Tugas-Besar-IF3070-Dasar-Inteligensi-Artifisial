import math

from src.core.state import State


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def serialize_result(result):
    initial = result["initial_state"]
    best = result["best_state"]

    history = list(result["history"])

    if "best_history" in result:
        best_history = list(result["best_history"])
    else:
        best_history = []
        highest = float("-inf")

        for value in history:
            highest = max(highest, value)
            best_history.append(highest)

    metrics = {}

    for key in (
        "stuck_count",
        "accept_worse",
        "temperature_history",
        "e_deltaet_history",
        "log_e_deltaet_history",
        "population_size",
        "sideways_moves",
        "maximum_sideways_move",
        "restarts",
        "iterations_per_restart",
        "history_per_restart",
    ):
        if key in result:
            metrics[key] = result[key]

    if "e_deltaet_history" in result:
        metrics["e_deltaet_overflow_history"] = [math.isinf(value) for value in result["e_deltaet_history"]]
        metrics["exponent_nonfinite_history"] = [not math.isfinite(value) for value in result["log_e_deltaet_history"]]

    return {
        "status": "success",
        "objective_value": result["best_value"],
        "iterations": result["iterations"],
        "duration": result["duration"],
        "initial_state": initial.to_dict(),
        "final_state": best.to_dict(),
        "history": history,
        "best_history": best_history,
        "mean_history": list(result["mean_history"]) if "mean_history" in result else None,
        "metrics": metrics,
    }


def state_statistics(state: State):
    ships = []

    for item in state.ships:
        vehicles = [
            state.vehicles[placement.vehicle_id]
            for placement in item.placements
        ]

        occupied_area = sum(
            vehicle.width * vehicle.length
            for vehicle in vehicles
        )

        area = item.ship.width * item.ship.length

        ships.append({
            "ship_id": item.ship.id,
            "loaded_count": len(vehicles),
            "weight": sum(vehicle.weight for vehicle in vehicles),
            "max_capacity": item.ship.max_capacity,
            "occupied_area": occupied_area,
            "deck_area": area,
            "area_utilization": occupied_area / area,
        })

    return {
        "loaded_count": sum(item["loaded_count"] for item in ships),
        "outside_count": len(state.outside_vehicle_ids),
        "ships": ships,
    }
