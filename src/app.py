"""Flask API, si penjaga pintu antara frontend dan backend.

Daftarnya begini.
GET /api/health buat cek backend hidup atau tidak.
POST /api/optimize buat jalanin satu optimasi.
POST /api/experiment buat jalanin eksperimen.

Target Tahap 0 sederhana saja. GET /api/health harus jawab
status success dengan pesan Backend Connected.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health():
    return jsonify({"status": "success", "message": "Backend Connected"}), 200


@app.post("/api/optimize")
def optimize():
    # TODO Tahap 3 Anggota 3, sambungkan ke services/optimization.py ya
    return jsonify({"status": "error", "message": "Not implemented yet"}), 501


@app.post("/api/experiment")
def experiment():
    # TODO Tahap 3 Anggota 3, sambungkan ke services/experiment.py ya
    return jsonify({"status": "error", "message": "Not implemented yet"}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
