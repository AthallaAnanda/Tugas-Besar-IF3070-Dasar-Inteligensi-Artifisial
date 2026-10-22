import assert from "node:assert/strict";
import test from "node:test";
import { annealingSeries, historySeries, restartSeries, stepLabel } from "../../frontend/js/results.js";
import { drawLines } from "../../frontend/js/charts.js";

test("GA charts distinguish the last generation from the best solution found", () => {
  const result = { algorithm: "genetic_algorithm", history: [20, 10], mean_history: [15, 5], best_history: [20, 20] };
  const series = historySeries(result);
  assert.deepEqual(series.map((item) => item.values), [[20, 10], [15, 5], [20, 20]]);
  assert.equal(new Set(series.map((item) => item.color)).size, 3);
  assert.equal(stepLabel(result), "Generasi");
});

test("restart aggregate is best-so-far while individual histories retain their own initial values", () => {
  const result = {
    algorithm: "random_restart", history: [10, 20, 20, 30], best_history: [10, 20, 20, 30],
    metrics: { history_per_restart: [[10, 20], [5, 5, 30]] }
  };
  assert.equal(stepLabel(result), "Total iterasi");
  assert.deepEqual(historySeries(result).map((series) => series.values), [[10, 20, 20, 30]]);
  assert.deepEqual(restartSeries(result, 1)[0].values, [5, 5, 30]);
  assert.match(historySeries(result)[0].label, /Terbaik/);
});

test("single-state searches show current and best values against iterations", () => {
  const result = { algorithm: "simulated_annealing", history: [20, 10], best_history: [20, 20] };
  assert.deepEqual(historySeries(result).map((item) => item.values), [[20, 10], [20, 20]]);
  assert.equal(stepLabel(result), "Iterasi");
});

test("SA acceptance probabilities handle improving, equal, worse, underflow and overflow factors", () => {
  const factors = [Math.exp(2), 1, Math.exp(-2), 0, null, null];
  const result = { metrics: {
    e_deltaet_history: factors,
    e_deltaet_overflow_history: [false, false, false, false, true, false],
    temperature_history: [100, 90, 81, 72.9, 65.61, 59.049, 53.1441]
  } };
  const series = annealingSeries(result);
  assert.deepEqual(series.acceptance.points.map((point) => point.y), [1, 1, Math.exp(-2), 0, 1, null]);
  assert.deepEqual(series.exponential.points.map((point) => point.y), [Math.exp(2), 1, Math.exp(-2), 0, null, null]);
  assert.deepEqual(series.exponential.points.map((point) => point.x), [1, 2, 3, 4, 5, 6]);
  assert.deepEqual(series.acceptance.points.map((point) => point.x), [1, 2, 3, 4, 5, 6]);
  assert.deepEqual(series.temperature.points[0], { x: 0, y: 100 });
  assert.deepEqual(series.temperature.points.at(-1), { x: 6, y: 53.1441 });
  assert.deepEqual(factors, [Math.exp(2), 1, Math.exp(-2), 0, null, null]);
});

test("SA with no evaluated candidates has no fabricated probability at iteration zero", () => {
  const series = annealingSeries({ metrics: {
    e_deltaet_history: [], e_deltaet_overflow_history: [], temperature_history: [100]
  } });
  assert.deepEqual(series.acceptance.points, []);
  assert.deepEqual(series.exponential.points, []);
  assert.deepEqual(series.temperature.points, [{ x: 0, y: 100 }]);
});

test("a constant acceptance curve keeps its probability axis fixed at zero to one", (t) => {
  const previousWindow = globalThis.window;
  globalThis.window = { devicePixelRatio: 1 };
  t.after(() => { globalThis.window = previousWindow; });
  const ticks = [];
  const context = {
    setTransform() {}, fillRect() {}, beginPath() {}, moveTo() {}, lineTo() {}, stroke() {},
    setLineDash() {}, arc() {}, fill() {},
    fillText(text) { if (this.textAlign === "right") ticks.push(text); }
  };
  const canvas = { getBoundingClientRect: () => ({ width: 600 }), getContext: () => context };
  drawLines(canvas, [{ points: [{ x: 1, y: 1 }, { x: 2, y: 1 }], color: "red" }], "Iterasi", "Probabilitas", {
    xMin: 0, xMax: 2, yMin: 0, yMax: 1
  });
  assert.deepEqual(ticks, ["0", "0.25", "0.5", "0.75", "1"]);
});
