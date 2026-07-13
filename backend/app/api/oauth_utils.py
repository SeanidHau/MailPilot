from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from fastapi import Request


def callback_url_for(request: Request, route_name: str) -> str:
    """Build a public callback URL, honoring common reverse-proxy headers."""
    raw_url = str(request.url_for(route_name))
    parsed = urlsplit(raw_url)
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    forwarded_host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()

    scheme = forwarded_proto or parsed.scheme
    netloc = forwarded_host or parsed.netloc
    return urlunsplit((scheme, netloc, parsed.path, parsed.query, parsed.fragment))
