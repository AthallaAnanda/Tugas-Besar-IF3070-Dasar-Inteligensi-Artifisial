import {
  getHealth,
  getCapabilities,
  getSample,
  optimize,
  experiment
} from "./api.js";

import {
  renderState,
  materializeFrame
} from "./visualization.js";

import { drawHistory } from "./charts.js";
import { ReplayController } from "./replay.js";

const form = document.getElementById("optimization-form");
const inputs = document.getElementById("inputs");
const algorithmInput = document.getElementById("algorithm");
const parametersContainer = document.getElementById("parameters");
const problemInput = document.getElementById("problem");
const message = document.getElementById("message");
const canvas = document.getElementById("chart");
const resultSection = document.getElementById("result-section");
const resultStatus = document.getElementById("result-status");

let available = null;
let lastResult = null;
let lastExperiment = null;
let activeIteration = 0;

const decisionLabels = {
  initial: "Kondisi awal",
  improved: "Solusi lebih baik diterima",
  no_improvement: "Tidak ada perbaikan",
  accepted_worse: "Solusi lebih buruk diterima",
  accepted_equal: "Solusi bernilai sama diterima",
  rejected: "Kandidat ditolak"
};

const stopReasonLabels = {
  no_improvement: "Pencarian selesai karena tidak ada neighbor yang lebih baik.",
  min_temperature: "Pencarian mencapai temperatur minimum.",
  no_neighbors: "Pencarian berhenti karena tidak ada neighbor valid.",
  max_iterations: "Pencarian mencapai batas iterasi.",
  finished: "Pencarian selesai."
};

function notify(text, error = false) {
  message.textContent = text;
  message.classList.toggle("error", error);
}

function number(value, digits = 2) {
  return new Intl.NumberFormat("id-ID", {
    maximumFractionDigits: digits
  }).format(value);
}

function download(filename, blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();

  window.setTimeout(function () {
    URL.revokeObjectURL(url);
  }, 1000);
}

function downloadJSON(filename, value) {
  download(filename, new Blob(
    [JSON.stringify(value, null, 2)],
    { type: "application/json" }
  ));
}

function readProblem() {
  try {
    return JSON.parse(problemInput.value);
  } catch {
    throw new Error("Data masalah bukan JSON yang valid");
  }
}

function appendTraceInterval() {
  const label = document.createElement("label");
  const title = document.createElement("span");
  const input = document.createElement("input");

  title.textContent = "Interval rekaman";

  input.id = "trace-interval";
  input.type = "number";
  input.min = "1";
  input.step = "1";
  input.value = "1";
  input.required = true;

  label.append(title, input);
  parametersContainer.append(label);
}

function buildParameters() {
  parametersContainer.replaceChildren();

  const definition = available.algorithms[algorithmInput.value];
  let hasMaxIterations = false;

  for (const [name, specification] of Object.entries(definition.parameters)) {
    const label = document.createElement("label");
    const title = document.createElement("span");
    const input = document.createElement("input");

    title.textContent = specification.label;

    input.type = "number";
    input.name = name;
    input.dataset.parameter = name;
    input.value = String(specification.default);
    input.step = specification.type === "integer" ? "1" : "any";
    input.required = true;

    if (specification.min !== undefined) {
      input.min = String(specification.min);
    }

    label.append(title, input);
    parametersContainer.append(label);

    if (name === "max_iterations") {
      appendTraceInterval();
      hasMaxIterations = true;
    }
  }

  if (!hasMaxIterations) {
    appendTraceInterval();
  }
}

function readParameters() {
  const parameters = {};

  for (const input of parametersContainer.querySelectorAll("input[data-parameter]")) {
    parameters[input.dataset.parameter] = Number(input.value);
  }

  return parameters;
}

function createRequest() {
  return {
    algorithm: algorithmInput.value,
    objective: document.getElementById("objective").value,
    seed: Number(document.getElementById("seed").value),
    algorithm_seed: Number(
      document.getElementById("algorithm-seed").value
    ),
    problem: readProblem(),
    parameters: readParameters(),
    record_steps: document.getElementById("record-steps").checked,
    trace_interval: Number(
      document.getElementById("trace-interval").value
    )
  };
}

function renderMetrics(result) {
  const container = document.getElementById("metrics");
  container.replaceChildren();

  const entries = [
    ["Objective terbaik", number(result.objective_value)],
    ["Iterasi", number(result.iterations, 0)],
    ["Durasi pencarian", number(result.duration, 4) + " detik"],
    ["Kendaraan dimuat", number(result.statistics.loaded_count, 0)]
  ];

  for (const [label, value] of entries) {
    const card = document.createElement("div");
    card.className = "metric";

    const title = document.createElement("span");
    title.textContent = label;

    const content = document.createElement("strong");
    content.textContent = value;

    card.append(title, content);
    container.append(card);
  }
}

const replay = new ReplayController(function (frame, previousFrame) {
  if (!lastResult) {
    return;
  }

  const state = materializeFrame(lastResult.initial_state, frame);
  const previousState = previousFrame
    ? materializeFrame(lastResult.initial_state, previousFrame)
    : null;

  renderState(
    state,
    document.getElementById("replay-state"),
    previousState
  );

  activeIteration = frame.iteration;

  const details = [
    "Iterasi " + frame.iteration + " dari " + lastResult.iterations,
    "Nilai saat ini: " + number(frame.objective_value),
    "Nilai terbaik: " + number(frame.best_value)
  ];

  const replayInfo = document.getElementById("replay-info");
  replayInfo.textContent = details.join(". ") + ".";
  replayInfo.append(
    document.createElement("br"),
    document.createTextNode(
      (decisionLabels[frame.decision] || frame.decision || "Langkah pencarian") + "."
    )
  );

  if (frame.temperature !== undefined) {
    replayInfo.append(
      document.createElement("br"),
      document.createTextNode("Temperatur: " + number(frame.temperature, 4) + ".")
    );
  }

  drawHistory(canvas, lastResult, activeIteration);
});

function showResult(result) {
  lastResult = result;
  activeIteration = 0;

  resultSection.hidden = false;
  resultStatus.textContent =
    stopReasonLabels[result.stop_reason] || "Pencarian selesai.";

  renderMetrics(result);

  renderState(
    result.initial_state,
    document.getElementById("initial-state")
  );

  renderState(
    result.final_state,
    document.getElementById("final-state")
  );

  replay.load(result.trace.frames);

  if (result.trace.frames.length === 0) {
    document.getElementById("replay-info").textContent =
      "Rekaman dinonaktifkan untuk proses ini.";

    document.getElementById("replay-state").replaceChildren();
  }

  drawHistory(canvas, result, activeIteration);
}

function showExperiment(result) {
  lastExperiment = result;

  document.getElementById("experiment-section").hidden = false;

  const body = document.getElementById("experiment-summary");
  body.replaceChildren();

  for (const summary of result.summaries) {
    const row = document.createElement("tr");

    const values = [
      available.algorithms[summary.configuration.algorithm].label,
      summary.runs,
      number(summary.best_value),
      number(summary.mean_value),
      number(summary.std_value),
      number(summary.mean_duration, 4) + " detik"
    ];

    for (const value of values) {
      const cell = document.createElement("td");
      cell.textContent = String(value);
      row.append(cell);
    }

    body.append(row);
  }

  document.getElementById("experiment-files").textContent =
    "Tersimpan: " + result.saved_files.json +
    " dan " + result.saved_files.csv;
}

async function loadSample() {
  const sample = await getSample();
  problemInput.value = JSON.stringify(sample, null, 2);
}

form.addEventListener("submit", async function (event) {
  event.preventDefault();

  if (!form.reportValidity()) {
    return;
  }

  replay.pause();
  inputs.disabled = true;
  notify("");

  try {
    const result = await optimize(createRequest());
    showResult(result);
    notify("");

    requestAnimationFrame(function () {
      resultSection.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "start"
      });
    });
  } catch (error) {
    notify(error.message, true);
  } finally {
    inputs.disabled = false;
  }
});

document.getElementById("sample-button").addEventListener(
  "click",
  async function () {
    try {
      await loadSample();
      notify("Contoh data dimuat.");
    } catch (error) {
      notify(error.message, true);
    }
  }
);

document.getElementById("problem-file").addEventListener(
  "change",
  async function (event) {
    const file = event.target.files[0];

    if (!file) {
      return;
    }

    try {
      const parsed = JSON.parse(await file.text());
      problemInput.value = JSON.stringify(parsed, null, 2);
      notify("Data dimuat dari " + file.name);
    } catch {
      notify("Berkas tidak berisi JSON yang valid.", true);
    }
  }
);

algorithmInput.addEventListener("change", buildParameters);

document.getElementById("experiment-button").addEventListener(
  "click",
  async function () {
    if (!form.reportValidity()) {
      return;
    }

    replay.pause();
    inputs.disabled = true;
    notify("Menjalankan eksperimen, masing-masing algoritma tiga kali.");

    try {
      const request = createRequest();
      const iterations = Math.max(
        1,
        request.parameters.max_iterations
      );

      const result = await experiment({
        problem: request.problem,
        seed: request.seed,
        runs: 3,
        configurations: [
          {
            algorithm: "hill_climbing",
            objective: "objective_1",
            parameters: {
              max_iterations: iterations
            }
          },
          {
            algorithm: "simulated_annealing",
            objective: "objective_1",
            parameters: {
              max_iterations: iterations,
              initial_temperature:
                request.parameters.initial_temperature ?? 1000,
              cooling_rate:
                request.parameters.cooling_rate ?? 0.95,
              min_temperature:
                request.parameters.min_temperature ?? 0.001
            }
          }
        ]
      });

      showExperiment(result);
      notify("Eksperimen selesai dan hasil tersimpan.");
    } catch (error) {
      notify(error.message, true);
    } finally {
      inputs.disabled = false;
    }
  }
);

document.getElementById("download-result").addEventListener(
  "click",
  function () {
    if (lastResult) {
      downloadJSON("optimization-result.json", lastResult);
    }
  }
);

document.getElementById("download-chart").addEventListener(
  "click",
  function () {
    canvas.toBlob(function (blob) {
      if (blob) {
        download("objective-history.png", blob);
      }
    }, "image/png");
  }
);

document.getElementById("download-experiment").addEventListener(
  "click",
  function () {
    if (lastExperiment) {
      downloadJSON("experiment-result.json", lastExperiment);
    }
  }
);

document.getElementById("download-csv").addEventListener(
  "click",
  function () {
    if (!lastExperiment) {
      return;
    }

    const rows = [[
      "configuration",
      "run",
      "algorithm",
      "seed",
      "objective_value",
      "iterations",
      "duration"
    ]];

    for (const item of lastExperiment.results) {
      const result = item.result;

      rows.push([
        item.configuration_index,
        item.run,
        result.algorithm,
        result.configuration.seed,
        result.objective_value,
        result.iterations,
        result.duration
      ]);
    }

    const csv = rows.map(function (row) {
      return row.map(function (value) {
        return '"' + String(value).replaceAll('"', '""') + '"';
      }).join(",");
    }).join("\r\n");

    download(
      "experiment-result.csv",
      new Blob([csv], { type: "text/csv;charset=utf-8" })
    );
  }
);

window.addEventListener("resize", function () {
  if (lastResult) {
    drawHistory(canvas, lastResult, activeIteration);
  }
});

async function initialize() {
  inputs.disabled = true;

  try {
    const health = await getHealth();

    document.getElementById("backend-status").textContent =
      health.message;

    available = await getCapabilities();

    for (const [id, definition] of Object.entries(available.algorithms)) {
      const option = document.createElement("option");
      option.value = id;
      option.textContent = definition.label;
      algorithmInput.append(option);
    }

    const objectiveInput = document.getElementById("objective");

    for (const objective of available.objectives) {
      const option = document.createElement("option");
      option.value = objective.id;
      option.textContent = objective.label;
      objectiveInput.append(option);
    }

    buildParameters();
    await loadSample();
    inputs.disabled = false;
    notify("");
  } catch (error) {
    document.getElementById("backend-status").textContent =
      "Backend tidak terhubung";

    notify(error.message, true);
  }
}

initialize();
