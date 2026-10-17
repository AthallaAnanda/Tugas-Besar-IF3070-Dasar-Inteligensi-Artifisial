async function request(path, payload) {
  const options = {};

  if (payload !== undefined) {
    options.method = "POST";
    options.headers = {
      "Content-Type": "application/json"
    };
    options.body = JSON.stringify(payload);
  }

  const response = await fetch("/api" + path, options);

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error("Backend mengirim respons yang tidak dapat dibaca");
  }

  if (!response.ok) {
    throw new Error(data.message || "Permintaan gagal");
  }

  return data;
}

export function getHealth() {
  return request("/health");
}

export function getCapabilities() {
  return request("/capabilities");
}

export function getSample() {
  return request("/sample");
}

export function optimize(payload) {
  return request("/optimize", payload);
}
