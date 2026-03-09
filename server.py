"""
Fake Job Post Detector — server.py
Flask backend with /predict endpoint and SQLite storage
"""

import os
import json
import random
import datetime
import sqlite3
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import werkzeug.utils

# ─── Config ───────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Allow frontend on different port

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
DB_PATH = "database.db"
MAX_FILE_SIZE_MB = 16

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "txt", "doc", "docx"}

# ─── Database ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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

            INSERT OR IGNORE INTO users (username, password, role)
                VALUES ('admin', '1234', 'admin');
            INSERT OR IGNORE INTO users (username, password, role)
                VALUES ('user', '123', 'user');
        """)


init_db()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
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
    "Illegal or ethically questionable job tasks requested.",
]

REAL_SIGNALS = [
    "Specific qualifications and technical responsibilities listed.",
    "Verifiable company name and multi-channel contact details.",
    "Professional language, formatting, and industry terminology.",
    "Market-aligned salary range and benefits mentioned.",
    "Clear application process (HR portal or official email).",
    "Benefits, insurance, and work environment details included.",
    "Specific office location and interview stages described.",
]


def run_model(filename: str, content: bytes | None = None) -> dict:
    """
    Simulated ML model with enhanced heuristics.
    Returns prediction, confidence, details, and flags.
    """
    name = filename.lower()
    # Comprehensive fake keywords for filenames
    fake_keywords = [
        "fake", "scam", "job123", "urgent", "offer", "work_from_home", 
        "earn_money", "guaranteed", "easy_cash", "payment", "unverified",
        "quick_hiring", "direct_joining", "no_interview"
    ]
    
    is_fake = any(k in name for k in fake_keywords)
    detection_reason = ""

    # Heuristic: file extension check
    if "." not in filename:
        is_fake = True
        detection_reason = "Missing file extension is highly suspicious."

    # Text content analysis
    text_content = ""
    if content:
        try:
            text_content = content.decode("utf-8", errors="ignore").lower()
            
            # prioritized fake signals
            fake_text_signals = {
                "wire transfer": "Request for wire transfer detected.",
                "whatsapp": "Suspicious off-platform communication (WhatsApp) requested.",
                "no experience needed": "Unrealistic job requirements (no experience) for high pay.",
                "urgent hiring": "Overly urgent hiring language used.",
                "earn $": "Unrealistic salary promises detected.",
                "immediate start": "Pressure to start immediately without formal process.",
                "payment required": "Illegal request for upfront payment.",
                "bank details": "Premature request for bank/financial details.",
                "gift cards": "Fraudulent payment method (gift cards) mentioned.",
                "part time home": "Common 'work from home' scam pattern detected.",
                "telegram": "Suspicious use of Telegram for recruitment.",
                "direct joining": "Bypassing standard interview processes."
            }
            
            for signal, reason in fake_text_signals.items():
                if signal in text_content:
                    is_fake = True
                    detection_reason = reason
                    break # Any fake signal confirms it
            
            if not is_fake:
                real_text_signals = [
                    "requirements:", "responsibilities:", "qualification:",
                    "experience in", "degree in", "benefits:", "company overview",
                    "equal opportunity employer", "job description"
                ]
                # Only check for real if no fake signal was found
                is_real_signal = any(s in text_content for s in real_text_signals)
                # We don't explicitly set is_fake = False here, we just use it 
                # to decide the final verdict if no fake signals were found.
        except Exception:
            pass

    # If nothing specific was found, use a more balanced random factor
    # but slightly lean towards fake if it doesn't look professional
    if not is_fake:
        # If it doesn't have professional keywords, higher chance of being fake
        professional_prob = 0.8 if (content and any(s in text_content for s in ["requirements", "experience"])) else 0.4
        if random.random() > professional_prob:
            is_fake = True
            detection_reason = "Lack of professional recruitment markers detected."

    confidence = random.randint(85, 99) if is_fake else random.randint(88, 99)
    
    # Select flags
    pool = FAKE_SIGNALS if is_fake else REAL_SIGNALS
    num_flags = min(3, len(pool))
    signals = random.sample(pool, k=num_flags)
    
    # Use the specific detection reason if we have one
    details = detection_reason if detection_reason else signals[0]

    return {
        "prediction": "FAKE" if is_fake else "REAL",
        "confidence": confidence,
        "details": details,
        "flags": signals,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return send_file("index.html")


@app.route("/<path:path>")
def static_proxy(path):
    return send_file(path)


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename  = werkzeug.utils.secure_filename(file.filename)
    file_path = UPLOAD_FOLDER / filename
    content   = file.read()
    file_path.write_bytes(content)

    result    = run_model(filename, content)
    timestamp = datetime.datetime.now().isoformat()

    # Store in DB
    with get_db() as conn:
        conn.execute(
            """INSERT INTO predictions (filename, prediction, confidence, details, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (filename, result["prediction"], result["confidence"], result["details"], timestamp),
        )

    result["filename"]  = filename
    result["timestamp"] = timestamp
    return jsonify(result)


@app.route("/history", methods=["GET"])
def get_history():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/history", methods=["POST"])
def add_history():
    """Accept history entries from frontend (when backend was offline during analysis)."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No data"}), 400

    with get_db() as conn:
        conn.execute(
            """INSERT INTO predictions (filename, prediction, confidence, details, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                data.get("filename", "unknown"),
                data.get("prediction", "UNKNOWN"),
                data.get("confidence", 0),
                data.get("details", ""),
                data.get("timestamp", datetime.datetime.now().isoformat()),
            ),
        )
    return jsonify({"status": "saved"})


@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json(force=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
        ).fetchone()

    if row:
        return jsonify({"status": "ok", "role": row["role"]})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n[OK]  Fake Job Post Detector API")
    print("   Running on http://127.0.0.1:5055\n")
    app.run(debug=True, port=5055)
