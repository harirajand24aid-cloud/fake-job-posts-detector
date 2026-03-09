# 🔍 Fake Job Post Detector

A responsive web application that detects fake job postings using AI/ML analysis.

---

## 📁 Project Structure

```
fake-job-detector/
├── index.html        ← Frontend entry point
├── style.css         ← Responsive design, ice-blue shimmer, green CTA
├── script.js         ← Login, upload, API calls, preview rendering
├── server.py         ← Flask backend with /predict endpoint
├── database.sql      ← SQL schema for users & predictions
├── requirements.txt  ← Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Open frontend (no backend needed)
Just open `index.html` in any browser. The app works standalone with simulated ML results.

### 2. Run the backend (optional, for real DB storage)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Flask server
python server.py
```

Server runs at: `http://127.0.0.1:5000`

---

## 🔑 Demo Login Credentials

| Role  | Username | Password |
|-------|----------|----------|
| Admin | `admin`  | `1234`   |
| User  | `user`   | `123`    |

---

## ✨ Features

- **Ice-blue shimmer navbar** with responsive hamburger menu
- **Admin / User login** with role selection
- **Drag & drop file upload** (image, PDF, TXT, DOC)
- **AI analysis** with confidence percentage and flags
- **Color-coded verdict** (green = REAL, red = FAKE)
- **Downloadable report** as .txt
- **Result history** stored in localStorage + SQLite
- **Fully responsive** — mobile, tablet, desktop

---

## 🛠 Tech Stack

| Layer    | Technology          |
|----------|---------------------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend  | Python Flask        |
| Database | SQLite (via sqlite3) |
| Fonts    | Cinzel, Cormorant Garamond, Raleway |

---

## 🔌 API Endpoints

| Method | Endpoint    | Description                   |
|--------|-------------|-------------------------------|
| POST   | `/predict`  | Upload file → get prediction  |
| GET    | `/history`  | Retrieve past predictions     |
| POST   | `/history`  | Save result from frontend     |
| POST   | `/login`    | Authenticate user             |

### `/predict` Response
```json
{
  "prediction": "FAKE",
  "confidence": 78,
  "details": "Suspicious wording and unrealistic salary detected.",
  "flags": ["Unrealistic salary promises detected.", "Vague job description."],
  "filename": "job_post.jpg",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## 🤖 Adding a Real ML Model

Replace the `run_model()` function in `server.py` with your own:

```python
import pickle

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

def run_model(filename, content=None):
    # Extract features from content
    features = extract_features(content)
    prediction = model.predict([features])[0]
    confidence = int(model.predict_proba([features]).max() * 100)
    return {
        "prediction": "FAKE" if prediction == 1 else "REAL",
        "confidence": confidence,
        "details": "Model-based analysis.",
        "flags": []
    }
```

---

## 📱 Responsive Breakpoints

- **Desktop**: > 768px — side-by-side result grid
- **Tablet**: 480–768px — stacked layout, hamburger nav
- **Mobile**: < 480px — single column, compact stats
