"""
URL feature extraction.

Computes the 26 URL-only lexical/structural features (see
`config.URL_ONLY_FEATURES`) directly from a raw URL string, with no network
request required. This mirrors (with documented approximations -- see
README > Limitations) the URL-derived subset of the feature schema from the
"Phishing Dataset for Machine Learning: Feature Evaluation" (Tan, 2018),
which is the schema used by the training dataset in data/raw/.

Because every feature here comes purely from the URL text itself, the same
function is used to prepare training-time sanity checks and to score URLs
submitted by a user at inference time -- the model never has to fetch a
potentially malicious page to classify it.
"""

import math
import re
from dataclasses import dataclass, asdict
from urllib.parse import urlsplit

from src.config import URL_ONLY_FEATURES

SENSITIVE_WORDS = [
    "secure", "account", "update", "login", "signin", "verify",
    "confirm", "banking", "password", "suspend", "webscr", "ebayisapi",
    "security", "billing", "unlock", "recover",
]

# Small, illustrative set of frequently-impersonated brand keywords used only
# to flag brand-name misuse in the hostname/path (see Limitations in README
# for why this heuristic is intentionally simple).
BRAND_KEYWORDS = [
    "paypal", "apple", "microsoft", "amazon", "google", "facebook",
    "netflix", "instagram", "whatsapp", "chase", "wellsfargo", "irs",
    "dhl", "outlook", "office365", "linkedin", "bankofamerica",
]

_IPV4_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


@dataclass
class URLParts:
    full_url: str
    scheme: str
    hostname: str
    path: str
    query: str


def _split_url(url: str) -> URLParts:
    url = url.strip()
    # Default to http:// if no scheme is given so urlsplit parses correctly.
    if "://" not in url:
        url = "http://" + url
    parts = urlsplit(url)
    hostname = parts.hostname or ""
    return URLParts(
        full_url=url,
        scheme=parts.scheme or "",
        hostname=hostname,
        path=parts.path or "",
        query=parts.query or "",
    )


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def _guess_domain_label(hostname: str) -> str:
    """Best-effort second-level-domain label, e.g. 'paypal' from
    'login.paypal.com'. Uses a simple heuristic (second-to-last label) rather
    than a public-suffix list, which is a documented simplification."""
    labels = hostname.split(".")
    if len(labels) >= 2:
        return labels[-2]
    return hostname


def _subdomain_labels(hostname: str) -> list:
    labels = hostname.split(".")
    if len(labels) <= 2:
        return []
    return labels[:-2]


def _looks_random(label: str) -> bool:
    if len(label) < 8:
        return False
    letters = [c for c in label if c.isalpha()]
    if not letters:
        return True
    vowels = sum(1 for c in letters if c.lower() in "aeiou")
    vowel_ratio = vowels / len(letters)
    entropy = _shannon_entropy(label)
    return vowel_ratio < 0.25 or entropy > 3.6


def extract_features(url: str) -> dict:
    """Extract the 26 URL-only features for a single URL string.

    Returns a dict keyed by the exact column names in
    `config.URL_ONLY_FEATURES`, in the same order, so it can be turned
    directly into a model-ready feature vector.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    parts = _split_url(url)
    full_url = parts.full_url
    hostname = parts.hostname.lower()
    path = parts.path
    query = parts.query

    domain_label = _guess_domain_label(hostname)
    sub_labels = _subdomain_labels(hostname)

    features = {
        "NumDots": full_url.count("."),
        "SubdomainLevel": len(sub_labels),
        "PathLevel": path.count("/"),
        "UrlLength": len(full_url),
        "NumDash": full_url.count("-"),
        "NumDashInHostname": hostname.count("-"),
        "AtSymbol": int("@" in full_url),
        "TildeSymbol": int("~" in full_url),
        "NumUnderscore": full_url.count("_"),
        "NumPercent": full_url.count("%"),
        "NumQueryComponents": len([q for q in query.split("&") if q]) if query else 0,
        "NumAmpersand": full_url.count("&"),
        "NumHash": full_url.count("#"),
        "NumNumericChars": sum(c.isdigit() for c in full_url),
        "NoHttps": int(parts.scheme.lower() != "https"),
        "RandomString": int(_looks_random(domain_label)),
        "IpAddress": int(bool(_IPV4_RE.match(hostname))),
        "DomainInSubdomains": int(
            any(lbl in BRAND_KEYWORDS for lbl in sub_labels)
        ),
        "DomainInPaths": int(
            any(brand in path.lower() for brand in BRAND_KEYWORDS)
        ),
        "HttpsInHostname": int("https" in hostname.replace("www.", "")),
        "HostnameLength": len(hostname),
        "PathLength": len(path),
        "QueryLength": len(query),
        "DoubleSlashInPath": int("//" in path),
        "NumSensitiveWords": sum(
            1 for w in SENSITIVE_WORDS if w in full_url.lower()
        ),
        "EmbeddedBrandName": int(
            any(
                brand in (path.lower() + " " + " ".join(sub_labels))
                and brand != domain_label.lower()
                for brand in BRAND_KEYWORDS
            )
        ),
    }

    # Preserve a fixed, deterministic column order matching training data.
    return {name: features[name] for name in URL_ONLY_FEATURES}


def extract_feature_vector(url: str) -> list:
    """Return the feature values only, in `URL_ONLY_FEATURES` order."""
    feats = extract_features(url)
    return [feats[name] for name in URL_ONLY_FEATURES]
