import { download } from "./ui.js";

const SVG_NS = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);

  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }

  return element;
}

function colorFor(id) {
  let hash = 0;

  for (const character of id) {
    hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  }

  return "hsl(" + (hash % 360) + ", 58%, 72%)";
}

async function downloadStateJpg(svg, ship) {
  const width = 1600;
  const height = Math.max(1, Math.round(width * ship.length / ship.width));
  const copy = svg.cloneNode(true);
  copy.setAttribute("xmlns", SVG_NS);
  copy.setAttribute("width", String(width));
  copy.setAttribute("height", String(height));
  copy.setAttribute("font-family", "sans-serif");
  const source = new Blob([new XMLSerializer().serializeToString(copy)], { type: "image/svg+xml" });
  const url = URL.createObjectURL(source);
  try {
    const image = new Image();
    image.src = url;
    await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    context.fillStyle = "white";
    context.fillRect(0, 0, width, height);
    context.drawImage(image, 0, 0, width, height);
    const jpg = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.95));
    if (!jpg) throw new Error("Gagal membuat gambar JPG");
    download(`state-${ship.id}.jpg`, jpg);
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function renderState(state, container) {
  container.replaceChildren();

  const vehicles = new Map();

  for (const vehicle of state.vehicles) {
    vehicles.set(vehicle.id, vehicle);
  }

  for (const item of state.ships) {
    const card = document.createElement("div");
    card.className = "ship-card";

    const heading = document.createElement("h4");
    heading.textContent =
      item.ship.id + " (" +
      item.ship.width + " × " + item.ship.length + ")";

    const svg = svgElement("svg", {
      viewBox: "0 0 " + item.ship.width + " " + item.ship.length,
      role: "img",
      "aria-label": "Geladak " + item.ship.id
    });

    svg.classList.add("deck");

    for (let x = 0; x <= item.ship.width; x += 1) {
      svg.append(svgElement("line", {
        x1: x,
        y1: 0,
        x2: x,
        y2: item.ship.length,
        stroke: "#d4e2e9",
        "stroke-width": 0.02
      }));
    }

    for (let y = 0; y <= item.ship.length; y += 1) {
      svg.append(svgElement("line", {
        x1: 0,
        y1: y,
        x2: item.ship.width,
        y2: y,
        stroke: "#d4e2e9",
        "stroke-width": 0.02
      }));
    }

    let weight = 0;

    for (const placement of item.placements) {
      const vehicle = vehicles.get(placement.vehicle_id);
      const vertical = placement.orientation === "vertical";
      const width = vertical ? vehicle.length : vehicle.width;
      const length = vertical ? vehicle.width : vehicle.length;

      weight += vehicle.weight;

      const group = svgElement("g");
      const title = svgElement("title");

      title.textContent = [
        "Kendaraan " + vehicle.id,
        "Tarif pengiriman: " + vehicle.shipping_fee,
        "Berat: " + vehicle.weight,
        "Posisi: (" + placement.x + ", " + placement.y + ")"
      ].join("\n");

      const rectangle = svgElement("rect", {
        x: placement.x + 0.05,
        y: placement.y + 0.05,
        width: width - 0.1,
        height: length - 0.1,
        rx: 0.08,
        fill: colorFor(vehicle.id),
        stroke: "#455a70",
        "stroke-width": 0.025
      });

      const label = svgElement("text", {
        x: placement.x + width / 2,
        y: placement.y + length / 2,
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "font-size": Math.min(0.35, 0.8 / Math.max(vehicle.id.length, 1)),
        fill: "#162d40"
      });

      label.textContent = vehicle.id;
      group.append(title, rectangle, label);
      svg.append(group);
    }

    const details = document.createElement("p");
    details.textContent =
      item.placements.length + " kendaraan dimuat dengan total berat " +
      weight + " dari kapasitas " + item.ship.max_capacity + ".";

    const exportButton = document.createElement("button");
    exportButton.type = "button";
    exportButton.textContent = "Unduh state JPG";
    exportButton.onclick = async () => {
      exportButton.disabled = true;
      try {
        await downloadStateJpg(svg, item.ship);
        exportButton.textContent = "Unduh state JPG";
      } catch {
        exportButton.textContent = "Gagal mengunduh JPG, coba lagi";
      } finally {
        exportButton.disabled = false;
      }
    };
    card.append(heading, svg, details, exportButton);
    container.append(card);
  }

  const outsideLabel = document.createElement("p");
  outsideLabel.textContent = "Kendaraan di luar kapal";

  const tags = document.createElement("div");
  tags.className = "vehicle-tags";

  if (state.outside_vehicle_ids.length === 0) {
    tags.textContent = "Semua kendaraan diangkut";
  }

  for (const id of state.outside_vehicle_ids) {
    const tag = document.createElement("span");
    tag.className = "vehicle-tag";
    tag.textContent = id;
    tags.append(tag);
  }

  container.append(outsideLabel, tags);
}
