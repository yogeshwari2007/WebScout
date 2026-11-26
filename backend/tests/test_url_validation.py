import ipaddress
import pytest
from app.utils.url_validation import (
    validate_url,
    is_ip_restricted,
    normalize_canonical_url,
)


def test_valid_public_urls():
    """Verifies that standard valid HTTP and HTTPS public URLs pass validation."""
    valid_cases = [
        "https://example.com",
        "http://example.org/path/to/page",
        "https://en.wikipedia.org/wiki/Main_Page",
        "https://news.ycombinator.com/item?id=123",
        "https://www.apple.com/macbook-air/",
    ]
    for url in valid_cases:
        is_valid, err, canonical = validate_url(url, resolve_dns=False)
        assert is_valid is True, f"Failed for {url}: {err}"
        assert err is None
        assert canonical is not None


def test_reject_dangerous_schemes():
    """Ensures file, javascript, data, and ftp schemes are strictly blocked."""
    invalid_schemes = [
        "file:///etc/passwd",
        "file://C:/Windows/win.ini",
        "javascript:alert(1)",
        "data:text/html,<h1>Test</h1>",
        "ftp://ftp.example.com",
        "gopher://gopher.example.com",
    ]
    for url in invalid_schemes:
        is_valid, err, _ = validate_url(url, resolve_dns=False)
        assert is_valid is False
        assert "Only HTTP and HTTPS" in err


def test_reject_localhost_and_internal_hostnames():
    """Ensures localhost and local network aliases are blocked."""
    blocked_hosts = [
        "http://localhost",
        "http://localhost:80",
        "https://localhost:443",
        "http://127.0.0.1",
        "http://0.0.0.0",
        "http://app.local",
        "http://service.internal",
        "http://router.lan",
    ]
    for url in blocked_hosts:
        is_valid, err, _ = validate_url(url, resolve_dns=False)
        assert is_valid is False, f"Expected reject for {url}"


def test_reject_private_and_cloud_metadata_ips():
    """Verifies direct private IP literals and 169.254.169.254 are blocked."""
    private_ips = [
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.1",
        "172.16.0.1",
        "169.254.169.254",  # AWS/GCP/Azure Metadata
        "::1",
        "fe80::1",
    ]
    for ip_str in private_ips:
        ip_obj = ipaddress.ip_address(ip_str)
        assert is_ip_restricted(ip_obj) is True

    # Test as URLs
    for ip_str in ["10.0.0.1", "192.168.0.100", "169.254.169.254"]:
        url = f"http://{ip_str}"
        is_valid, err, _ = validate_url(url, resolve_dns=False)
        assert is_valid is False
        assert "private" in err.lower() or "restricted" in err.lower()


def test_reject_non_standard_ports():
    """Ensures ports other than 80 (http) and 443 (https) are blocked."""
    blocked_ports = [
        "http://example.com:8080",
        "https://example.com:8443",
        "http://example.com:22",
        "http://example.com:3000",
        "http://example.com:8000",
    ]
    for url in blocked_ports:
        is_valid, err, _ = validate_url(url, resolve_dns=False)
        assert is_valid is False
        assert "Non-standard port" in err


def test_canonical_url_normalization():
    """Verifies URLs are cleaned, default ports stripped, and fragments removed."""
    assert normalize_canonical_url("HTTP://Example.COM:80/test#section") == "http://example.com/test"
    assert normalize_canonical_url("https://Example.COM:443/review/") == "https://example.com/review/"
    assert normalize_canonical_url("https://example.com") == "https://example.com/"
