import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.services.experiment import run_experiment


def runner(experiment_config, output_dir="output/results"):
    result = run_experiment(experiment_config)

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    identifier = f"{timestamp}-{uuid4().hex[:8]}"

    json_path = directory / f"{identifier}.json"
    csv_path = directory / f"{identifier}.csv"

    result["experiment_id"] = identifier
    result["saved_files"] = {
        "json": str(json_path),
        "csv": str(csv_path),
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2, allow_nan=False)

    fields = [
        "configuration_index",
        "run",
        "algorithm",
        "seed",
        "algorithm_seed",
        "objective_value",
        "iterations",
        "duration",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for item in result["results"]:
            run_result = item["result"]
            configuration = run_result["configuration"]

            writer.writerow({
                "configuration_index": item["configuration_index"],
                "run": item["run"],
                "algorithm": configuration["algorithm"],
                "seed": configuration["seed"],
                "algorithm_seed": configuration["algorithm_seed"],
                "objective_value": run_result["objective_value"],
                "iterations": run_result["iterations"],
                "duration": run_result["duration"],
            })

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("--output-dir", default="output/results")
    arguments = parser.parse_args()

    with Path(arguments.config).open(encoding="utf-8") as file:
        configuration = json.load(file)

    result = runner(configuration, arguments.output_dir)
    print(json.dumps({
        "experiment_id": result["experiment_id"],
        "summaries": result["summaries"],
        "saved_files": result["saved_files"],
    }, indent=2))


if __name__ == "__main__":
    main()