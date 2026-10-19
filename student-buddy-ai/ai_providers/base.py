"""
Base provider interface for Student Buddy AI.

Every AI provider (mock, xAI, or any future service) must inherit from
``BaseProvider`` and implement all abstract methods.  The service layer
calls these methods without knowing which concrete provider is active,
keeping the UI completely decoupled from the AI backend.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseProvider(ABC):
    """Abstract interface that every AI provider must satisfy."""

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @abstractmethod
    def get_name(self) -> str:
        """Return a human‑readable name for this provider."""

    @abstractmethod
    def is_live_ai(self) -> bool:
        """Return ``True`` if this provider makes real AI API calls."""

    # ------------------------------------------------------------------
    # Core learning operations
    # ------------------------------------------------------------------

    @abstractmethod
    def generate_hint(
        self,
        problem: str,
        language: str,
        hint_level: int,
    ) -> str:
        """Return a progressive hint for *problem* at *hint_level* (1–4).

        Parameters
        ----------
        problem : str
            The coding problem description.
        language : str
            Programming language context (``"Python"`` or ``"C++"``).
        hint_level : int
            1 = small clue, 2 = algorithm/data‑structure suggestion,
            3 = step‑by‑step approach, 4 = sample solution.
        """

    @abstractmethod
    def explain_approach(
        self,
        problem: str,
        language: str,
    ) -> str:
        """Return a structured approach explanation for *problem*."""

    @abstractmethod
    def explain_code(
        self,
        code: str,
        language: str,
    ) -> str:
        """Explain the provided *code* snippet."""

    @abstractmethod
    def debug_code(
        self,
        code: str,
        language: str,
        error_message: str,
    ) -> str:
        """Suggest debugging steps for *code* given *error_message*."""

    @abstractmethod
    def get_practice_questions(
        self,
        topic: str,
        difficulty: str,
    ) -> List[Dict]:
        """Return practice questions filtered by *topic* and *difficulty*.

        Each item should be a dict with keys:
        ``title``, ``difficulty``, ``topic``, ``statement``,
        ``example_input``, ``example_output``.
        """
