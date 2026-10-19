"""
Live AI Provider (xAI Grok / OpenAI-compatible) for Student Buddy AI.

This module connects Student Buddy AI to live LLMs using any OpenAI-compatible
chat completions API, including xAI (Grok), Groq, OpenAI, or local endpoints.
All requests are formatted with specialized educational prompts to ensure
Socratic, step-by-step guidance rather than instant answer dumping.
"""

from typing import Dict, List, Optional
import requests

from ai_providers.base import BaseProvider
import config


class XAIProviderError(Exception):
    """Raised when the AI provider encounters a configuration, network, or API error."""


class XAIProvider(BaseProvider):
    """Live AI provider using an OpenAI-compatible HTTP chat completions endpoint.

    Supports xAI (Grok), Groq, OpenAI, or any endpoint adhering to the
    ``/chat/completions`` specification.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self._api_key: Optional[str] = api_key if api_key is not None else config.get_xai_api_key()
        self._model: str = model if model is not None else config.get_xai_model()
        self._base_url: str = base_url if base_url is not None else config.get_xai_base_url()
        self._timeout: int = timeout

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        return f"xAI / Grok ({self._model})"

    def is_live_ai(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Credential check & API client
    # ------------------------------------------------------------------

    def _require_credentials(self) -> None:
        """Raise an error if the API key is not configured."""
        if not self._api_key:
            raise XAIProviderError(
                "xAI API key is not configured.\n\n"
                "To use the live AI provider:\n"
                "1. Create `.streamlit/secrets.toml` from `secrets.toml.example`.\n"
                "2. Set `[ai] provider = \"xai\"`.\n"
                "3. Add your API key under `[xai] api_key = \"your_key\"`.\n"
                "4. Restart the Streamlit application.\n\n"
                "You can switch back to demo mode anytime by setting `provider = \"mock\"`."
            )

    def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        """Execute a chat completion HTTP POST request against the API endpoint."""
        self._require_credentials()

        endpoint = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"StudentBuddyAI/{config.APP_VERSION}",
        }
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout:
            raise XAIProviderError(
                f"Request to AI service timed out after {self._timeout} seconds. "
                "The server may be overloaded or your internet connection is slow. Please try again."
            )
        except requests.exceptions.ConnectionError:
            raise XAIProviderError(
                f"Failed to connect to AI service at `{endpoint}`. "
                "Please check your internet connection or verify the configured base URL."
            )
        except requests.exceptions.RequestException as exc:
            raise XAIProviderError(f"Network error while communicating with AI service: {exc}")

        # Check HTTP response status codes
        if response.status_code == 401:
            raise XAIProviderError(
                "Authentication failed (HTTP 401: Unauthorized). "
                "Please verify that your API key in `.streamlit/secrets.toml` is valid and active."
            )
        elif response.status_code == 429:
            raise XAIProviderError(
                "Rate limit or quota exceeded (HTTP 429). "
                "You have made too many requests or your account has reached its billing quota. "
                "Please wait a moment or check your account balance."
            )
        elif response.status_code >= 500:
            raise XAIProviderError(
                f"AI service returned a server error (HTTP {response.status_code}). "
                "The provider may be undergoing maintenance. Please try again shortly."
            )
        elif not response.ok:
            error_details = response.text
            try:
                error_json = response.json()
                if "error" in error_json and "message" in error_json["error"]:
                    error_details = error_json["error"]["message"]
            except Exception:
                pass
            raise XAIProviderError(f"AI API request failed (HTTP {response.status_code}): {error_details}")

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise XAIProviderError(f"Received malformed response payload from AI service: {exc}")

    # ------------------------------------------------------------------
    # Core learning operations
    # ------------------------------------------------------------------

    def generate_hint(self, problem: str, language: str, hint_level: int) -> str:
        """Generate a progressive hint at the specified level (1-4)."""
        system_prompt = (
            "You are Student Buddy AI, a patient and encouraging computer science tutor. "
            "Your mission is to help students truly UNDERSTAND programming concepts and "
            "develop algorithmic thinking rather than merely copying solutions.\n\n"
            "Rules:\n"
            "- Adhere strictly to the requested Hint Level.\n"
            "- Never dump the complete working solution prematurely.\n"
            "- Use clean Markdown formatting, bullet points, and short readable paragraphs.\n"
            f"- Address the problem using {language} idioms and best practices when relevant."
        )

        level_guidelines = {
            1: (
                "HINT LEVEL 1 OF 4: Intuition & Concept Clarification.\n"
                "Goal: Help the student understand what the problem is actually asking.\n"
                "- Restate the problem in simple real-world terms.\n"
                "- Highlight the key goal, input types, and output expectation.\n"
                "- Ask 1-2 thought-provoking questions to spark intuition.\n"
                "- DO NOT mention specific algorithms or write any code."
            ),
            2: (
                "HINT LEVEL 2 OF 4: Algorithmic Strategy & Pattern Identification.\n"
                "Goal: Guide the student toward the right algorithmic pattern or data structure.\n"
                "- Suggest 1 or 2 relevant algorithmic patterns (e.g., Two Pointers, Hash Map, "
                "Sliding Window, Binary Search, DFS/BFS, Dynamic Programming, Greedy).\n"
                "- Explain briefly WHY that pattern fits this problem.\n"
                "- Point out key edge cases to watch out for.\n"
                "- DO NOT write code or complete logic."
            ),
            3: (
                "HINT LEVEL 3 OF 4: Step-by-Step Logic & Pseudocode.\n"
                "Goal: Lay out the logical sequence of operations without giving away full code.\n"
                "- Provide clear, numbered steps explaining how to solve the problem.\n"
                "- Include readable pseudocode outline.\n"
                "- Explain how data flows through the steps.\n"
                "- DO NOT provide copy-pasteable complete solution code."
            ),
            4: (
                f"HINT LEVEL 4 OF 4: Code Skeleton & Implementation Guidance in {language}.\n"
                "Goal: Give the student a structured scaffold to complete.\n"
                f"- Provide a starter function skeleton in {language} with function signature, "
                "type hints/annotations, and comments marking where student logic goes (TODOs).\n"
                "- Include a checklist of test cases (normal case, empty/edge case, boundary values).\n"
                "- State the expected time and space complexity."
            ),
        }

        guideline = level_guidelines.get(hint_level, level_guidelines[1])
        user_prompt = (
            f"Programming Language: {language}\n"
            f"Hint Level: {hint_level} / 4\n\n"
            f"Coding Problem:\n{problem}\n\n"
            f"Instructions:\n{guideline}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages, temperature=0.3)

    def explain_approach(self, problem: str, language: str) -> str:
        """Provide a comprehensive, structured approach breakdown."""
        system_prompt = (
            "You are Student Buddy AI, a computer science tutor helping university students "
            "prepare for exams and coding interviews. Break down the approach with high pedagogical "
            "clarity, structure, and educational rigor."
        )

        user_prompt = (
            f"Explain the optimal approach to solve the following problem in {language}:\n\n"
            f"Problem:\n{problem}\n\n"
            "Please format your explanation with these clear markdown sections:\n"
            "### 1. 🎯 Problem Understanding & I/O Breakdown\n"
            "### 2. 💡 Intuition & Core Observation\n"
            "### 3. ⚙️ Optimal Algorithm & Data Structures\n"
            "### 4. 🪜 Step-by-Step Walkthrough\n"
            "### 5. 🧪 Dry Run with an Example\n"
            "### 6. ⚠️ Common Edge Cases & Traps\n"
            "### 7. ⏱️ Time & Space Complexity Analysis (Big-O)"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages, temperature=0.3)

    def explain_code(self, code: str, language: str) -> str:
        """Explain the submitted code snippet semantically and structurally."""
        system_prompt = (
            "You are Student Buddy AI, a knowledgeable programming tutor. Explain code thoroughly "
            "so students understand every line, the underlying mechanics, and computational complexity."
        )

        user_prompt = (
            f"Please explain this {language} code snippet in detail:\n\n"
            f"```{language.lower()}\n{code}\n```\n\n"
            "Provide an explanation structured as follows:\n"
            "### 1. 📌 High-Level Summary\n"
            "What does this code accomplish?\n\n"
            "### 2. 🔍 Line-by-Line / Block Explanation\n"
            "Break down the code logically, explaining what key statements and functions do.\n\n"
            "### 3. 🧠 Key Language Features & Idioms Used\n"
            "Highlight language-specific mechanisms (e.g. memory management, built-in functions, syntax).\n\n"
            "### 4. ⏱️ Complexity Analysis\n"
            "State both Time Complexity and Space Complexity with brief justifications.\n\n"
            "### 5. 💡 Optimization & Style Suggestions\n"
            "How could this code be made cleaner, faster, or more idiomatic?"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages, temperature=0.3)

    def debug_code(self, code: str, language: str, error_message: str = "") -> str:
        """Diagnose bugs, explain the root cause, and guide the student to a fix."""
        system_prompt = (
            "You are Student Buddy AI, a patient debugging mentor. Help the student identify, "
            "understand, and fix errors in their code. Always explain WHY the error happened so "
            "they learn to avoid it in the future."
        )

        error_context = f"\nReported Error/Issue:\n`{error_message}`\n" if error_message.strip() else ""

        user_prompt = (
            f"I need help debugging this {language} code:{error_context}\n\n"
            f"```{language.lower()}\n{code}\n```\n\n"
            "Please format your response with the following sections:\n"
            "### 1. 🔍 Diagnosis of Issues\n"
            "Identify what is going wrong (syntax error, logic flaw, index out of bounds, etc.).\n\n"
            "### 2. 💥 Why Did This Happen?\n"
            "Explain the root cause clearly so the concept sticks.\n\n"
            "### 3. 🛠️ How to Fix It\n"
            "Explain the exact changes needed.\n\n"
            "### 4. ✅ Corrected Code\n"
            f"Provide the corrected, working {language} code with comments highlighting fixes.\n\n"
            "### 5. 🛡️ Verification Checklist\n"
            "2-3 things the student should verify before moving on."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_api(messages, temperature=0.3)

    def get_practice_questions(self, topic: str = "All", difficulty: str = "All") -> List[Dict]:
        """Return practice questions from the curated bank."""
        from ai_providers.mock_provider import MockProvider
        return MockProvider().get_practice_questions(topic, difficulty)
