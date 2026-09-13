import pytest

from src.predict import predict_url, get_model_metrics


def test_predict_returns_expected_shape():
    result = predict_url("https://www.wikipedia.org/wiki/Phishing")
    assert set(["url", "verdict", "risk_score", "confidence", "features", "top_contributors"]) <= set(result.keys())
    assert result["verdict"] in {"Legitimate", "Suspicious", "Phishing"}
    assert 0 <= result["risk_score"] <= 100
    assert 0 <= result["confidence"] <= 100


def test_predict_invalid_url_raises_value_error():
    with pytest.raises(ValueError):
        predict_url("")


def test_top_contributors_bounded():
    result = predict_url("http://secure-paypal-login.verify-account.tk/confirm")
    assert 1 <= len(result["top_contributors"]) <= 5


def test_ip_based_url_scores_higher_risk_than_known_domain():
    ip_result = predict_url("http://192.168.5.7/account/login.php")
    clean_result = predict_url("https://www.python.org/downloads/")
    assert ip_result["risk_score"] >= clean_result["risk_score"]


def test_model_metrics_available_after_training():
    metrics = get_model_metrics()
    assert "random_forest" in metrics
    assert "selected_model" in metrics
    assert metrics["random_forest"]["accuracy"] > 0.5
