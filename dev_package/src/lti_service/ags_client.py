"""
ags_client.py
=============

Assignments and Grade Services (AGS) client for score passback.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class AGSClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self._timeout_seconds = timeout_seconds

    def create_line_item(
        self,
        lineitems_url: str,
        payload: Dict[str, Any],
        access_token: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = self._build_headers(
            access_token,
            content_type="application/vnd.ims.lis.v2.lineitem+json",
            idempotency_key=idempotency_key,
        )

        response = requests.post(
            lineitems_url,
            json=payload,
            headers=headers,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return {}

    def submit_score(
        self,
        line_item_url: str,
        score_payload: Dict[str, Any],
        access_token: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = self._build_headers(
            access_token,
            content_type="application/vnd.ims.lis.v1.score+json",
            idempotency_key=idempotency_key,
        )

        response = requests.post(
            line_item_url,
            json=score_payload,
            headers=headers,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return {}

    @staticmethod
    def _build_headers(
        access_token: str,
        content_type: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers
