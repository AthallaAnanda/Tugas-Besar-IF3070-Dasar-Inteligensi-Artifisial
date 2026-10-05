// Halo, ini api.js.
// Tugasnya sederhana, jadi kurir yang ngobrol sama Flask API.
// Kalau mau ganti alamat backend, ubah API_BASE di bawah ini saja.
const API_BASE = "http://localhost:5000/api";

// Cek backend masih hidup atau tidak.
async function checkHealth() {
  const res = await fetch(API_BASE + "/health");
  return res.json();
}

// Kirim config optimasi ke backend lalu tunggu jawabannya.
async function runOptimization(payload) {
  const res = await fetch(API_BASE + "/optimize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}
