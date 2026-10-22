import json
import math
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from .optimization import ALGORITHMS


PLOT_LOCK = Lock()
PRIMARY_COLOR = "#2e7d32"


def plot_title(result, subject):
    algorithm = ALGORITHMS[result["algorithm"]]["label"]
    objective = result["configuration"]["objective"]
    return f"{algorithm}\n{subject} ({objective})"


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
        plot_line(axes, result["best_history"], "Terbaik seluruh pencarian", PRIMARY_COLOR)
    else:
        ga = algorithm == "genetic_algorithm"
        xlabel = "Generasi" if ga else "Iterasi"
        plot_line(axes, result["history"], "Maksimum populasi" if ga else "Nilai saat ini", PRIMARY_COLOR)
        if ga:
            plot_line(axes, result["mean_history"], "Rata-rata populasi", "#126c8c")
        plot_line(axes, result["best_history"], "Terbaik sepanjang pencarian", "#d97706", dashed=True)
    subject = ("Objective maksimum dan rata-rata populasi terhadap generasi"
               if algorithm == "genetic_algorithm" else f"Objective terhadap {xlabel.lower()}")
    decorate(axes, plot_title(result, subject), xlabel)
    save_figure(figure, path)


def annealing_plot(result, path):
    figure = Figure(figsize=(10, 8), layout="constrained")
    figure.suptitle(plot_title(result, "Analisis probabilitas penerimaan dan temperatur"))
    acceptance_axes, temperature_axes = figure.subplots(2, 1)
    metrics = result["metrics"]
    overflow = metrics["e_deltaet_overflow_history"]
    probabilities = [
        1 if overflow[index] else min(1, factor) if factor is not None and factor >= 0 else None
        for index, factor in enumerate(metrics["e_deltaet_history"])
    ]
    plot_line(acceptance_axes, probabilities, "Probabilitas penerimaan", PRIMARY_COLOR, start=1)
    acceptance_axes.set_ylim(0, 1)
    if not probabilities:
        acceptance_axes.text(0.5, 0.5, "Belum ada kandidat yang dievaluasi.",
                             ha="center", transform=acceptance_axes.transAxes)
    decorate(acceptance_axes, "Probabilitas penerimaan", "Iterasi", "min(1, exp(ΔE/T))")
    plot_line(temperature_axes, metrics["temperature_history"], "Temperatur", "#e58b13")
    temperature_axes.set_ylim(bottom=0)
    decorate(temperature_axes, "Temperatur setelah iterasi", "Iterasi", "Temperatur")
    save_figure(figure, path)


def annealing_exponential_plot(result, path):
    figure = Figure(figsize=(10, 5), layout="constrained")
    axes = figure.subplots()
    metrics = result["metrics"]
    values = [
        factor if factor is not None and math.isfinite(factor) and factor >= 0 else None
        for factor in metrics["e_deltaet_history"]
    ]
    plot_line(axes, values, "exp(ΔE/T)", PRIMARY_COLOR, start=1)
    axes.set_xlim(0, max(1, result["iterations"]))
    axes.set_ylim(bottom=0)
    overflow_count = sum(metrics["e_deltaet_overflow_history"])
    notes = []
    if not values:
        notes.append("Belum ada kandidat yang dievaluasi.")
    elif not any(value is not None for value in values):
        notes.append("Tidak ada nilai terbatas untuk ditampilkan.")
    if overflow_count:
        notes.append(f"{overflow_count} nilai overflow tidak digambar; lihat data JSON untuk detailnya.")
    if notes:
        figure.text(0.5, 0.01, "\n".join(notes), ha="center", fontsize=9)
        figure.get_layout_engine().set(rect=(0, 0.1, 1, 0.9))
    decorate(axes, plot_title(result, "exp(ΔE/T) terhadap iterasi"), "Iterasi", "exp(ΔE/T)")
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
        plots.append((Path("plots") / f"{run_id}-sa-exponential.png", annealing_exponential_plot, ()))

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
