import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


PLOT_LOCK = Lock()


def plot_line(axes, values, label, color, *, start=0, dashed=False):
    axes.plot(
        range(start, start + len(values)),
        [float("nan") if value is None else value for value in values],
        label=label,
        color=color,
        linestyle="--" if dashed else "-",
        marker="o" if len(values) == 1 else None,
    )


def decorate(axes, title, xlabel, ylabel="Objective"):
    axes.set(title=title, xlabel=xlabel, ylabel=ylabel)
    axes.grid(True, alpha=0.25)
    axes.legend()


def save_figure(figure, path):
    try:
        FigureCanvasAgg(figure).print_png(str(path))
    finally:
        figure.clear()


def objective_plot(result, path):
    figure = Figure(figsize=(10, 5), layout="constrained")
    axes = figure.subplots()
    algorithm = result["algorithm"]
    if algorithm == "random_restart":
        xlabel = "Total iterasi"
        plot_line(axes, result["best_history"], "Terbaik seluruh pencarian", "#126c8c")
    else:
        ga = algorithm == "genetic_algorithm"
        xlabel = "Generasi" if ga else "Iterasi"
        plot_line(axes, result["history"], "Maksimum populasi" if ga else "Nilai saat ini", "#126c8c")
        if ga:
            plot_line(axes, result["mean_history"], "Rata-rata populasi", "#16806a")
        plot_line(axes, result["best_history"], "Terbaik sepanjang pencarian", "#d97706", dashed=True)
    decorate(axes, f"{algorithm} — {result['configuration']['objective']}", xlabel)
    save_figure(figure, path)


def annealing_plot(result, path):
    figure = Figure(figsize=(10, 8), layout="constrained")
    acceptance_axes, temperature_axes = figure.subplots(2, 1)
    metrics = result["metrics"]
    overflow = metrics["e_deltaet_overflow_history"]
    probabilities = [
        1 if overflow[index] else min(1, factor) if factor is not None and factor >= 0 else None
        for index, factor in enumerate(metrics["e_deltaet_history"])
    ]
    plot_line(acceptance_axes, probabilities, "Probabilitas penerimaan", "#d62828", start=1)
    acceptance_axes.set_ylim(0, 1)
    if not probabilities:
        acceptance_axes.text(0.5, 0.5, "Belum ada kandidat yang dievaluasi.",
                             ha="center", transform=acceptance_axes.transAxes)
    decorate(acceptance_axes, "Probabilitas penerimaan", "Iterasi", "min(1, exp(ΔE/T))")
    plot_line(temperature_axes, metrics["temperature_history"], "Temperatur", "#e58b13")
    temperature_axes.set_ylim(bottom=0)
    decorate(temperature_axes, "Temperatur setelah iterasi", "Iterasi", "Temperatur")
    save_figure(figure, path)


def restart_plot(result, index, path):
    figure = Figure(figsize=(10, 5), layout="constrained")
    axes = figure.subplots()
    plot_line(axes, result["metrics"]["history_per_restart"][index], "Objective", "#126c8c")
    title = "Pencarian awal" if index == 0 else f"Restart {index}"
    seed = result["configuration"]["restart_seeds"][index]
    decorate(axes, f"{title} (seed {seed})", "Iterasi per pencarian")
    save_figure(figure, path)


def save_output(result, output_dir):
    output_dir = Path(output_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"{timestamp}-{result['algorithm']}-{uuid4().hex[:12]}"
    result_path = Path("results") / f"{run_id}.json"
    objective_path = Path("plots") / f"{run_id}-objective.png"
    plots = [(objective_path, objective_plot, ())]
    if result["algorithm"] == "simulated_annealing":
        plots.append((Path("plots") / f"{run_id}-sa-analysis.png", annealing_plot, ()))
    elif result["algorithm"] == "random_restart":
        plots.extend(
            (Path("plots") / f"{run_id}-restart-{index}.png", restart_plot, (index,))
            for index in range(len(result["metrics"]["history_per_restart"]))
        )

    saved = {**result, "output": {
        "status": "saved",
        "run_id": run_id,
        "result": f"output/{result_path.as_posix()}",
        "plots": [f"output/{path.as_posix()}" for path, _, _ in plots],
    }}
    temporary = output_dir / result_path.with_suffix(".json.tmp")
    created = []
    try:
        (output_dir / "results").mkdir(parents=True, exist_ok=True)
        (output_dir / "plots").mkdir(parents=True, exist_ok=True)
        with PLOT_LOCK:
            for path, render, args in plots:
                created.append(output_dir / path)
                render(result, *args, output_dir / path)
        created.append(temporary)
        with temporary.open("x", encoding="utf-8") as file:
            json.dump(saved, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write("\n")
        temporary.replace(output_dir / result_path)
    except Exception:
        for path in created:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    return saved
