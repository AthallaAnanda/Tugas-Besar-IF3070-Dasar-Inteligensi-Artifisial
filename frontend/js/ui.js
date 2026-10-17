export const $ = (id) => document.getElementById(id);
export const number = (value, digits = 2) => new Intl.NumberFormat("id-ID", { maximumFractionDigits: digits }).format(value);

export function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function download(filename, value, type = "application/json") {
  const blob = value instanceof Blob ? value : new Blob([typeof value === "string" ? value : JSON.stringify(value, null, 2)], { type });
  const url = URL.createObjectURL(blob);
  const link = element("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function downloadCanvas(canvas, filename) {
  canvas.toBlob((blob) => { if (blob) download(filename, blob); }, "image/png");
}

export function downloadChartStack(charts, filename) {
  const ratio = window.devicePixelRatio || 1;
  const titleHeight = Math.round(36 * ratio);
  const gap = Math.round(20 * ratio);
  const output = element("canvas");
  output.width = Math.max(...charts.map(({ canvas }) => canvas.width));
  output.height = charts.reduce((sum, { canvas }) => sum + titleHeight + canvas.height, 0) + gap * (charts.length - 1);
  const context = output.getContext("2d");
  context.fillStyle = "white";
  context.fillRect(0, 0, output.width, output.height);
  context.fillStyle = "#173047";
  context.font = `600 ${16 * ratio}px system-ui`;
  let top = 0;
  for (const { canvas, title } of charts) {
    context.fillText(title, 16 * ratio, top + 24 * ratio);
    context.drawImage(canvas, 0, top + titleHeight);
    top += titleHeight + canvas.height + gap;
  }
  downloadCanvas(output, filename);
}

export function addOptions(select, options) {
  select.replaceChildren();
  for (const [value, label] of options) select.append(new Option(label, value));
}

export function parameterInput(name, specification, value = specification.default) {
  const label = element("label", specification.label);
  const input = element("input");
  input.type = "number";
  input.dataset.parameter = name;
  input.value = value;
  input.step = specification.type === "integer" ? "1" : "any";
  input.required = true;
  for (const boundary of ["min", "max"]) {
    if (specification[boundary] !== undefined) input[boundary] = specification[boundary];
  }
  label.append(input);
  return label;
}

export function readParameters(container) {
  return Object.fromEntries([...container.querySelectorAll("[data-parameter]")].map((input) => [input.dataset.parameter, Number(input.value)]));
}

export function parseProblem(input) {
  try { return JSON.parse(input.value); } catch { throw new Error("Data masalah bukan JSON yang valid"); }
}

export function valueList(container, entries) {
  container.replaceChildren(...entries.map(([label, value]) => {
    const item = element("div");
    item.append(element("dt", label), element("dd", String(value)));
    return item;
  }));
}
