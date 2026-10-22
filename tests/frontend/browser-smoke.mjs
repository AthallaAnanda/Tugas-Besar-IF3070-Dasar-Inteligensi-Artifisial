import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH || undefined });

try {
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  const errors = [];
  const apiPaths = new Set();
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    const path = new URL(request.url()).pathname;
    if (path.startsWith("/api/")) apiPaths.add(path);
  });
  await page.goto(process.env.APP_URL || "http://127.0.0.1:5000/", { waitUntil: "networkidle" });
  await page.waitForFunction(() => !document.getElementById("inputs").disabled);
  assert.equal(await page.locator("form").count(), 1);
  assert.equal(await page.getByRole("heading", { name: "Tugas Besar IF3070 Dasar Inteligensi Artifisial", exact: true }).count(), 1);
  assert.equal(await page.locator("#algorithm option").count(), 6);
  assert.equal(await page.locator("#objective option").count(), 2);
  assert.equal(await page.locator("#objective").inputValue(), "objective_1");
  assert.equal(await page.locator("#seed-mode").inputValue(), "random");
  assert.equal(await page.locator("#seed").isDisabled(), true);
  assert.equal(await page.locator("#algorithm-seed").isDisabled(), true);
  assert.equal(await page.locator("#initial-seed-field").isVisible(), false);

  async function optimize() {
    const [response] = await Promise.all([
      page.waitForResponse((response) => response.url().endsWith("/api/optimize")),
      page.locator('#optimization-form button[type="submit"]').click()
    ]);
    await page.waitForFunction(() => !document.getElementById("inputs").disabled);
    const result = await response.json();
    if (response.ok()) {
      assert.equal(result.output.status, "saved");
    }
    return { response, result };
  }

  await page.locator('#parameters [data-parameter="max_iterations"]').fill("2");
  const firstRandom = await optimize();
  const secondRandom = await optimize();
  assert.equal(firstRandom.response.status(), 200);
  assert.equal(secondRandom.response.status(), 200);
  for (const run of [firstRandom, secondRandom]) {
    const request = run.response.request().postDataJSON();
    assert.equal(request.seed, null);
    assert.equal(request.algorithm_seed, null);
    assert.ok(Number.isInteger(run.result.configuration.seed));
    assert.ok(Number.isInteger(run.result.configuration.algorithm_seed));
  }
  assert.notDeepEqual(
    [firstRandom.result.configuration.seed, firstRandom.result.configuration.algorithm_seed],
    [secondRandom.result.configuration.seed, secondRandom.result.configuration.algorithm_seed]
  );
  const [randomDownload] = await Promise.all([page.waitForEvent("download"), page.locator("#download-result").click()]);
  const randomExport = JSON.parse(await readFile(await randomDownload.path(), "utf8"));
  assert.deepEqual(randomExport.configuration, secondRandom.result.configuration);

  await page.locator("#algorithm").selectOption("stochastic_hill_climbing");
  assert.equal(await page.locator("#algorithm-seed").isDisabled(), true);
  await page.locator("#seed-mode").selectOption("manual");
  assert.equal(await page.locator("#seed").isDisabled(), false);
  assert.equal(await page.locator("#algorithm-seed").isDisabled(), false);
  await page.locator("#seed").fill("99");
  await page.locator("#algorithm-seed").fill("199");
  await page.locator("#seed-mode").selectOption("random");
  assert.equal(await page.locator("#algorithm-seed-field").isVisible(), false);
  await page.locator("#seed-mode").selectOption("manual");
  assert.equal(await page.locator("#seed").inputValue(), "99");
  assert.equal(await page.locator("#algorithm-seed").inputValue(), "199");
  await page.locator("#seed").fill("42");
  await page.locator("#algorithm-seed").fill("43");
  await page.locator("#algorithm").selectOption("hill_climbing");
  assert.equal(await page.locator("#algorithm-seed").isDisabled(), true);
  const hc = await optimize();
  assert.equal(hc.response.status(), 200);
  assert.equal(hc.result.algorithm, "hill_climbing");
  assert.equal(hc.response.request().postDataJSON().seed, 42);
  assert.equal(hc.result.configuration.seed, 42);
  assert.equal(await page.locator("#initial-state svg").count(), 1);
  assert.equal(await page.locator("#final-state svg").count(), 1);
  assert.match(await page.locator("#final-value").innerText(), new RegExp(String(hc.result.objective_value)));

  await page.locator("#algorithm").selectOption("stochastic_hill_climbing");
  assert.equal(await page.locator("#algorithm-seed").isDisabled(), false);
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("5");
  const stochastic = await optimize();
  assert.equal(stochastic.response.status(), 200);
  assert.equal(stochastic.result.iterations, 5);
  assert.deepEqual((await optimize()).result.history, stochastic.result.history);

  await page.locator("#algorithm").selectOption("sideways_move");
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("4");
  await page.locator('#parameters [data-parameter="maximum_sideways_move"]').fill("1");
  const sideways = await optimize();
  assert.equal(sideways.response.status(), 200);
  assert.ok(sideways.result.metrics.sideways_moves <= 1);
  assert.match(await page.locator("#statistics").innerText(), /Batas sideways move/);
  await page.locator('#parameters [data-parameter="maximum_sideways_move"]').fill("0");
  assert.equal((await optimize()).result.metrics.sideways_moves, 0);

  await page.locator("#algorithm").selectOption("random_restart");
  assert.equal(await page.locator("#algorithm-seed").isDisabled(), true);
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("2");
  await page.locator('#parameters [data-parameter="maximum_restart"]').fill("2");
  const restart = await optimize();
  assert.equal(restart.response.status(), 200);
  assert.equal(restart.result.metrics.restarts, 2);
  assert.deepEqual(restart.result.configuration.restart_seeds, [42, 43, 44]);
  assert.equal(await page.locator("#restart-summary tr").count(), 3);
  assert.equal(await page.locator("#restart-summary tr").nth(2).locator("td").nth(1).innerText(), "44");
  assert.equal(await page.locator("#history-legend span").count(), 1);
  assert.match(await page.locator("#history-legend").innerText(), /Terbaik seluruh pencarian/);
  assert.equal(await page.locator("#initial-state-heading").innerText(), "Initial State");
  await page.locator("#restart-search").selectOption("2");
  assert.equal(await page.locator("#restart-chart").evaluate((canvas) => canvas.width > 0), true);
  const [restartJSON] = await Promise.all([page.waitForEvent("download"), page.locator("#download-result").click()]);
  const exportedRestart = JSON.parse(await readFile(await restartJSON.path(), "utf8"));
  assert.deepEqual(exportedRestart.metrics.history_per_restart, restart.result.metrics.history_per_restart);
  const [restartPNG] = await Promise.all([page.waitForEvent("download"), page.locator("#download-restart-chart").click()]);
  assert.equal(restartPNG.suggestedFilename(), "restart-history.png");
  await page.locator('#parameters [data-parameter="maximum_restart"]').fill("0");
  assert.equal((await optimize()).result.metrics.restarts, 0);
  assert.equal(await page.locator("#restart-summary tr").count(), 1);

  await page.locator("#algorithm").selectOption("genetic_algorithm");
  await page.locator('#parameters [data-parameter="population_size"]').fill("4");
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("3");
  const ga = await optimize();
  assert.equal(ga.response.status(), 200);
  assert.equal(await page.locator("#restart-section").isVisible(), false);
  assert.equal(await page.locator("#history-legend span").count(), 3);
  assert.equal(await page.locator("#initial-state-heading").innerText(), "Initial State");
  assert.match(await page.locator("#history-heading").innerText(), /generasi/);
  const repeated = await optimize();
  assert.deepEqual(repeated.result.history, ga.result.history);
  assert.deepEqual(repeated.result.final_state, ga.result.final_state);
  const [jsonDownload] = await Promise.all([page.waitForEvent("download"), page.locator("#download-result").click()]);
  const exported = JSON.parse(await readFile(await jsonDownload.path(), "utf8"));
  assert.deepEqual(exported.history, ga.result.history);
  assert.deepEqual(exported.mean_history, ga.result.mean_history);
  const [png] = await Promise.all([page.waitForEvent("download"), page.locator("#download-chart").click()]);
  assert.equal(png.suggestedFilename(), "objective-history.png");
  for (const selector of ["#initial-state button", "#final-state button"]) {
    assert.equal(await page.locator(selector).innerText(), "Unduh state JPG");
    const [jpg] = await Promise.all([page.waitForEvent("download"), page.locator(selector).click()]);
    assert.match(jpg.suggestedFilename(), /\.jpg$/);
    const image = await readFile(await jpg.path());
    assert.equal(image.readUInt16BE(0), 0xffd8);
    assert.equal(image.readUInt16BE(image.length - 2), 0xffd9);
  }

  await page.locator('#parameters [data-parameter="max_iterations"]').fill("0");
  const zero = await optimize();
  assert.equal(zero.result.iterations, 0);
  assert.deepEqual(zero.result.initial_state, zero.result.final_state);
  assert.equal(await page.locator("#chart").evaluate((canvas) => canvas.width > 0), true);
  await page.locator("#seed").fill("0");
  await page.locator("#algorithm-seed").fill("0");
  const zeroSeed = await optimize();
  assert.equal(zeroSeed.result.configuration.seed, 0);
  assert.equal(zeroSeed.result.configuration.algorithm_seed, 0);
  await page.locator("#seed").fill("42");
  await page.locator("#algorithm-seed").fill("43");

  await page.locator("#algorithm").selectOption("simulated_annealing");
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("3");
  const sa = await optimize();
  assert.equal(sa.response.status(), 200);
  assert.equal(await page.locator("#diagnostics-section").isVisible(), true);
  assert.equal(await page.locator("#acceptance-chart").isVisible(), true);
  assert.equal(await page.locator("#temperature-chart").isVisible(), true);
  assert.equal(await page.locator("#exponential-chart").isVisible(), true);
  assert.equal(await page.locator("#exponential-chart").evaluate((canvas) => canvas.width > 0), true);
  assert.ok(sa.result.output.plots.some((path) => path.endsWith("-sa-exponential.png")));
  const [exponentialPNG] = await Promise.all([page.waitForEvent("download"), page.locator("#download-sa-exponential").click()]);
  assert.equal(exponentialPNG.suggestedFilename(), "sa-exponential.png");
  const exponentialImage = await readFile(await exponentialPNG.path());
  assert.equal(exponentialImage.readUInt32BE(16), await page.locator("#exponential-chart").evaluate((canvas) => canvas.width));
  assert.ok(exponentialImage.readUInt32BE(20) > await page.locator("#exponential-chart").evaluate((canvas) => canvas.height));
  assert.equal(await page.locator("#history-legend span").count(), 2);
  assert.match(await page.locator("#statistics").innerText(), /Frekuensi stuck/);
  for (const [metric, chart] of [["acceptance", "acceptance-chart"], ["temperature", "temperature-chart"]]) {
    const [saPNG] = await Promise.all([
      page.waitForEvent("download"), page.locator(`#download-sa-${metric}`).click()
    ]);
    assert.equal(saPNG.suggestedFilename(), `sa-${metric}.png`);
    const saImage = await readFile(await saPNG.path());
    const chartSizes = await page.locator(`#${chart}`).evaluate((canvas) => ({ width: canvas.width, height: canvas.height }));
    assert.equal(saImage.readUInt32BE(16), chartSizes.width);
    assert.ok(saImage.readUInt32BE(20) > chartSizes.height);
  }
  if (process.env.SA_SCREENSHOT) {
    await page.locator('#parameters [data-parameter="max_iterations"]').fill("100");
    await page.locator('#parameters [data-parameter="initial_temperature"]').fill("100");
    await optimize();
    await page.locator("#diagnostics-section").screenshot({ path: process.env.SA_SCREENSHOT });
    await page.locator('#parameters [data-parameter="initial_temperature"]').fill("1000");
  }
  assert.equal(await page.locator("#sa-analysis-extra").count(), 0);
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("0");
  assert.equal((await optimize()).result.iterations, 0);
  assert.equal(await page.locator("#temperature-chart").isVisible(), true);
  assert.equal(await page.locator("#exponential-chart").isVisible(), true);
  await page.locator('#parameters [data-parameter="max_iterations"]').fill("3");

  await page.locator("#algorithm").selectOption("genetic_algorithm");
  assert.equal(await page.locator('#parameters [data-parameter="population_size"]').inputValue(), "4");
  await page.locator('#parameters [data-parameter="elitism"]').fill("4");
  assert.equal((await optimize()).response.status(), 400);
  assert.match(await page.locator("#message").innerText(), /elite/);
  await page.locator('#parameters [data-parameter="elitism"]').fill("1");

  const originalProblem = await page.locator("#problem").inputValue();
  await page.locator("#optimization-form details summary").click();
  await page.locator("#problem").fill("{invalid");
  await page.locator('#optimization-form button[type="submit"]').click();
  await page.waitForFunction(() => document.getElementById("message").textContent.includes("JSON"));
  assert.equal(await page.locator("#inputs").isDisabled(), false);
  await page.locator("#problem").fill(originalProblem);
  await page.locator("#optimization-form details summary").click();
  await page.locator("#algorithm").selectOption("simulated_annealing");
  await optimize();

  await page.locator("#seed").fill("");
  await page.locator("#algorithm-seed").fill("");
  await page.locator("#seed-mode").selectOption("random");
  await page.locator("#algorithm").selectOption("random_restart");
  await page.locator('#parameters [data-parameter="maximum_restart"]').fill("2");
  assert.equal(await page.locator('#parameters [data-parameter="max_iterations"]').inputValue(), "2");
  const randomRestart = await optimize();
  assert.equal(randomRestart.response.status(), 200);
  assert.equal(await page.locator("#diagnostics-section").isVisible(), false);
  assert.equal(randomRestart.response.request().postDataJSON().seed, null);
  assert.deepEqual(randomRestart.result.configuration.restart_seeds, [0, 1, 2].map((index) => randomRestart.result.configuration.seed + index));
  await page.locator("#restart-search").selectOption("2");

  await page.locator("#objective").selectOption("objective_2");
  for (const algorithm of ["hill_climbing", "stochastic_hill_climbing", "sideways_move", "random_restart", "genetic_algorithm", "simulated_annealing"]) {
    await page.locator("#algorithm").selectOption(algorithm);
    await page.locator('#parameters [data-parameter="max_iterations"]').fill("2");
    const bonus = await optimize();
    assert.equal(bonus.response.status(), 200);
    assert.equal(bonus.response.request().postDataJSON().objective, "objective_2");
    assert.equal(bonus.result.configuration.objective, "objective_2");
    assert.equal(bonus.result.initial_state.value, bonus.result.history[0]);
    assert.equal(bonus.result.final_state.value, bonus.result.objective_value);
    const state = bonus.result.final_state;
    let expectedScore = 0;
    let expectedFee = 0;
    for (const item of state.ships) {
      const vehicles = item.placements.map((placement) => state.vehicles.find((vehicle) => vehicle.id === placement.vehicle_id));
      if (!vehicles.length) continue;
      const fee = vehicles.reduce((sum, vehicle) => sum + vehicle.shipping_fee, 0);
      const weight = vehicles.reduce((sum, vehicle) => sum + vehicle.weight, 0);
      const eta = Math.max(...vehicles.map((vehicle) => vehicle.eta));
      expectedFee += fee;
      expectedScore += fee / (1 + eta) / (1 + (item.ship.max_capacity ? weight / item.ship.max_capacity : 0));
    }
    assert.ok(Math.abs(bonus.result.objective_value - expectedScore) < 1e-9);
    assert.equal(bonus.result.statistics.total_shipping_fee, expectedFee);
    assert.match(await page.locator("#result-objective").innerText(), /Efisiensi Pendapatan/);
    assert.match(await page.locator("#statistics").innerText(), /Total ShippingFee/);
    assert.match(await page.locator("#statistics").innerText(), /ETA terlama/);
    assert.equal(await page.locator("#chart").evaluate((canvas) => canvas.width > 0), true);
  }
  const [bonusDownload] = await Promise.all([page.waitForEvent("download"), page.locator("#download-result").click()]);
  const bonusExport = JSON.parse(await readFile(await bonusDownload.path(), "utf8"));
  assert.equal(bonusExport.configuration.objective, "objective_2");
  assert.equal(bonusExport.final_state.value, bonusExport.objective_value);
  await page.locator("#objective").selectOption("objective_1");
  assert.match(await page.locator("#result-objective").innerText(), /Efisiensi Pendapatan/);
  await page.locator("#objective").selectOption("objective_2");

  if (process.env.SMOKE_SCREENSHOT) await page.screenshot({ path: process.env.SMOKE_SCREENSHOT, fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.locator("#algorithm").selectOption("simulated_annealing");
  assert.equal((await optimize()).response.status(), 200);
  assert.equal(await page.locator("#acceptance-chart").isVisible(), true);
  assert.equal(await page.locator("#temperature-chart").isVisible(), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  assert.equal(await page.evaluate(() => document.body.innerText.includes(" · ") || document.body.innerText.includes("—")), false);
  assert.deepEqual([...apiPaths].sort(), ["/api/capabilities", "/api/health", "/api/optimize", "/api/sample"]);
  assert.deepEqual(errors, []);
  console.log("Browser checks passed: both objectives on all six algorithms, consistent bonus exports, stacked SA analysis and combined PNG, random/manual seeds, zero limits, reproducibility, validation, exports, and mobile layout.");
} finally {
  await browser.close();
}
