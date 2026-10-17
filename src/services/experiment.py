from src.experiments.metrics import summarize
from src.services.optimization import read_seed, run_optimization


def run_experiment(config):
    if not isinstance(config, dict):
        raise ValueError("Konfigurasi eksperimen harus berupa object")

    problem = config.get("problem")
    configurations = config.get("configurations")
    runs = config.get("runs", 3)
    base_seed = read_seed(config.get("seed"), "seed")

    if type(runs) is not int or runs < 1:
        raise ValueError("runs harus bilangan bulat positif")

    if not isinstance(configurations, list) or not configurations:
        raise ValueError("configurations harus berupa daftar yang tidak kosong")

    if any(not isinstance(item, dict) for item in configurations):
        raise ValueError("Setiap konfigurasi harus berupa object")

    results = []
    summaries = []

    for index, configuration in enumerate(configurations):
        group = []

        for run in range(runs):
            request = {
                **configuration,
                "problem": problem,
                "seed": base_seed + run,
                "algorithm_seed": base_seed + 100000 + run,
                "record_steps": False,
            }

            result = run_optimization(request)
            group.append(result)

            results.append({
                "configuration_index": index,
                "run": run + 1,
                "result": result,
            })

        summaries.append({
            "configuration_index": index,
            "configuration": group[0]["configuration"],
            **summarize(group),
        })

    return {
        "status": "success",
        "base_seed": base_seed,
        "runs_per_configuration": runs,
        "summaries": summaries,
        "results": results,
    }