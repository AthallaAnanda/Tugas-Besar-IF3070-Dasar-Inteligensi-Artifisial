import { historySeries, stepLabel } from "./results.js";

export function drawHistory(canvas, result) {
  const series = historySeries(result).map((item) => ({
    ...item, points: item.values.map((y, x) => ({ x, y }))
  }));
  drawLines(canvas, series, stepLabel(result), "Objective");
}

export function drawLines(canvas, series, xLabel, yLabel, bounds = {}) {
  const width = Math.max(260, canvas.getBoundingClientRect().width);
  const height = 300;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const context = canvas.getContext("2d");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.fillStyle = "white";
  context.fillRect(0, 0, width, height);
  context.font = "12px system-ui";
  const points = series.flatMap((item) => item.points).filter((point) => Number.isFinite(point.y));
  if (!points.length) {
    context.fillStyle = "#536976";
    context.fillText(bounds.emptyMessage || "Tidak ada nilai terbatas untuk ditampilkan.", 16, 48);
    return;
  }
  let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
  for (const point of points) {
    xmin = Math.min(xmin, point.x); xmax = Math.max(xmax, point.x);
    ymin = Math.min(ymin, point.y); ymax = Math.max(ymax, point.y);
  }
  xmin = bounds.xMin ?? xmin;
  xmax = bounds.xMax ?? xmax;
  ymin = bounds.yMin ?? ymin;
  ymax = bounds.yMax ?? ymax;
  const lastStep = xmax;
  if (xmin === xmax) xmax = xmin + 1;
  if (ymin === ymax) {
    if (bounds.yMin !== undefined) ymax = ymin + 1;
    else { ymin -= 1; ymax += 1; }
  }
  const left = 75, right = width - 20, top = 30, bottom = height - 45;
  const x = (value) => left + (value - xmin) / (xmax - xmin) * (right - left);
  const y = (value) => bottom - (value - ymin) / (ymax - ymin) * (bottom - top);
  for (let tick = 0; tick <= 4; tick++) {
    const fraction = tick / 4;
    const value = ymin + fraction * (ymax - ymin);
    context.strokeStyle = "#e2e8f0";
    context.beginPath(); context.moveTo(left, y(value)); context.lineTo(right, y(value)); context.stroke();
    context.fillStyle = "#536976";
    context.textAlign = "right";
    context.fillText(Number(value.toPrecision(3)).toString(), left - 8, y(value) + 4);
  }
  context.textAlign = "center";
  const steps = new Set(Array.from({ length: 5 }, (_, index) => Math.round(xmin + index / 4 * (lastStep - xmin))));
  for (const step of steps) context.fillText(String(step), x(step), bottom + 20);
  context.textAlign = "left"; context.fillText(yLabel, left, 16);
  context.textAlign = "center"; context.fillText(xLabel, (left + right) / 2, height - 5);
  for (const item of series) {
    context.strokeStyle = item.color;
    context.fillStyle = item.color;
    context.lineWidth = 2;
    context.setLineDash(item.dashed ? [6, 4] : []);
    context.beginPath();
    let started = false;
    for (const point of item.points) {
      if (!Number.isFinite(point.y)) { started = false; continue; }
      if (started) context.lineTo(x(point.x), y(point.y));
      else context.moveTo(x(point.x), y(point.y));
      started = true;
    }
    context.stroke(); context.setLineDash([]);
    if (item.points.length < 80) {
      for (const point of item.points) {
        if (!Number.isFinite(point.y)) continue;
        context.beginPath(); context.arc(x(point.x), y(point.y), 2.5, 0, Math.PI * 2); context.fill();
      }
    }
  }
}
