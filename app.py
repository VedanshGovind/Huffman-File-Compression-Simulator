import base64
import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

import compressor

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB upload cap

COMPRESSED_EXT = ".hcm"


@app.route("/")
def index():
    """Upload page (HTML form to pick a file)."""
    return render_template("index.html")


def _read_text_file(file_storage):
    """Read an upload as text: UTF-8 first, lossless latin-1 fallback."""
    raw = file_storage.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


@app.route("/compress", methods=["POST"])
def compress():
    """Compress the uploaded file.

    Returns JSON with the compression stats, the character code table, and
    the compressed file as base64 (the browser turns it into a download).
    """
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"error": "No file uploaded — please choose a text file first."}), 400

    text = _read_text_file(file)
    compressed, stats = compressor.compress_text(text)

    base, _ = os.path.splitext(file.filename)
    return jsonify({
        "ok": True,
        "filename": file.filename,
        "compressed_name": base + COMPRESSED_EXT,
        "compressed_size": len(compressed),
        "compressed_base64": base64.b64encode(compressed).decode("ascii"),
        "stats": stats,
    })


@app.route("/decompress", methods=["POST"])
def decompress():
    """Decompress an uploaded .hcm file and return the original text."""
    file = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify({"error": "No file uploaded — please choose a .hcm compressed file first."}), 400

    data = file.read()
    try:
        text = compressor.decompress_bytes(data)
    except ValueError as exc:
        return jsonify({"error": f"Could not decompress: {exc}"}), 400

    return jsonify({
        "ok": True,
        "text": text,
        "compressed_size": len(data),
        "original_size": len(text.encode("utf-8")),
    })


@app.errorhandler(RequestEntityTooLarge)
def too_large(_e):
    return jsonify({"error": "File is too large (32 MB max for this demo)."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
