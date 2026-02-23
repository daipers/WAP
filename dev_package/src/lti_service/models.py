"""
models.py
=========

LTI configuration models and loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import yaml


@dataclass(frozen=True)
class LTIPlatformConfig:
    issuer: str
    client_id: str
    deployment_id: str
    jwks_url: str
    auth_url: str
    token_url: str
    audience: str


@dataclass(frozen=True)
class LTIToolConfig:
    tool_name: str
    tool_url: str
    default_line_item_url: str


def load_lti_config(
    config_path: str = "dev_package/configs/lti_config.yaml",
) -> Tuple[LTIPlatformConfig, LTIToolConfig]:
    """Load LTI configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"LTI config file not found: {config_path}")

    with config_file.open("r", encoding="utf-8") as file_handle:
        raw_config = yaml.safe_load(file_handle) or {}

    platform_data = raw_config.get("platform", {})
    tool_data = raw_config.get("tool", {})

    platform = LTIPlatformConfig(
        issuer=platform_data.get("issuer", ""),
        client_id=platform_data.get("client_id", ""),
        deployment_id=platform_data.get("deployment_id", ""),
        jwks_url=platform_data.get("jwks_url", ""),
        auth_url=platform_data.get("auth_url", ""),
        token_url=platform_data.get("token_url", ""),
        audience=platform_data.get("audience", ""),
    )

    tool = LTIToolConfig(
        tool_name=tool_data.get("tool_name", ""),
        tool_url=tool_data.get("tool_url", ""),
        default_line_item_url=tool_data.get("default_line_item_url", ""),
    )

    return platform, tool
