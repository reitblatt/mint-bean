"""Security headers middleware for production deployments.

This module adds essential security headers to all HTTP responses to protect
against common web vulnerabilities:

- HSTS (HTTP Strict Transport Security): Forces HTTPS connections
- X-Content-Type-Options: Prevents MIME sniffing attacks
- X-Frame-Options: Prevents clickjacking
- X-XSS-Protection: Enables browser XSS filters (legacy browsers)
- Content-Security-Policy: Restricts resource loading
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Controls browser features

These headers implement defense-in-depth security best practices.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    This middleware adds comprehensive security headers following OWASP
    best practices for web application security.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers to the response.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # HTTP Strict Transport Security (HSTS)
        # Tells browsers to only use HTTPS for the next 1 year
        # includeSubDomains: Apply to all subdomains
        # preload: Allow inclusion in browser HSTS preload lists
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains; preload"

        # X-Content-Type-Options
        # Prevents browsers from MIME-sniffing responses
        # Forces browser to respect the Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        # Prevents the page from being loaded in an iframe
        # Protects against clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection
        # Enables browser's built-in XSS filter (legacy browsers)
        # Modern browsers rely on CSP instead
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content-Security-Policy
        # Restricts which resources can be loaded by the browser
        # This is a strict policy - adjust based on your frontend needs
        csp_directives = [
            "default-src 'self'",  # Only allow resources from same origin
            "script-src 'self' 'unsafe-inline'",  # Allow inline scripts (needed for some frameworks)
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles
            "img-src 'self' data: https:",  # Allow images from same origin, data URIs, and HTTPS
            "font-src 'self' data:",  # Allow fonts from same origin and data URIs
            "connect-src 'self'",  # Allow API calls to same origin only
            "frame-ancestors 'none'",  # Prevent framing (redundant with X-Frame-Options)
            "base-uri 'self'",  # Restrict <base> tag URLs
            "form-action 'self'",  # Restrict form submission targets
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer-Policy
        # Controls how much referrer information is sent with requests
        # strict-origin-when-cross-origin: Send full URL for same-origin, origin only for cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features the page can use
        # Disables potentially dangerous features
        permissions_directives = [
            "geolocation=()",  # Disable geolocation
            "microphone=()",  # Disable microphone
            "camera=()",  # Disable camera
            "payment=()",  # Disable payment APIs
            "usb=()",  # Disable USB access
            "magnetometer=()",  # Disable magnetometer
            "accelerometer=()",  # Disable accelerometer
            "gyroscope=()",  # Disable gyroscope
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # X-Powered-By and Server header removal
        # Some frameworks add these headers - remove them to avoid disclosing tech stack
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        if "Server" in response.headers:
            del response.headers["Server"]

        return response
