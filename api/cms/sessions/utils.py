import ipaddress
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract and validate the real IP address of the client from the request."""
    # Check for X-Forwarded-For header (most common)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        ip = forwarded_for.split(",")[0].strip()
        return _validate_ip(ip)

    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return _validate_ip(real_ip.strip())

    # Fall back to direct client IP
    client_ip = request.client.host if request.client else "unknown"
    return _validate_ip(client_ip) if client_ip != "unknown" else "unknown"


def _validate_ip(ip_str: str) -> str:
    """Validate and normalize IP address."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return str(ip_obj)
    except ValueError:
        return "unknown"
