"""HMAC-SHA256 signature verification for incoming switch requests.

The platform signs dispatch payloads with the team's webhook_secret.
This module verifies those signatures to ensure requests are authentic.

Signature header format: X-Webhook-Signature: sha256=<hex digest>
The digest is computed over the raw request body bytes.
"""
import hashlib
import hmac


def verify_signature(body: bytes, secret: str, signature_header: str) -> bool:
    """Verify HMAC-SHA256 signature from the platform.

    Returns True if the signature is valid, False otherwise.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    received_hex = signature_header[7:]
    expected_hex = hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_hex, received_hex)
