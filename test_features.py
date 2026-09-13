import pytest

from src.config import URL_ONLY_FEATURES
from src.features import extract_features


def test_returns_all_expected_feature_keys_in_order():
    feats = extract_features("https://example.com/path?a=1&b=2")
    assert list(feats.keys()) == URL_ONLY_FEATURES


def test_empty_url_raises():
    with pytest.raises(ValueError):
        extract_features("")


def test_none_url_raises():
    with pytest.raises(ValueError):
        extract_features(None)


def test_https_detected_correctly():
    https_feats = extract_features("https://example.com")
    http_feats = extract_features("http://example.com")
    assert https_feats["NoHttps"] == 0
    assert http_feats["NoHttps"] == 1


def test_ip_address_hostname_detected():
    feats = extract_features("http://192.168.1.1/login")
    assert feats["IpAddress"] == 1


def test_domain_hostname_not_flagged_as_ip():
    feats = extract_features("http://example.com/login")
    assert feats["IpAddress"] == 0


def test_at_symbol_detected():
    feats = extract_features("http://example.com@evil.com/path")
    assert feats["AtSymbol"] == 1


def test_query_components_counted():
    feats = extract_features("http://example.com/x?a=1&b=2&c=3")
    assert feats["NumQueryComponents"] == 3
    assert feats["NumAmpersand"] == 2


def test_no_query_components_when_no_query():
    feats = extract_features("http://example.com/path")
    assert feats["NumQueryComponents"] == 0


def test_sensitive_words_counted():
    feats = extract_features("http://example.com/secure/login/verify-account")
    assert feats["NumSensitiveWords"] >= 3


def test_subdomain_level_counts_extra_labels():
    feats = extract_features("http://a.b.example.com/path")
    assert feats["SubdomainLevel"] == 2


def test_no_subdomains_gives_zero():
    feats = extract_features("http://example.com/path")
    assert feats["SubdomainLevel"] == 0


def test_url_without_scheme_is_handled():
    feats = extract_features("example.com/path")
    assert feats["HostnameLength"] > 0


def test_numeric_char_count():
    feats = extract_features("http://example.com/id123")
    assert feats["NumNumericChars"] == 3
