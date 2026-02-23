"""
lti_service.py
=============

LTI 1.3 launch validation and launch context handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import time
import uuid

from audit_ledger_service.events import EventType, create_event
from audit_ledger_service.ledger import AuditLedger
from lti_service.ags_client import AGSClient
from lti_service.models import LTIPlatformConfig, LTIToolConfig
from scoring_engine.score_runs import ScoreRun


@dataclass
class LaunchContext:
    launch_id: str
    state: str
    user_id: str
    line_item_url: str
    claims: Dict[str, Any]
    created_at: float


class LTIService:
    def __init__(
        self,
        platform_config: LTIPlatformConfig,
        tool_config: LTIToolConfig,
        audit_ledger: Optional[AuditLedger] = None,
        ags_client: Optional[AGSClient] = None,
    ) -> None:
        self._platform_config = platform_config
        self._tool_config = tool_config
        self._audit_ledger = audit_ledger or AuditLedger()
        self._ags_client = ags_client or AGSClient()
        self._launch_contexts: Dict[str, LaunchContext] = {}
        self._launch_by_state: Dict[str, str] = {}
        self._launch_messages: Dict[str, Any] = {}
        self._tool_conf = self._build_tool_conf()

    def _build_tool_conf(self) -> Any:
        from pylti1p3.tool_config import ToolConfDict

        tool_conf = {
            "title": self._tool_config.tool_name,
            "scopes": [],
            "platforms": {
                self._platform_config.issuer: {
                    "client_id": self._platform_config.client_id,
                    "auth_login_url": self._platform_config.auth_url,
                    "auth_token_url": self._platform_config.token_url,
                    "key_set_url": self._platform_config.jwks_url,
                    "deployment_id": self._platform_config.deployment_id,
                    "audience": self._platform_config.audience,
                }
            },
        }

        return ToolConfDict(tool_conf)

    def _build_request(self, params: Dict[str, Any]) -> "LTIRequestAdapter":
        return LTIRequestAdapter(params)

    def start_login(self, params: Dict[str, Any]) -> str:
        from pylti1p3.oidc_login import OIDCLogin

        oidc_login = OIDCLogin(self._build_request(params), self._tool_conf)
        return oidc_login.get_redirect_url()

    def validate_launch(self, params: Dict[str, Any]) -> LaunchContext:
        from pylti1p3.message_launch import MessageLaunch

        id_token = params.get("id_token")
        if not id_token:
            raise ValueError("id_token is required for LTI launch")

        message_launch = MessageLaunch(
            self._build_request(params),
            self._tool_conf,
        )
        launch_data = message_launch.validate()

        line_item_url = self._extract_line_item_url(launch_data)
        user_id = launch_data.get("sub") or launch_data.get("user_id") or "unknown"

        launch_id = str(uuid.uuid4())
        state = params.get("state") or launch_id

        context = LaunchContext(
            launch_id=launch_id,
            state=state,
            user_id=user_id,
            line_item_url=line_item_url or self._tool_config.default_line_item_url,
            claims=launch_data,
            created_at=time.time(),
        )

        self._launch_contexts[launch_id] = context
        self._launch_by_state[state] = launch_id
        self._launch_messages[launch_id] = message_launch
        self._record_launch_event(context)
        return context

    def get_launch_context(self, launch_id: str) -> LaunchContext:
        if launch_id not in self._launch_contexts:
            raise KeyError(f"Launch context {launch_id} not found")
        return self._launch_contexts[launch_id]

    def get_launch_context_by_state(self, state: str) -> LaunchContext:
        launch_id = self._launch_by_state.get(state)
        if not launch_id:
            raise KeyError(f"Launch context with state {state} not found")
        return self.get_launch_context(launch_id)

    def publish_score(self, launch_id: str, score_run: ScoreRun) -> Dict[str, Any]:
        context = self.get_launch_context(launch_id)
        message_launch = self._launch_messages.get(launch_id)
        if not message_launch:
            raise KeyError(f"Launch message {launch_id} not found")

        access_token = message_launch.get_access_token(
            scopes=["https://purl.imsglobal.org/spec/lti-ags/scope/score"]
        )

        score_payload = self._build_score_payload(score_run, context.user_id)
        response = self._ags_client.submit_score(
            context.line_item_url,
            score_payload,
            access_token,
            idempotency_key=score_run.score_run_id,
        )

        self._record_passback_event(context, score_payload, score_run, response)
        return response

    @staticmethod
    def _extract_line_item_url(claims: Dict[str, Any]) -> Optional[str]:
        ags_claim = claims.get(
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint", {}
        )
        if not isinstance(ags_claim, dict):
            return None
        return ags_claim.get("lineitem") or ags_claim.get("lineitems")

    def _record_launch_event(self, context: LaunchContext) -> None:
        event = create_event(
            event_type=EventType.LTI_LAUNCH,
            session_id=context.launch_id,
            candidate_id=context.user_id,
            actor="lti_platform",
            payload={
                "launch_id": context.launch_id,
                "user_id": context.user_id,
                "line_item_url": context.line_item_url,
                "issuer": self._platform_config.issuer,
                "deployment_id": self._platform_config.deployment_id,
            },
            metadata={"state": context.state},
            timestamp=context.created_at,
        )
        self._audit_ledger.record_audit_event(event)

    def _record_passback_event(
        self,
        context: LaunchContext,
        score_payload: Dict[str, Any],
        score_run: ScoreRun,
        response: Dict[str, Any],
    ) -> None:
        event = create_event(
            event_type=EventType.LTI_GRADE_PASSBACK,
            session_id=context.launch_id,
            candidate_id=context.user_id,
            actor="system",
            payload={
                "score_run_id": score_run.score_run_id,
                "launch_id": context.launch_id,
                "line_item_url": context.line_item_url,
                "score_payload": score_payload,
                "status": response.get("status") if response else None,
            },
            metadata={"idempotency_key": score_run.score_run_id},
            timestamp=time.time(),
        )
        self._audit_ledger.record_audit_event(event)

    @staticmethod
    def _build_score_payload(score_run: ScoreRun, user_id: str) -> Dict[str, Any]:
        score_output = score_run.score_output or {}
        total_score = score_output.get("total_score")
        max_score = score_output.get("max_score")

        if total_score is None:
            cps_score = score_output.get("CPS")
            asi_score = score_output.get("ASI")
            if cps_score is not None or asi_score is not None:
                total_score = (cps_score or 0) + (asi_score or 0)

        if max_score is None:
            cps_total = score_output.get("cps_total")
            asi_total = score_output.get("asi_total")
            if cps_total is not None or asi_total is not None:
                max_score = (cps_total or 0) + (asi_total or 0)
            elif total_score is not None:
                max_score = total_score

        if score_output and total_score is None:
            total_score = 0
        if score_output and max_score is None:
            max_score = 0

        return {
            "userId": user_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scoreGiven": total_score,
            "scoreMaximum": max_score,
            "activityProgress": "Completed",
            "gradingProgress": "FullyGraded",
            "score_run_id": score_run.score_run_id,
            "cps_total": score_output.get("cps_total"),
            "asi_total": score_output.get("asi_total"),
        }


class LTIRequestAdapter:
    """Minimal request adapter for pylti1p3 helpers."""

    def __init__(self, params: Dict[str, Any]) -> None:
        self._params = params

    def get_param(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self._params.get(key)
        return value if value is not None else default

    def get_params(self) -> Dict[str, Any]:
        return dict(self._params)

    def get_cookie(self, key: str) -> Optional[str]:
        return None

    def get_http_header(self, key: str) -> Optional[str]:
        return None
