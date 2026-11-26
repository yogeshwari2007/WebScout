"""
URL Validation and Anti-SSRF Security Engine.

Ensures that user-supplied URLs are strictly validated, limited to standard HTTP/HTTPS
protocols and standard ports, and prevented from accessing local, private, loopback,
link-local, cloud metadata, or reserved network destinations.
"""

import ipaddress
import re
import socket
from typing import Optional, Set, Tuple
from urllib.parse import urlsplit, urlunsplit

# Blocked hostnames and local aliases
RESTRICTED_HOSTNAMES: Set[str] = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "broadcasthost",
    "local",
    "0.0.0.0",
}

# Blocked domain suffixes
RESTRICTED_DOMAIN_SUFFIXES: Tuple[str, ...] = (
    ".local",
    ".localhost",
    ".internal",
    ".lan",
    ".home.arpa",
    ".test",
    ".example",
    ".invalid",
)

# Additional restricted IPv4 networks not completely covered by default flags
EXTRA_RESTRICTED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),       # Current network (only valid as source)
    ipaddress.ip_network("100.64.0.0/10"),   # Shared address space / Carrier-grade NAT
    ipaddress.ip_network("192.0.0.0/24"),     # IETF protocol assignments
    ipaddress.ip_network("198.18.0.0/15"),    # Network benchmark tests
    ipaddress.ip_network("192.88.99.0/24"),   # 6to4 relay anycast
    ipaddress.ip_network("240.0.0.0/4"),      # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
]


def is_ip_restricted(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """
    Evaluates whether an IP address belongs to private, loopback, link-local,
    multicast, cloud-metadata (169.254.169.254), or reserved ranges.
    """
    # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        ip_obj = ip_obj.ipv4_mapped

    if (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    ):
        return True

    # Cloud metadata endpoint explicitly (169.254.169.254)
    if str(ip_obj) == "169.254.169.254":
        return True

    # Check extra restricted networks (IPv4 only)
    if isinstance(ip_obj, ipaddress.IPv4Address):
        for net in EXTRA_RESTRICTED_NETWORKS:
            if ip_obj in net:
                return True

    return False


def normalize_canonical_url(url: str) -> str:
    """
    Normalizes a validated URL:
    - Lowercases scheme and hostname
    - Strips standard port (80 for http, 443 for https)
    - Strips URL fragments (#...)
    - Ensures minimum path '/'
    """
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Strip default ports from netloc
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path if parsed.path else "/"
    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def validate_url(
    url: str, resolve_dns: bool = True
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Performs comprehensive validation against SSRF and malicious input.

    Returns:
        (is_valid: bool, error_message: Optional[str], canonical_url: Optional[str])
    """
    if not isinstance(url, str) or not url.strip():
        return False, "URL must be a non-empty string.", None

    clean_url = url.strip()

    # Reject dangerous schemes immediately before parsing
    lower_url = clean_url.lower()
    if lower_url.startswith(("file:", "data:", "javascript:", "blob:", "ftp:", "gopher:", "dict:")):
        return False, "Only HTTP and HTTPS URLs are allowed.", None

    try:
        parsed = urlsplit(clean_url)
    except Exception:
        return False, "Malformed URL format.", None

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are allowed.", None

    # Hostname validation
    hostname = parsed.hostname
    if not hostname:
        return False, "URL is missing a valid destination hostname.", None

    lower_host = hostname.lower()

    # Reject localhost & internal domain suffixes
    if lower_host in RESTRICTED_HOSTNAMES:
        return False, "Localhost destinations are not allowed.", None

    if any(lower_host.endswith(suffix) for suffix in RESTRICTED_DOMAIN_SUFFIXES):
        return False, "Local and internal domain destinations are not allowed.", None

    # Port validation: standard ports only (80 for http, 443 for https, or omitted)
    if parsed.port is not None:
        if scheme == "http" and parsed.port != 80:
            return False, f"Non-standard port '{parsed.port}' is not permitted. Only standard port 80 is allowed for HTTP.", None
        if scheme == "https" and parsed.port != 443:
            return False, f"Non-standard port '{parsed.port}' is not permitted. Only standard port 443 is allowed for HTTPS.", None

    # Direct IP literal check
    is_direct_ip = False
    try:
        # Strip brackets if IPv6
        ip_str = lower_host.strip("[]")
        ip_obj = ipaddress.ip_address(ip_str)
        is_direct_ip = True
        if is_ip_restricted(ip_obj):
            return False, "Access to private, loopback, or restricted IP destinations is blocked.", None
    except ValueError:
        # Host is a domain name, not a literal IP
        pass

    # DNS Resolution and SSRF validation
    if resolve_dns and not is_direct_ip:
        try:
            # Look up all addresses associated with the hostname
            addr_info = socket.getaddrinfo(
                lower_host,
                parsed.port or (443 if scheme == "https" else 80),
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
            if not addr_info:
                return False, "Domain name could not be resolved to any network address.", None

            for entry in addr_info:
                sockaddr = entry[4]
                ip_addr_str = sockaddr[0]
                resolved_ip = ipaddress.ip_address(ip_addr_str)
                if is_ip_restricted(resolved_ip):
                    return False, "Destination resolves to a restricted or private network address.", None

        except socket.gaierror:
            return False, "Domain name could not be resolved by DNS.", None
        except Exception:
            return False, "Network address resolution failed for destination URL.", None

    canonical = normalize_canonical_url(clean_url)
    return True, None, canonical
