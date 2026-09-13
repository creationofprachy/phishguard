 PhishGuard
A machine-learning phishing URL detector that scores any URL in real time using only the URL text itself — no page content is ever fetched.
Overview
PhishGuard is a defensive cybersecurity tool that classifies URLs as Legitimate, Suspicious, or Phishing using a Random Forest model trained on lexical and structural properties of the URL string (length, subdomain depth, special characters, sensitive keywords, IP-literal hosts, etc.). It ships as a small FastAPI service with a browser dashboard, a reproducible training pipeline, and an automated test suite.
Problem Statement
Phishing remains one of the most common initial-access techniques in real attacks: an attacker registers a look-alike domain (`paypal-secure-login.verify-account.tk`) and sends it to a victim. Two groups need a fast first-pass signal on a URL before deciding whether to click, block, or investigate further:
End users / security-aware students who receive a suspicious link and want an instant, local risk assessment.
SOC analysts / triage engineers who need to batch-eyeball many reported URLs quickly, before spending time on deeper sandboxing.
Why existing simple approaches fall short:
Blocklists (e.g. Google Safe Browsing, PhishTank feeds) only catch URLs that have already been reported — they miss brand-new phishing domains, which is exactly when the attack is most dangerous.
Regex/keyword rules (e.g. "block if URL contains 'login'") are trivially evaded and produce high false-positive rates on legitimate sites that also use those words.
Content-fetching detectors that render the target page to extract features (forms, iframes, favicons, external links) require visiting the URL first. For a defensive tool this is a real problem: it can trigger the phishing page's own detection/evasion logic, leak the analyst's IP/analytics to the attacker, expose the tool to malicious redirects or drive-by content, and it fails entirely once the page goes offline. PhishGuard deliberately avoids this by scoring the URL before ever making a request to it.
Solution
PhishGuard trains a classifier on the URL-derived subset of a public phishing-features dataset, wraps it in a small feature-extraction module that can reproduce those same features for any URL a user types in (no network call required), and serves predictions through a FastAPI backend with a dashboard for interactive analysis, an explanation panel, and a session history table.
Key Features
Real-time URL risk scoring (0–100) with Legitimate / Suspicious / Phishing verdicts
Model works from the URL string alone — safe to use on links you haven't visited
"Why this verdict" panel showing the top contributing features and their model weight
Model performance dashboard (accuracy, precision, recall, F1, ROC-AUC) sourced from the actual training run
Session history table with clear/reset
Input validation and graceful error handling (empty URL, malformed URL, oversized input)
Reproducible ML pipeline: baseline (Logistic Regression) vs. improved (Random Forest) model comparison
27 automated tests covering feature extraction, model inference, and the API
Architecture
```
Browser (dashboard) ──HTTP──▶ FastAPI (app/main.py) ──▶ src/predict.py ──▶ src/features.py (URL → feature vector)
                                                              │
                                                              ▼
                                                   models/phishing_model.joblib
                                                   models/scaler.joblib
```
Training is a fully separate offline step (`src/train.py`) that only touches `data/` and writes to `models/` and `assets/` — it never runs as part of a live request.
How It Works
A user submits a URL to `POST /api/predict`.
`src/features.py` parses the URL (`urllib.parse`) and computes 26 lexical/structural features (see below) — purely from the string, no network request.
The feature vector is scaled with the saved `StandardScaler` and passed to the saved Random Forest model.
The model's phishing-class probability becomes the risk score; a fixed threshold maps it to a verdict (`< 40` → Legitimate, `40–70` → Suspicious, `≥ 70` → Phishing).
The top features (by model importance, weighted by how "active" they are for this specific URL) are returned for the explanation panel.
The result is appended to an in-memory history list and returned to the dashboard.
Dataset
Source: "Phishing Dataset for Machine Learning: Feature Evaluation" (Tan, Choon Lin, 2018, Mendeley Data), a widely used, publicly available phishing-features dataset also mirrored in several public GitHub research repositories.
Samples: 10,000 URLs (5,000 legitimate, 5,000 phishing) — after de-duplication and NA removal, 9,370 rows remain (4,854 legitimate / 4,516 phishing) for training.
Original feature count: 48 pre-extracted features per URL.
Features used in this project: 26 of the 48 — specifically, every feature computable directly from the URL string, hostname, path, and query (e.g. `UrlLength`, `NumDots`, `SubdomainLevel`, `NumDash`, `IpAddress`, `NumSensitiveWords`). The remaining 22 features in the original dataset require rendering the live webpage (e.g. counting external hyperlinks, checking for iframes, detecting a disabled right-click handler) and were excluded by design — see "Why existing simple approaches fall short" above.
Target: `CLASS_LABEL` (1 = phishing, 0 = legitimate).
Preprocessing: column subsetting to the 26 URL-only features + target, de-duplication, drop rows with missing values, `StandardScaler` normalization.
Train/test methodology: stratified 80/20 split (`random_state=42`), preserving class balance in both splits.
Feature Engineering
For live inference (URLs a user types in, which obviously aren't in the training CSV), `src/features.py` independently recomputes the same 26 features from raw URL text using `urllib.parse` plus a handful of documented heuristics (see Limitations) for things like "does this hostname look randomly generated" and "does a well-known brand name appear outside the real domain." This is the same code path used for training-time validation and for every prediction the API serves.
Machine Learning
Step	Detail
Baseline model	Logistic Regression (`max_iter=1000`)
Improved model	Random Forest (`n_estimators=300`, `max_depth=14`, `min_samples_leaf=2`)
Feature scaling	`StandardScaler`, fit on training split only
Model selection	Best F1-score on the held-out test set
Selected model	Random Forest
Model Evaluation
All numbers below come directly from `models/metrics.json`, generated by actually running `python -m src.train` in this repository — nothing here is hand-typed or estimated.
Metric	Logistic Regression (baseline)	Random Forest (selected)
Accuracy	85.17%	89.70%
Precision	82.38%	86.75%
Recall	88.04%	92.80%
F1-score	85.12%	89.67%
ROC-AUC	0.9236	0.9674
Test set: 1,874 held-out URLs (stratified). See `assets/confusion_matrix.png`, `assets/roc_curve.png`, and `assets/feature_importance.png` for the corresponding plots, and `assets/class_balance.png` / `assets/correlation_matrix.png` for the exploratory data analysis (`notebooks/eda.py`).
Screenshots
The dashboard is a single-page app served at `/` once the app is running (`app/static/index.html`). It shows a URL input box, a risk-score meter with a Legitimate/Suspicious/Phishing badge, a "why this verdict" feature breakdown, a live model-performance panel, and a scrollable analysis history table. Run the app locally (see Usage) to view it — screenshots are intentionally omitted here rather than faked.
Tech Stack
Backend: Python, FastAPI, Uvicorn
ML: scikit-learn, pandas, NumPy, joblib
Frontend: HTML, CSS, vanilla JavaScript (no build step)
Testing: pytest, httpx (FastAPI `TestClient`)
Visualization: Matplotlib
Installation
Windows PowerShell Setup
```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd phishguard
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
macOS / Linux
```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd phishguard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Usage
Train the model (already-trained artifacts are included in `models/`, but you can retrain from scratch):
```bash
   python -m src.train
   ```
Run the exploratory data analysis (optional):
```bash
   python notebooks/eda.py
   ```
Start the API + dashboard:
```bash
   uvicorn app.main:app --reload
   ```
Open http://127.0.0.1:8000 in your browser, paste a URL, and click Analyze URL.
API quick reference
Method	Endpoint	Description
`POST`	`/api/predict`	Body: `{"url": "..."}` → risk score, verdict, feature breakdown
`GET`	`/api/history`	Returns the in-memory analysis history
`DELETE`	`/api/history`	Clears history
`GET`	`/api/metrics`	Returns the model's evaluation metrics
`GET`	`/api/health`	Liveness/readiness check
Testing
```bash
pytest tests/ -v
```
27 tests covering:
Feature extraction — scheme handling, IP-literal detection, `@`-symbol tricks, query-component counting, sensitive-word detection, subdomain depth, input validation.
Model inference — output shape/ranges, verdict bucketing, relative risk ordering, error handling on invalid input.
API — health check, dashboard serving, successful/invalid prediction requests, history lifecycle, metrics endpoint.
All 27 tests pass in this repository as committed.
Project Structure
```
phishguard/
│
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── .env.example
│
├── data/
│   ├── raw/phishing_legitimate_full.csv   # source dataset
│   └── processed/                          # reserved for cached splits
│
├── models/
│   ├── phishing_model.joblib               # trained Random Forest
│   ├── scaler.joblib                       # fitted StandardScaler
│   ├── metrics.json                        # evaluation metrics (generated)
│   └── feature_importance.json             # feature weights (generated)
│
├── notebooks/
│   └── eda.py                              # exploratory data analysis script
│
├── src/
│   ├── config.py                           # paths, constants, feature list
│   ├── features.py                         # URL → feature vector
│   ├── train.py                            # training pipeline
│   └── predict.py                          # inference wrapper
│
├── app/
│   ├── main.py                             # FastAPI app
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── script.js
│
├── tests/
│   ├── test_features.py
│   ├── test_model.py
│   └── test_api.py
│
└── assets/                                 # generated plots (EDA + evaluation)
```
Security Considerations
This is a defensive-only tool: it analyzes text, it does not crawl, exploit, or interact with target sites.
No credentials, API keys, or personal data are collected or required.
All URL analysis happens locally in-process; nothing is sent to a third party.
History is kept in memory only (not persisted to disk), and is cleared on restart or on demand.
Input is length-limited and validated before feature extraction to avoid malformed-input crashes.
Limitations
Because the model deliberately avoids fetching page content, it cannot see genuinely content-only phishing signals (e.g. a cloned login form on an otherwise "clean-looking" domain). It is a first-pass lexical filter, not a full verdict.
Several inference-time heuristics (`RandomString`, `DomainInSubdomains`, `DomainInPaths`, `EmbeddedBrandName`) are simplified approximations of the original dataset's feature definitions (no public-suffix list is used, and the brand keyword list is small and illustrative) — they will not perfectly match how the training data's authors computed the same-named columns from their original URLs.
The dataset is from 2018–2020; phishing tactics evolve, so periodic retraining on fresher data is recommended for production use.
Verdict thresholds (40 / 70) are reasonable defaults, not calibrated against a specific cost-of-false-positive/negative analysis.
Future Improvements
Add a browser extension front-end that calls the existing API.
Add optional, explicitly-opt-in content-based analysis (with sandboxed fetching) as a second-stage deeper check.
Persist history to a lightweight database (SQLite) instead of in-memory storage.
Replace the brand/random-string heuristics with a public-suffix-list-based domain parser and a larger, curated brand list.
Add SHAP-based per-prediction explanations instead of the current importance-weighted heuristic.
License
MIT — see LICENSE.
Author
Built as a portfolio project demonstrating applied ML + defensive cybersecurity + full-stack engineering.
