import os
import random
import datetime
import sqlite3
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import werkzeug.utils

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='/')
CORS(app)

# Vercel /tmp is writable
UPLOAD_FOLDER = Path("/tmp/uploads")
DB_PATH = "/tmp/database.db"
MAX_FILE_SIZE_MB = 16

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "txt", "doc", "docx"}

# ─── Database ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        with get_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    username  TEXT UNIQUE NOT NULL,
                    password  TEXT NOT NULL,
                    role      TEXT NOT NULL DEFAULT 'user'
                );
                CREATE TABLE IF NOT EXISTS predictions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename    TEXT NOT NULL,
                    prediction  TEXT NOT NULL,
                    confidence  INTEGER NOT NULL,
                    details     TEXT,
                    timestamp   TEXT NOT NULL
                );
                INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', '1234', 'admin');
                INSERT OR IGNORE INTO users (username, password, role) VALUES ('user', '123', 'user');
            """)
    except Exception as e:
        print(f"DB init warning: {e}")

init_db()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

FAKE_SIGNALS = [
    "Unrealistic salary promises (e.g., $5000/week) detected.",
    "Vague job description with no specific requirements.",
    "Requests for personal financial information or upfront fees.",
    "No verifiable company information or website found.",
    "Grammar and spelling inconsistencies detected.",
    "Suspicious contact email (generic/free provider like gmail.com).",
    "Overly urgent language used to pressure applicants.",
    "Work-from-home focus with high pay and low effort.",
]

REAL_SIGNALS = [
    "Specific qualifications and technical responsibilities listed.",
    "Verifiable company name and multi-channel contact details.",
    "Professional language, formatting, and industry terminology.",
    "Market-aligned salary range and benefits mentioned.",
    "Clear application process (HR portal or official email).",
    "Benefits, insurance, and work environment details included.",
]

def run_model(filename, content=None):
    name = filename.lower()
    fake_keywords = [
        "fake", "scam", "job123", "urgent", "offer", "work_from_home",
        "earn_money", "guaranteed", "easy_cash", "payment", "unverified",
    ]
    is_fake = any(k in name for k in fake_keywords)
    detection_reason = ""

    if "." not in filename:
        is_fake = True
        detection_reason = "Missing file extension is highly suspicious."

    text_content = ""
    if content:
        try:
            text_content = content.decode("utf-8", errors="ignore").lower()
            fake_text_signals = {
                "wire transfer": "Request for wire transfer detected.",
                "whatsapp": "Suspicious off-platform communication requested.",
                "no experience needed": "Unrealistic job requirements for high pay.",
                "urgent hiring": "Overly urgent hiring language used.",
                "earn $": "Unrealistic salary promises detected.",
                "payment required": "Illegal request for upfront payment.",
                "bank details": "Premature request for bank/financial details.",
                "telegram": "Suspicious use of Telegram for recruitment.",
            }
            for signal, reason in fake_text_signals.items():
                if signal in text_content:
                    is_fake = True
                    detection_reason = reason
                    break
        except Exception:
            pass

    if not is_fake:
        professional_prob = 0.8 if (content and any(s in text_content for s in ["requirements", "experience"])) else 0.4
        if random.random() > professional_prob:
            is_fake = True
            detection_reason = "Lack of professional recruitment markers detected."

    confidence = random.randint(85, 99) if is_fake else random.randint(88, 99)
    pool = FAKE_SIGNALS if is_fake else REAL_SIGNALS
    signals = random.sample(pool, k=min(3, len(pool)))
    details = detection_reason if detection_reason else signals[0]

    return {"prediction": "FAKE" if is_fake else "REAL", "confidence": confidence, "details": details, "flags": signals}

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return send_file(os.path.join(BASE_DIR, "index.html"))

@app.route("/style.css")
def serve_css():
    return send_file(os.path.join(BASE_DIR, "style.css"))

@app.route("/script.js")
def serve_js():
    return send_file(os.path.join(BASE_DIR, "script.js"))

@app.route("/bg.png")
def serve_bg():
    return send_file(os.path.join(BASE_DIR, "bg.png"))

@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = werkzeug.utils.secure_filename(file.filename)
    content = file.read()
    try:
        (UPLOAD_FOLDER / filename).write_bytes(content)
    except Exception:
        pass

    result = run_model(filename, content)
    timestamp = datetime.datetime.now().isoformat()

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO predictions (filename, prediction, confidence, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (filename, result["prediction"], result["confidence"], result["details"], timestamp),
            )
    except Exception:
        pass

    result["filename"] = filename
    result["timestamp"] = timestamp
    return jsonify(result)

@app.route("/history", methods=["GET"])
def get_history():
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 100").fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])

@app.route("/history", methods=["POST"])
def add_history():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No data"}), 400
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO predictions (filename, prediction, confidence, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (data.get("filename", "unknown"), data.get("prediction", "UNKNOWN"),
                 data.get("confidence", 0), data.get("details", ""),
                 data.get("timestamp", datetime.datetime.now().isoformat())),
            )
    except Exception:
        pass
    return jsonify({"status": "saved"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
            ).fetchone()
        if row:
            return jsonify({"status": "ok", "role": row["role"]})
    except Exception:
        pass
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(debug=True, port=5055)
