export const PRIMARY_COLOR = "#2e7d32";

export function algorithmLabel(result) {
  const labels = {
    hill_climbing: "Steepest Ascent Hill Climbing",
    stochastic_hill_climbing: "Stochastic Hill Climbing",
    sideways_move: "Hill Climbing with Sideways Move",
    random_restart: "Random Restart Hill Climbing",
    simulated_annealing: "Simulated Annealing",
    genetic_algorithm: "Genetic Algorithm"
  };
  return labels[result.algorithm] || result.algorithm;
}

export function stepLabel(result) {
  if (result.algorithm === "random_restart") return "Total iterasi";
  return result.algorithm === "genetic_algorithm" ? "Generasi" : "Iterasi";
}

export function historySeries(result) {
  if (result.algorithm === "random_restart") {
    return [{ label: "Terbaik seluruh pencarian", values: result.best_history, color: PRIMARY_COLOR }];
  }
  const ga = result.algorithm === "genetic_algorithm";
  const series = [{
    label: ga ? "Maksimum populasi" : "Nilai saat ini",
    values: result.history, color: PRIMARY_COLOR
  }];
  if (ga) series.push({ label: "Rata-rata populasi", values: result.mean_history, color: "#126c8c" });
  series.push({ label: "Terbaik sepanjang pencarian", values: result.best_history, color: "#d97706", dashed: true });
  return series;
}

export function restartSeries(result, index) {
  return [{ label: "Objective", values: result.metrics.history_per_restart[index], color: PRIMARY_COLOR }];
}

export function annealingSeries(result) {
  const metrics = result.metrics;
  const acceptance = metrics.e_deltaet_history.map((factor, index) => {
    let probability = null;
    if (metrics.e_deltaet_overflow_history?.[index]) probability = 1;
    else if (Number.isFinite(factor) && factor >= 0) probability = Math.min(1, factor);
    return { x: index + 1, y: probability };
  });
  return {
    exponential: {
      color: PRIMARY_COLOR,
      points: metrics.e_deltaet_history.map((factor, index) => ({
        x: index + 1, y: Number.isFinite(factor) && factor >= 0 ? factor : null
      }))
    },
    acceptance: { color: PRIMARY_COLOR, points: acceptance },
    temperature: { color: "#e58b13", points: metrics.temperature_history.map((y, x) => ({ x, y })) }
  };
}
