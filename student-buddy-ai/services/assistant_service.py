"""
Assistant service — the bridge between the Streamlit UI and AI providers.

The UI calls methods on ``AssistantService``.  The service delegates to
whichever ``BaseProvider`` is currently active (mock or xAI).  This
keeps the UI completely decoupled from the AI backend.
"""

from typing import Dict, List, Optional

import config
from ai_providers.base import BaseProvider
from ai_providers.mock_provider import MockProvider
from ai_providers.xai_provider import XAIProvider, XAIProviderError


class AssistantService:
    """Façade that routes learning requests to the active AI provider."""

    def __init__(self) -> None:
        self._provider: BaseProvider = self._create_provider()

    # ------------------------------------------------------------------
    # Provider selection
    # ------------------------------------------------------------------

    @staticmethod
    def _create_provider() -> BaseProvider:
        """Instantiate the provider specified in the configuration.

        Falls back to ``MockProvider`` when the requested provider is
        unavailable or misconfigured.
        """
        provider_name = config.get_ai_provider()

        if provider_name == "xai":
            # Only select xAI if credentials are present
            if config.get_xai_api_key():
                return XAIProvider()
            # Credentials missing — fall back to mock with a warning
            return MockProvider()

        return MockProvider()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_provider_name(self) -> str:
        return self._provider.get_name()

    def is_live_ai(self) -> bool:
        return self._provider.is_live_ai()

    def get_mode_label(self) -> str:
        """Return a user‑friendly mode description."""
        if self._provider.is_live_ai():
            return f"🟢 Live AI mode — {self._provider.get_name()}"
        return "🟡 Demo mode — using built‑in rules and sample learning responses. Live AI is not connected."

    def generate_hint(
        self,
        problem: str,
        language: str,
        hint_level: int,
    ) -> str:
        """Return a progressive hint at the given level."""
        if not problem.strip():
            return "⚠️ Please enter a coding problem first."
        hint_level = max(1, min(hint_level, config.MAX_HINT_LEVEL))
        try:
            return self._provider.generate_hint(problem, language, hint_level)
        except XAIProviderError as exc:
            return f"### ⚠️ Provider Error\n\n{exc}"
        except Exception as exc:
            return f"### ❌ Unexpected Error\n\n{exc}"

    def explain_approach(self, problem: str, language: str) -> str:
        """Return a structured approach explanation."""
        if not problem.strip():
            return "⚠️ Please enter a coding problem first."
        try:
            return self._provider.explain_approach(problem, language)
        except XAIProviderError as exc:
            return f"### ⚠️ Provider Error\n\n{exc}"
        except Exception as exc:
            return f"### ❌ Unexpected Error\n\n{exc}"

    def explain_code(self, code: str, language: str) -> str:
        """Explain the submitted code snippet."""
        if not code.strip():
            return "⚠️ Please paste your code to get an explanation."
        try:
            return self._provider.explain_code(code, language)
        except XAIProviderError as exc:
            return f"### ⚠️ Provider Error\n\n{exc}"
        except Exception as exc:
            return f"### ❌ Unexpected Error\n\n{exc}"

    def debug_code(
        self,
        code: str,
        language: str,
        error_message: str = "",
    ) -> str:
        """Suggest debugging steps."""
        if not code.strip():
            return "⚠️ Please paste your code to get debugging help."
        try:
            return self._provider.debug_code(code, language, error_message)
        except XAIProviderError as exc:
            return f"### ⚠️ Provider Error\n\n{exc}"
        except Exception as exc:
            return f"### ❌ Unexpected Error\n\n{exc}"

    def get_practice_questions(
        self,
        topic: str = "All",
        difficulty: str = "All",
    ) -> List[Dict]:
        """Return filtered practice questions."""
        try:
            return self._provider.get_practice_questions(topic, difficulty)
        except XAIProviderError as exc:
            return []
        except Exception:
            return []
