"""
auth.py
======

JWT-based authentication and authorization utilities.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

# Default configuration values (can be overridden by config file)
DEFAULT_CONFIG = {
    "jwt_secret": "dev-secret-key-change-in-production",
    "jwt_algorithm": "HS256",
    "access_token_expire_minutes": 15,
    "refresh_token_expire_days": 7,
}


def load_auth_config(config_path: str = "configs/auth_config.yaml") -> dict:
    """Load auth configuration from YAML file."""
    import yaml
    from pathlib import Path

    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r") as f:
            return {**DEFAULT_CONFIG, **yaml.safe_load(f)}
    return DEFAULT_CONFIG


def create_token(
    candidate_id: str,
    expires_delta: Optional[timedelta] = None,
    config: Optional[dict] = None,
) -> str:
    """
    Create a JWT token with candidate_id claim.

    Args:
        candidate_id: The candidate's unique identifier
        expires_delta: Token expiration time delta (default: 15 minutes)
        config: Auth configuration dict (loads from file if not provided)

    Returns:
        Encoded JWT token string
    """
    if config is None:
        config = load_auth_config()

    if expires_delta is None:
        expires_delta = timedelta(minutes=config.get("access_token_expire_minutes", 15))

    expire = datetime.utcnow() + expires_delta

    payload = {
        "candidate_id": candidate_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(
        payload, config["jwt_secret"], algorithm=config.get("jwt_algorithm", "HS256")
    )
    return token


def verify_token(token: str, config: Optional[dict] = None) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify
        config: Auth configuration dict (loads from file if not provided)

    Returns:
        Decoded token payload dict with candidate_id and claims

    Raises:
        JWTError: If token is invalid, expired, or verification fails
    """
    if config is None:
        config = load_auth_config()

    try:
        payload = jwt.decode(
            token,
            config["jwt_secret"],
            algorithms=[config.get("jwt_algorithm", "HS256")],
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token verification failed: {str(e)}") from e


def require_auth(authorization_header: str, config: Optional[dict] = None) -> dict:
    """
    Validate a Bearer token from Authorization header.

    Args:
        authorization_header: Authorization header value (e.g., "Bearer <token>")
        config: Auth configuration dict (loads from file if not provided)

    Returns:
        Decoded token payload dict

    Raises:
        ValueError: If header format is invalid
        JWTError: If token is invalid or expired
    """
    if not authorization_header:
        raise ValueError("Authorization header is required")

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError(
            "Invalid authorization header format. Expected: 'Bearer <token>'"
        )

    token = parts[1]
    return verify_token(token, config)


def create_refresh_token(candidate_id: str, config: Optional[dict] = None) -> str:
    """
    Create a refresh token with longer expiration.

    Args:
        candidate_id: The candidate's unique identifier
        config: Auth configuration dict (loads from file if not provided)

    Returns:
        Encoded refresh JWT token string
    """
    if config is None:
        config = load_auth_config()

    expires_delta = timedelta(days=config.get("refresh_token_expire_days", 7))
    return create_token(candidate_id, expires_delta, config)
