export function drawHistory(canvas, result, activeIteration = 0) {
  const width = Math.max(300, canvas.getBoundingClientRect().width);
  const height = 280;
  const ratio = window.devicePixelRatio || 1;

  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);

  const context = canvas.getContext("2d");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);

  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);

  const left = 60;
  const right = width - 20;
  const top = 20;
  const bottom = height - 40;

  let minimum = Infinity;
  let maximum = -Infinity;

  for (const series of [result.history, result.best_history]) {
    for (const value of series) {
      minimum = Math.min(minimum, value);
      maximum = Math.max(maximum, value);
    }
  }

  if (minimum === maximum) {
    minimum -= 1;
    maximum += 1;
  }

  const lastIteration = Math.max(1, result.history.length - 1);

  function xPosition(iteration) {
    return left + iteration / lastIteration * (right - left);
  }

  function yPosition(value) {
    return bottom -
      (value - minimum) / (maximum - minimum) * (bottom - top);
  }

  context.font = "12px system-ui";
  context.fillStyle = "#64748b";
  context.strokeStyle = "#e2e8f0";
  context.lineWidth = 1;

  for (let tick = 0; tick <= 4; tick += 1) {
    const fraction = tick / 4;
    const value = minimum + fraction * (maximum - minimum);
    const y = yPosition(value);

    context.beginPath();
    context.moveTo(left, y);
    context.lineTo(right, y);
    context.stroke();

    context.textAlign = "right";
    context.fillText(value.toFixed(1), left - 8, y + 4);

    const iteration = Math.round(fraction * (result.history.length - 1));
    context.textAlign = "center";
    context.fillText(String(iteration), xPosition(iteration), bottom + 22);
  }

  function line(values, color, dashed) {
    context.strokeStyle = color;
    context.lineWidth = 2;
    context.setLineDash(dashed ? [6, 4] : []);
    context.beginPath();

    values.forEach(function (value, index) {
      const x = xPosition(index);
      const y = yPosition(value);

      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });

    context.stroke();
    context.setLineDash([]);

    if (values.length === 1) {
      context.fillStyle = color;
      context.beginPath();
      context.arc(xPosition(0), yPosition(values[0]), 3, 0, Math.PI * 2);
      context.fill();
    }
  }

  line(result.history, "#126c8c", false);
  line(result.best_history, "#d97706", true);

  const selected = Math.max(
    0,
    Math.min(activeIteration, result.history.length - 1)
  );

  context.strokeStyle = "#8b5cf6";
  context.setLineDash([3, 4]);
  context.beginPath();
  context.moveTo(xPosition(selected), top);
  context.lineTo(xPosition(selected), bottom);
  context.stroke();
  context.setLineDash([]);

  context.fillStyle = "#64748b";
  context.textAlign = "center";
  context.fillText("Iterasi", (left + right) / 2, height - 4);
}