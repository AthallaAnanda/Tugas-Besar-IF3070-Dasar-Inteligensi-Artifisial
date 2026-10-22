

def validate_limit(parameters, name, default, minimum=1):
    value = parameters.get(name, default)
    if type(value) is not int or value < minimum:
        qualifier = "positif" if minimum == 1 else "tidak negatif"
        raise ValueError(f"{name} harus bilangan bulat {qualifier}")
    return value


def build_result(initial_state, final_state, best_value, history, iterations, duration, **metrics):
    result = {
        "initial_state": initial_state,
        "final_state": final_state,
        "best_state": final_state,
        "best_value": best_value,
        "history": history,
        "iterations": iterations,
        "duration": duration,
    }
    result.update(metrics)
    return result
