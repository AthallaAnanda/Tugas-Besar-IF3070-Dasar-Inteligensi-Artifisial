from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from src.services.optimization import capabilities, run_optimization


ROOT = Path(__file__).resolve().parents[1]

app = Flask(
    __name__,
    static_folder=str(ROOT / "frontend"),
    static_url_path="/assets",
)
app.json.sort_keys = False


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "Backend Connected",
    })


@app.get("/api/capabilities")
def available_capabilities():
    return jsonify(capabilities())


@app.get("/api/sample")
def sample():
    import json

    with (ROOT / "data/sample/small.json").open(encoding="utf-8") as file:
        return jsonify(json.load(file))


def request_body():
    data = request.get_json()

    if not isinstance(data, dict):
        raise ValueError("Body request harus berupa object JSON")

    return data


@app.post("/api/optimize")
def optimize():
    return jsonify(run_optimization(request_body()))


@app.errorhandler(ValueError)
def invalid_value(error):
    return jsonify({
        "status": "error",
        "message": str(error),
    }), 400


@app.errorhandler(BadRequest)
def invalid_json(error):
    return jsonify({
        "status": "error",
        "message": "JSON tidak valid",
    }), 400


@app.errorhandler(UnsupportedMediaType)
def invalid_content_type(error):
    return jsonify({
        "status": "error",
        "message": "Gunakan Content-Type application/json",
    }), 415


if __name__ == "__main__":
    app.run(port=5000, debug=True)
