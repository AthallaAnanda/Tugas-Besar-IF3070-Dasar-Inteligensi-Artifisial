// Halo, ini visualization.js.
// Tugasnya gambar kondisi kapal di layar, baik awal maupun akhir.
// Nanti ada gambar deck, posisi kendaraan, sama putarannya.
// TODO Tahap 4 Anggota 3, lengkapi gambar deck dan dukung multi ship ya.
function renderShip(state, containerId) {
  // Untuk sekarang tampilkan mentah dulu biar kelihatan isinya.
  document.getElementById(containerId).textContent = JSON.stringify(state);
}
