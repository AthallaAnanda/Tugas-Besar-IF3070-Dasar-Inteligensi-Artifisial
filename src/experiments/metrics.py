from statistics import mean, pstdev


def summarize(results):
    if not results:
        raise ValueError("Tidak ada hasil untuk diringkas")

    values = [result["objective_value"] for result in results]
    durations = [result["duration"] for result in results]
    iterations = [result["iterations"] for result in results]

    return {
        "runs": len(results),
        "best_value": max(values),
        "worst_value": min(values),
        "mean_value": mean(values),
        "std_value": pstdev(values),
        "mean_duration": mean(durations),
        "mean_iterations": mean(iterations),
    }