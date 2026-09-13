"""
Central configuration for PhishGuard.

All paths are resolved relative to the project root so the project runs
correctly regardless of the current working directory or the machine it is
cloned onto (no hardcoded absolute paths).
"""

from pathlib import Path

# Project root = two levels up from this file (src/config.py -> project root)
ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "phishing_legitimate_full.csv"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MODELS_DIR = ROOT_DIR / "models"
MODEL_PATH = MODELS_DIR / "phishing_model.joblib"
SCALER_PATH = MODELS_DIR / "scaler.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"
FEATURE_IMPORTANCE_PATH = MODELS_DIR / "feature_importance.json"

ASSETS_DIR = ROOT_DIR / "assets"

RANDOM_STATE = 42
TEST_SIZE = 0.2
VAL_SIZE = 0.1  # taken out of the remaining training data

# The 26 features below are all derivable directly from a URL string alone
# (hostname/path/query lexical + structural properties). They are the subset
# of the original 48-feature UCI/Mendeley "Phishing Dataset for Machine
# Learning" schema that does NOT require fetching and rendering the live
# webpage (see README > Feature Engineering for the full rationale).
URL_ONLY_FEATURES = [
    "NumDots",
    "SubdomainLevel",
    "PathLevel",
    "UrlLength",
    "NumDash",
    "NumDashInHostname",
    "AtSymbol",
    "TildeSymbol",
    "NumUnderscore",
    "NumPercent",
    "NumQueryComponents",
    "NumAmpersand",
    "NumHash",
    "NumNumericChars",
    "NoHttps",
    "RandomString",
    "IpAddress",
    "DomainInSubdomains",
    "DomainInPaths",
    "HttpsInHostname",
    "HostnameLength",
    "PathLength",
    "QueryLength",
    "DoubleSlashInPath",
    "NumSensitiveWords",
    "EmbeddedBrandName",
]

TARGET_COLUMN = "CLASS_LABEL"  # 1 = phishing, 0 = legitimate in the source dataset
