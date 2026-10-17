from src.core.state import State


def serialize_result(result):
    initial = result["initial_state"]
    best = result["best_state"]
    terminal = result.get("terminal_state", result["final_state"])

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
    ):
        if key in result:
            metrics[key] = result[key]

    return {
        "status": "success",
        "objective_value": result["best_value"],
        "iterations": result["iterations"],
        "duration": result["duration"],
        "initial_state": initial.to_dict(),
        "final_state": best.to_dict(),
        "terminal_state": terminal.to_dict(),
        "history": history,
        "best_history": best_history,
        "metrics": metrics,
        "stop_reason": result.get("stop_reason", "finished"),
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