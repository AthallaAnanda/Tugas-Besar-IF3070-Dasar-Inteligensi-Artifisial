import { drawHistory, drawLines } from "./charts.js";
import { renderState } from "./visualization.js";
import { annealingSeries, historySeries, restartSeries, stepLabel } from "./results.js";
import { $, addOptions, download, downloadCanvas, downloadChartStack, element, number, valueList } from "./ui.js";

const stopLabels = {
  no_improvement: "Pencarian berhenti karena tidak ada neighbor yang lebih baik.",
  min_temperature: "Pencarian mencapai temperatur minimum.",
  no_neighbors: "Pencarian berhenti karena tidak ada neighbor valid.",
  max_iterations: "Pencarian mencapai batas iterasi atau generasi.",
  max_sideways_moves: "Pencarian mencapai batas sideways move.",
  no_admissible_move: "Tidak ada perpindahan yang dapat diterima dengan batas sideways move saat ini.",
  max_restarts: "Pencarian awal dan seluruh restart selesai."
};

export class ResultView {
  constructor() {
    $("download-result").onclick = () => { if (this.result) download("optimization-result.json", this.result); };
    $("download-chart").onclick = () => downloadCanvas($("chart"), "objective-history.png");
    $("download-diagnostic").onclick = () => downloadCanvas($("diagnostic-chart"), "sa-diagnostic.png");
    $("download-sa-analysis").onclick = () => downloadChartStack([
      { canvas: $("acceptance-chart"), title: "Probabilitas penerimaan" },
      { canvas: $("temperature-chart"), title: "Temperatur setelah iterasi" }
    ], "sa-analysis.png");
    $("diagnostic-metric").onchange = () => this.drawDiagnostic();
    $("sa-analysis-extra").ontoggle = () => { if ($("sa-analysis-extra").open) this.drawDiagnostic(); };
    $("restart-search").onchange = () => this.drawRestart();
    $("download-restart-chart").onclick = () => downloadCanvas($("restart-chart"), "restart-history.png");
    window.addEventListener("resize", () => this.redraw());
  }

  show(result, objectiveLabel) {
    this.result = result;
    $("result-section").hidden = false;
    $("result-objective").textContent = `Objective: ${objectiveLabel}`;
    $("result-status").textContent = stopLabels[result.stop_reason];
    const entries = [
      ["Objective terbaik", number(result.objective_value)],
      ["Objective awal", number(result.history[0])],
      [stepLabel(result), number(result.iterations, 0)],
      ["Durasi pencarian", `${number(result.duration, 4)} detik`]
    ];
    $("metrics").replaceChildren(...entries.map(([title, value]) => {
      const card = element("div", undefined, "metric");
      card.append(element("span", title), element("strong", value));
      return card;
    }));
    const statistics = [
      ["Total ShippingFee (juta rupiah)", number(result.statistics.total_shipping_fee)],
      ["Kendaraan dimuat", result.statistics.loaded_count],
      ["Kendaraan di luar", result.statistics.outside_count],
      ["Peningkatan objective", number(result.objective_value - result.history[0])],
      ["Durasi inisialisasi", `${number(result.initialization_duration, 4)} detik`]
    ];
    for (const ship of result.statistics.ships) {
      statistics.push([`ShippingFee ${ship.ship_id} (juta rupiah)`, number(ship.shipping_fee)]);
      statistics.push([`ETA terlama ${ship.ship_id}`, ship.max_eta === null ? "Tidak ada muatan" : `${number(ship.max_eta, 0)} hari`]);
      statistics.push([`Utilisasi geladak ${ship.ship_id}`, `${number(ship.area_utilization * 100)}%`]);
      statistics.push([`Berat muatan ${ship.ship_id}`, `${number(ship.weight)} dari ${number(ship.max_capacity)}`]);
    }
    if (result.metrics.population_size !== undefined) statistics.push(["Jumlah populasi", result.metrics.population_size]);
    if (result.metrics.stuck_count !== undefined) statistics.push(["Frekuensi stuck", result.metrics.stuck_count]);
    if (result.metrics.accept_worse !== undefined) statistics.push(["Solusi lebih buruk diterima", result.metrics.accept_worse]);
    if (result.metrics.sideways_moves !== undefined) {
      statistics.push(["Sideways move", result.metrics.sideways_moves]);
      statistics.push(["Batas sideways move", result.metrics.maximum_sideways_move]);
    }
    if (result.metrics.restarts !== undefined) {
      statistics.push(["Jumlah restart", result.metrics.restarts]);
      statistics.push(["Total pencarian", result.metrics.restarts + 1]);
    }
    valueList($("statistics"), statistics);
    $("initial-value").textContent = `Objective: ${number(result.history[0])}`;
    $("final-value").textContent = `Objective: ${number(result.objective_value)}`;
    renderState(result.initial_state, $("initial-state"));
    renderState(result.final_state, $("final-state"));
    const heading = result.algorithm === "random_restart" ? "Objective terbaik terhadap total iterasi"
      : `Objective terhadap ${stepLabel(result).toLowerCase()}`;
    $("history-heading").textContent = heading;
    $("chart").setAttribute("aria-label", heading);
    $("history-legend").replaceChildren(...historySeries(result).map((series) => {
      const label = element("span", series.label);
      label.style.color = series.color;
      return label;
    }));
    $("diagnostics-section").hidden = result.algorithm !== "simulated_annealing";
    this.showRestarts();
    this.redraw();
  }

  showRestarts() {
    const result = this.result;
    const isRestart = result.algorithm === "random_restart";
    $("restart-section").hidden = !isRestart;
    $("restart-summary").replaceChildren();
    $("restart-search").replaceChildren();
    if (!isRestart) return;
    const searches = result.metrics.history_per_restart;
    const label = (index) => index === 0 ? "Pencarian awal" : `Restart ${index}`;
    addOptions($("restart-search"), searches.map((_, index) => [String(index), label(index)]));
    $("restart-summary").replaceChildren(...searches.map((history, index) => {
      const row = element("tr");
      const values = [label(index), result.configuration.restart_seeds[index],
        result.metrics.iterations_per_restart[index], number(history[0]), number(history.at(-1))];
      row.append(...values.map((value) => element("td", String(value))));
      return row;
    }));
  }

  drawRestart() {
    if (this.result?.algorithm !== "random_restart") return;
    const series = restartSeries(this.result, Number($("restart-search").value)).map((item) => ({
      ...item, points: item.values.map((y, x) => ({ x, y }))
    }));
    drawLines($("restart-chart"), series, "Iterasi per pencarian", "Objective");
  }

  drawDiagnostic() {
    if (this.result?.algorithm !== "simulated_annealing" || !$("sa-analysis-extra").open) return;
    const field = $("diagnostic-metric").value;
    const offset = field === "temperature_history" ? 0 : 1;
    const points = this.result.metrics[field].map((y, index) => ({ x: index + offset, y }));
    const label = $("diagnostic-metric").selectedOptions[0].textContent;
    drawLines($("diagnostic-chart"), [{ points, color: "#126c8c" }], "Iterasi", label);
  }

  drawAnnealing() {
    if (this.result?.algorithm !== "simulated_annealing") return;
    const series = annealingSeries(this.result);
    const domain = { xMin: 0, xMax: this.result.iterations };
    drawLines($("acceptance-chart"), [series.acceptance], "Iterasi", "min(1, exp(ΔE/T))", {
      ...domain, yMin: 0, yMax: 1, emptyMessage: "Belum ada kandidat yang dievaluasi."
    });
    drawLines($("temperature-chart"), [series.temperature], "Iterasi", "Temperatur", { ...domain, yMin: 0 });
  }

  redraw() {
    if (!this.result) return;
    drawHistory($("chart"), this.result);
    this.drawAnnealing();
    this.drawDiagnostic();
    this.drawRestart();
  }
}
