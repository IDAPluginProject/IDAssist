#!/usr/bin/env python3

"""
OpenWebUI Provider - OpenAI-compatible API support for OpenWebUI.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

from .openai_platform_api_provider import OpenAIPlatformApiProvider
from .provider_factory import ProviderFactory
from ..models.provider_types import ProviderType


class OpenWebUIPlatformApiProvider(OpenAIPlatformApiProvider):
    """
    OpenWebUI exposes its OpenAI-compatible API below /api by default.

    The path is configured explicitly instead of inferred from the host URL,
    since OpenWebUI can be self-hosted on arbitrary domains and base paths.
    """

    def _get_client_base_url(self) -> Optional[str]:
        base_url = (self.url or ProviderType.OPENWEBUI.default_url).strip()
        if not base_url:
            return None

        return self._append_api_base_path(base_url)

    def _get_models_endpoint_candidates(self) -> List[str]:
        base_url = (self._get_client_base_url() or "").strip().rstrip("/")
        if not base_url:
            return []
        if base_url.endswith("/models"):
            return [base_url]
        return [f"{base_url}/models"]

    def _append_api_base_path(self, base_url: str) -> str:
        api_base_path = self._get_api_base_path()
        normalized = base_url.rstrip("/")
        if not api_base_path:
            return normalized

        parsed = urlsplit(normalized)
        current_path = parsed.path.rstrip("/")
        if current_path == api_base_path or current_path.endswith(f"/{api_base_path.lstrip('/')}"):
            return normalized

        appended_path = f"{current_path}/{api_base_path.lstrip('/')}" if current_path else api_base_path
        return urlunsplit((
            parsed.scheme,
            parsed.netloc,
            appended_path,
            parsed.query,
            parsed.fragment,
        ))

    def _get_api_base_path(self) -> str:
        configured = self.config.get("api_base_path", "/api")
        if configured is None:
            return "/api"

        api_base_path = str(configured).strip()
        if api_base_path in ("", "/"):
            return ""
        return f"/{api_base_path.strip('/')}"


class OpenWebUIPlatformApiProviderFactory(ProviderFactory):
    """Factory for creating OpenWebUI Platform API provider instances."""

    def create_provider(self, config: Dict[str, Any]) -> OpenWebUIPlatformApiProvider:
        """Create OpenWebUI Platform API provider instance."""
        return OpenWebUIPlatformApiProvider(config)

    def supports_provider_type(self, provider_type: ProviderType) -> bool:
        """Check if this factory supports the provider type."""
        return provider_type == ProviderType.OPENWEBUI
