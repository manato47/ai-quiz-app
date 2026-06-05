import os
import base64
import io
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import openpyxl
from datetime import datetime

app = Flask(__name__, static_folder="static")
CORS(app)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/solve", methods=["POST"])
def solve():
    question = request.form.get("question", "").strip()
    image_file = request.files.get("image")

    if not question and not image_file:
        return jsonify({"error": "問題を入力するか、画像を追加してください"}), 400

    parts = []

    if image_file:
        if image_file.mimetype not in ALLOWED_IMAGE_TYPES:
            return jsonify({"error": "対応していない画像形式です（JPEG / PNG / GIF / WebP）"}), 400
        image_data = image_file.read()
        parts.append({"mime_type": image_file.mimetype, "data": image_data})

    parts.append(question if question else "この画像の問題を解いてください。")

    response = model.generate_content(parts)
    answer = response.text
    snippet = question[:10] if question else "（画像のみ）"

    return jsonify({"answer": answer, "snippet": snippet})


@app.route("/save", methods=["POST"])
def save():
    snippet = request.form.get("snippet", "")
    answer = request.form.get("answer", "")
    has_image = request.form.get("has_image", "なし")
    excel_file = request.files.get("excel")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if excel_file:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        filename = excel_file.filename
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "回答記録"
        ws.append(["日時", "問題（先頭10文字）", "画像あり", "回答"])
        for col, width in [("A", 20), ("B", 20), ("C", 10), ("D", 60)]:
            ws.column_dimensions[col].width = width
        filename = "results.xlsx"

    ws.append([now, snippet, has_image, answer])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
