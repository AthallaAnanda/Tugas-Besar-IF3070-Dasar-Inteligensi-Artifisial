// Halo, ini app.js.
// Tugasnya ngatur UI. Baca pilihan user, panggil API, lalu tampilkan hasil.
// TODO Tahap 4 Anggota 3, lengkapi integrasi optimize dan experiment ya.

// Tombol run ditekan, nanti jalanin optimasi dari sini.
var runBtn = document.getElementById("run-btn");
if (runBtn) {
  runBtn.addEventListener("click", function () {
    alert("Belum jadi ya, sabar dulu sampai Tahap 3 dan 4 beres.");
  });
}

// Waktu halaman dibuka, langsung sapa backend dulu.
async function sayHello() {
  try {
    var health = await checkHealth();
    document.getElementById("backend-status").textContent =
      health.message || JSON.stringify(health);
  } catch (e) {
    document.getElementById("backend-status").textContent = "Backend disconnected";
  }
}
sayHello();
