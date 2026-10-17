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

function placementMap(state) {
  const result = new Map();

  if (!state) {
    return result;
  }

  for (const item of state.ships) {
    for (const placement of item.placements) {
      result.set(placement.vehicle_id, JSON.stringify(placement));
    }
  }

  return result;
}

export function materializeFrame(initialState, frame) {
  const loaded = new Set();

  for (const placement of frame.placements) {
    loaded.add(placement.vehicle_id);
  }

  return {
    vehicles: initialState.vehicles,
    ships: initialState.ships.map(function (item) {
      return {
        ship: item.ship,
        placements: frame.placements.filter(function (placement) {
          return placement.ship_id === item.ship.id;
        })
      };
    }),
    outside_vehicle_ids: initialState.vehicles
      .filter(function (vehicle) {
        return !loaded.has(vehicle.id);
      })
      .map(function (vehicle) {
        return vehicle.id;
      }),
    value: frame.objective_value
  };
}

export function renderState(state, container, previousState = null) {
  container.replaceChildren();

  const vehicles = new Map();

  for (const vehicle of state.vehicles) {
    vehicles.set(vehicle.id, vehicle);
  }

  const previous = placementMap(previousState);

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

      const changed =
        previousState !== null &&
        previous.get(vehicle.id) !== JSON.stringify(placement);

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
        stroke: changed ? "#e25822" : "#455a70",
        "stroke-width": changed ? 0.09 : 0.025
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

    card.append(heading, svg, details);
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
