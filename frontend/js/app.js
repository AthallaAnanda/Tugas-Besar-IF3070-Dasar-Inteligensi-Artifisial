import { getCapabilities, getHealth, getSample, optimize } from "./api.js";
import { ResultView } from "./result-view.js";
import { $, addOptions, parameterInput, parseProblem, readParameters } from "./ui.js";

const optimization = new ResultView();
let available;
const parameterValues = new Map();

function notify(text, error = false) {
  $("message").textContent = text;
  $("message").classList.toggle("error", error);
}

function updateSeedControls() {
  const manual = $("seed-mode").value === "manual";
  $("initial-seed-field").hidden = !manual;
  $("algorithm-seed-field").hidden = !manual;
  $("seed").disabled = !manual;
  $("algorithm-seed").disabled = !manual || !available.algorithms[$("algorithm").value].uses_algorithm_seed;
}

function updateObjectiveDescription() {
  const objective = available.objectives.find((item) => item.id === $("objective").value);
  $("objective-description").textContent = objective.description;
}

function buildParameters() {
  const algorithm = $("algorithm").value;
  const definition = available.algorithms[algorithm];
  updateSeedControls();
  $("parameters").replaceChildren();
  const saved = parameterValues.get(algorithm) || {};
  for (const [name, field] of Object.entries(definition.parameters)) {
    $("parameters").append(parameterInput(name, field, saved[name] ?? field.default));
  }
}
$("parameters").addEventListener("input", () => parameterValues.set($("algorithm").value, readParameters($("parameters"))));
$("algorithm").onchange = buildParameters;
$("seed-mode").onchange = updateSeedControls;
$("objective").onchange = updateObjectiveDescription;
$("sample-button").onclick = async () => {
  try {
    $("problem").value = JSON.stringify(await getSample(), null, 2);
  } catch (error) { notify(error.message, true); }
};
$("problem-file").onchange = async (event) => {
  try {
    if (!event.target.files[0]) return;
    $("problem").value = JSON.stringify(JSON.parse(await event.target.files[0].text()), null, 2);
  } catch { notify("Berkas tidak berisi JSON yang valid.", true); }
};

$("optimization-form").onsubmit = async (event) => {
  event.preventDefault();
  if (!event.target.reportValidity()) return;
  const manualSeed = $("seed-mode").value === "manual";
  $("inputs").disabled = true;
  notify("Pencarian sedang berjalan.");
  try {
    const result = await optimize({
      algorithm: $("algorithm").value, objective: $("objective").value,
      seed: manualSeed ? Number($("seed").value) : null,
      algorithm_seed: manualSeed ? Number($("algorithm-seed").value) : null,
      parameters: readParameters($("parameters")), problem: parseProblem($("problem"))
    });
    const objective = available.objectives.find((item) => item.id === result.configuration.objective);
    optimization.show(result, objective.label);
    notify("");
    $("result-section").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { notify(error.message, true); }
  finally { $("inputs").disabled = false; }
};

async function initialize() {
  $("inputs").disabled = true;
  try {
    const [health, capabilities, sample] = await Promise.all([getHealth(), getCapabilities(), getSample()]);
    available = capabilities;
    $("backend-status").textContent = health.message;
    addOptions($("algorithm"), Object.entries(available.algorithms).map(([id, definition]) => [id, definition.label]));
    addOptions($("objective"), available.objectives.map((item) => [item.id, item.label]));
    updateObjectiveDescription();
    buildParameters();
    $("problem").value = JSON.stringify(sample, null, 2);
    $("inputs").disabled = false;
  } catch (error) {
    $("backend-status").textContent = "Backend tidak terhubung";
    notify(error.message, true);
  }
}
initialize();
