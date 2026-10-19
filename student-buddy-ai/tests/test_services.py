"""
Tests for the AssistantService layer.

Run with:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import config
from services.assistant_service import AssistantService


class TestAssistantServiceInit(unittest.TestCase):
    """Test that the service initializes correctly without secrets."""

    def setUp(self):
        self.service = AssistantService()

    def test_default_provider_is_mock(self):
        """Without secrets, the provider should be the mock provider."""
        self.assertIn("Mock", self.service.get_provider_name())

    def test_is_not_live_ai(self):
        self.assertFalse(self.service.is_live_ai())

    def test_mode_label_contains_demo(self):
        label = self.service.get_mode_label()
        self.assertIn("Demo", label)


class TestAssistantServiceHints(unittest.TestCase):
    """Test hint generation through the service layer."""

    def setUp(self):
        self.service = AssistantService()

    def test_empty_problem(self):
        result = self.service.generate_hint("", "Python", 1)
        self.assertIn("Please enter", result)

    def test_whitespace_problem(self):
        result = self.service.generate_hint("   ", "Python", 1)
        self.assertIn("Please enter", result)

    def test_valid_hint(self):
        result = self.service.generate_hint("Find max in array", "Python", 1)
        self.assertIn("Hint 1", result)

    def test_hint_level_clamped_low(self):
        """Hint level below 1 should be clamped to 1."""
        result = self.service.generate_hint("test problem", "Python", -5)
        self.assertIn("Hint 1", result)

    def test_hint_level_clamped_high(self):
        """Hint level above MAX should be clamped."""
        result = self.service.generate_hint("test problem", "Python", 99)
        self.assertIn("Hint 4", result)


class TestAssistantServiceApproach(unittest.TestCase):
    """Test approach explanation through the service layer."""

    def setUp(self):
        self.service = AssistantService()

    def test_empty_problem(self):
        result = self.service.explain_approach("", "Python")
        self.assertIn("Please enter", result)

    def test_valid_approach(self):
        result = self.service.explain_approach("Reverse a string", "Python")
        self.assertIn("Approach", result)


class TestAssistantServiceCodeExplanation(unittest.TestCase):
    """Test code explanation through the service layer."""

    def setUp(self):
        self.service = AssistantService()

    def test_empty_code(self):
        result = self.service.explain_code("", "Python")
        self.assertIn("paste", result.lower())

    def test_valid_code(self):
        result = self.service.explain_code("x = 5\nprint(x)", "Python")
        self.assertIn("Code Analysis", result)


class TestAssistantServiceDebug(unittest.TestCase):
    """Test debugging through the service layer."""

    def setUp(self):
        self.service = AssistantService()

    def test_empty_code(self):
        result = self.service.debug_code("", "Python", "")
        self.assertIn("paste", result.lower())

    def test_valid_debug(self):
        result = self.service.debug_code("x = 5", "Python", "SyntaxError")
        self.assertIn("Debug", result)


class TestAssistantServicePractice(unittest.TestCase):
    """Test practice question retrieval through the service layer."""

    def setUp(self):
        self.service = AssistantService()

    def test_get_all_questions(self):
        questions = self.service.get_practice_questions("All", "All")
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

    def test_filter_returns_list(self):
        questions = self.service.get_practice_questions("Loops", "Easy")
        self.assertIsInstance(questions, list)

    def test_invalid_topic_returns_empty(self):
        questions = self.service.get_practice_questions("NonExistent", "All")
        self.assertEqual(len(questions), 0)


class TestConfigModule(unittest.TestCase):
    """Test config.py behavior when no secrets are configured."""

    def test_default_provider_is_mock(self):
        provider = config.get_ai_provider()
        self.assertEqual(provider, "mock")

    def test_no_xai_key(self):
        key = config.get_xai_api_key()
        self.assertIsNone(key)

    def test_mysql_not_enabled(self):
        # In test environment without env vars, MySQL should not be enabled
        self.assertFalse(config.is_mysql_enabled())

    def test_app_constants(self):
        self.assertEqual(config.APP_TITLE, "Student Buddy AI")
        self.assertIn("Python", config.SUPPORTED_LANGUAGES)
        self.assertIn("C++", config.SUPPORTED_LANGUAGES)
        self.assertIn("Java", config.SUPPORTED_LANGUAGES)
        self.assertIn("JavaScript", config.SUPPORTED_LANGUAGES)
        self.assertIn("C", config.SUPPORTED_LANGUAGES)
        self.assertEqual(config.MAX_HINT_LEVEL, 4)

    def test_provider_switch_with_xai_credentials(self):
        from unittest.mock import patch
        with patch("config.get_ai_provider", return_value="xai"), \
             patch("config.get_xai_api_key", return_value="test_xai_key_123"):
            service = AssistantService()
            self.assertTrue(service.is_live_ai())
            self.assertIn("xAI", service.get_provider_name())
            self.assertIn("Live AI", service.get_mode_label())


class TestDatabaseDisabledOperation(unittest.TestCase):
    """Test that the database module works when MySQL is not available."""

    def test_connection_without_mysql(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        self.assertFalse(db.is_available)
        self.assertTrue(len(db.error_message) > 0)

    def test_save_returns_false(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        result = db.save_interaction("sid", "test", "Python", "q", "r")
        self.assertFalse(result)

    def test_get_history_returns_empty(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        result = db.get_history("sid")
        self.assertEqual(result, [])

    def test_clear_returns_false(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        result = db.clear_history("sid")
        self.assertFalse(result)

    def test_generate_session_id(self):
        from database.connection import generate_session_id
        sid = generate_session_id()
        self.assertEqual(len(sid), 16)
        # Should be unique
        sid2 = generate_session_id()
        self.assertNotEqual(sid, sid2)


if __name__ == "__main__":
    unittest.main()
