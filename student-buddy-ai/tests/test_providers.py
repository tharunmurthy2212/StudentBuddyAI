"""
Tests for AI provider modules.

Run with:
    python -m pytest tests/ -v
    or
    python -m unittest discover -s tests -v
"""

import json
import os
import sys
import unittest

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ai_providers.base import BaseProvider
from ai_providers.mock_provider import (
    MockProvider,
    _count_lines,
    _detect_common_python_issues,
    _detect_common_cpp_issues,
    _detect_common_java_issues,
    _detect_common_js_issues,
    _detect_common_c_issues,
    _detect_language_constructs,
)
from ai_providers.xai_provider import XAIProvider, XAIProviderError
from unittest.mock import MagicMock, patch


class TestMockProviderIdentity(unittest.TestCase):
    """Test that the mock provider correctly identifies itself."""

    def setUp(self):
        self.provider = MockProvider()

    def test_name(self):
        self.assertIn("Mock", self.provider.get_name())

    def test_not_live_ai(self):
        self.assertFalse(self.provider.is_live_ai())

    def test_is_base_provider(self):
        self.assertIsInstance(self.provider, BaseProvider)


class TestMockProviderHints(unittest.TestCase):
    """Test progressive hint generation."""

    def setUp(self):
        self.provider = MockProvider()
        self.problem = "Find the largest number in a list"

    def test_hint_level_1(self):
        result = self.provider.generate_hint(self.problem, "Python", 1)
        self.assertIn("Hint 1", result)
        self.assertIn("Conceptual", result)

    def test_hint_level_2(self):
        result = self.provider.generate_hint(self.problem, "Python", 2)
        self.assertIn("Hint 2", result)
        self.assertIn("Algorithm", result)

    def test_hint_level_3(self):
        result = self.provider.generate_hint(self.problem, "Python", 3)
        self.assertIn("Hint 3", result)
        self.assertIn("Step", result)

    def test_hint_level_4_python(self):
        result = self.provider.generate_hint(self.problem, "Python", 4)
        self.assertIn("Hint 4", result)
        self.assertIn("Sample Solution", result)
        self.assertIn("python", result.lower())

    def test_hint_level_4_cpp(self):
        result = self.provider.generate_hint(self.problem, "C++", 4)
        self.assertIn("cpp", result.lower())

    def test_hint_contains_disclaimer(self):
        result = self.provider.generate_hint(self.problem, "Python", 1)
        self.assertIn("built‑in rules", result)

    def test_progressive_levels_differ(self):
        """Each hint level should produce different content."""
        hints = [
            self.provider.generate_hint(self.problem, "Python", level)
            for level in range(1, 5)
        ]
        # All four should be distinct
        self.assertEqual(len(set(hints)), 4)

    def test_keyword_matching_sort(self):
        result = self.provider.generate_hint("sort the array", "Python", 2)
        self.assertIn("Sort", result)

    def test_keyword_matching_search(self):
        result = self.provider.generate_hint("search for an element", "Python", 2)
        self.assertIn("Search", result)


class TestMockProviderApproach(unittest.TestCase):
    """Test approach explanation."""

    def setUp(self):
        self.provider = MockProvider()

    def test_approach_structure(self):
        result = self.provider.explain_approach("Reverse a string", "Python")
        self.assertIn("Problem Understanding", result)
        self.assertIn("Input", result)
        self.assertIn("Step", result)
        self.assertIn("Complexity", result)

    def test_approach_includes_problem(self):
        problem = "Calculate factorial of N"
        result = self.provider.explain_approach(problem, "Python")
        self.assertIn("factorial", result.lower())


class TestMockProviderCodeExplanation(unittest.TestCase):
    """Test code explanation."""

    def setUp(self):
        self.provider = MockProvider()

    def test_empty_code(self):
        result = self.provider.explain_code("", "Python")
        self.assertIn("No code provided", result)

    def test_whitespace_only_code(self):
        result = self.provider.explain_code("   \n\n  ", "Python")
        self.assertIn("No code provided", result)

    def test_python_code_analysis(self):
        code = "def hello():\n    print('Hello World')\n"
        result = self.provider.explain_code(code, "Python")
        self.assertIn("function definition", result)
        self.assertIn("print call", result)
        self.assertIn("Lines", result)

    def test_cpp_code_analysis(self):
        code = '#include <iostream>\nint main() {\n    cout << "Hi";\n    return 0;\n}\n'
        result = self.provider.explain_code(code, "C++")
        self.assertIn("include directive", result)
        self.assertIn("main function", result)

    def test_disclaimer_present(self):
        code = "x = 5"
        result = self.provider.explain_code(code, "Python")
        self.assertIn("built‑in rules", result)


class TestMockProviderDebugging(unittest.TestCase):
    """Test debugging assistance."""

    def setUp(self):
        self.provider = MockProvider()

    def test_empty_code(self):
        result = self.provider.debug_code("", "Python", "")
        self.assertIn("No code provided", result)

    def test_python_missing_colon(self):
        code = "if x == 5\n    print(x)\n"
        result = self.provider.debug_code(code, "Python", "SyntaxError")
        # Should detect the missing colon
        self.assertIn("colon", result.lower())

    def test_python_print_without_parens(self):
        code = 'print "hello"\n'
        result = self.provider.debug_code(code, "Python", "SyntaxError")
        self.assertIn("parentheses", result.lower())

    def test_error_message_suggestions(self):
        code = "print(x)"
        result = self.provider.debug_code(code, "Python", "NameError: name 'x' is not defined")
        self.assertIn("defined", result.lower())

    def test_cpp_missing_iostream(self):
        code = 'int main() {\n    cout << "Hi";\n    return 0;\n}\n'
        result = self.provider.debug_code(code, "C++", "")
        self.assertIn("iostream", result.lower())

    def test_general_checklist_present(self):
        code = "x = 1"
        result = self.provider.debug_code(code, "Python", "")
        self.assertIn("Debugging Checklist", result)


class TestMockProviderPracticeQuestions(unittest.TestCase):
    """Test practice question retrieval."""

    def setUp(self):
        self.provider = MockProvider()

    def test_get_all_questions(self):
        questions = self.provider.get_practice_questions("All", "All")
        self.assertGreater(len(questions), 0)
        # Each question should have required keys
        for q in questions:
            self.assertIn("title", q)
            self.assertIn("topic", q)
            self.assertIn("difficulty", q)
            self.assertIn("statement", q)
            self.assertIn("example_input", q)
            self.assertIn("example_output", q)

    def test_filter_by_topic(self):
        questions = self.provider.get_practice_questions("Loops", "All")
        self.assertGreater(len(questions), 0)
        for q in questions:
            self.assertEqual(q["topic"], "Loops")

    def test_filter_by_difficulty(self):
        questions = self.provider.get_practice_questions("All", "Easy")
        self.assertGreater(len(questions), 0)
        for q in questions:
            self.assertEqual(q["difficulty"], "Easy")

    def test_filter_combined(self):
        questions = self.provider.get_practice_questions("Strings", "Easy")
        for q in questions:
            self.assertEqual(q["topic"], "Strings")
            self.assertEqual(q["difficulty"], "Easy")

    def test_no_match_returns_empty(self):
        questions = self.provider.get_practice_questions("Quantum Computing", "All")
        self.assertEqual(len(questions), 0)


class TestHelperFunctions(unittest.TestCase):
    """Test the code-analysis helper functions."""

    def test_count_lines(self):
        self.assertEqual(_count_lines("a\nb\nc"), 3)
        self.assertEqual(_count_lines("single"), 1)
        self.assertEqual(_count_lines(""), 0)

    def test_detect_python_constructs(self):
        code = "def foo():\n    for x in range(10):\n        print(x)"
        constructs = _detect_language_constructs(code, "Python")
        self.assertIn("function definition (def)", constructs)
        self.assertIn("for loop", constructs)
        self.assertIn("print call", constructs)

    def test_detect_cpp_constructs(self):
        code = "#include <iostream>\nint main() {\n    for (int i=0; i<10; i++) {}\n}"
        constructs = _detect_language_constructs(code, "C++")
        self.assertIn("include directive", constructs)
        self.assertIn("main function", constructs)
        self.assertIn("for loop", constructs)

    def test_python_tab_space_mix(self):
        code = "def foo():\n\tprint(1)\n    print(2)"
        issues = _detect_common_python_issues(code)
        found = any("tab" in issue.lower() for issue in issues)
        self.assertTrue(found, "Should detect mixed tabs and spaces")


class TestXAIProviderPlaceholder(unittest.TestCase):
    """Test the xAI placeholder provider."""

    def test_is_live_ai(self):
        provider = XAIProvider()
        self.assertTrue(provider.is_live_ai())

    def test_name(self):
        provider = XAIProvider()
        self.assertIn("xAI", provider.get_name())

    def test_requires_credentials(self):
        """Without credentials, methods should raise XAIProviderError."""
        provider = XAIProvider()
        # API key is not configured in test environment
        with self.assertRaises(XAIProviderError):
            provider.generate_hint("test", "Python", 1)

    def test_hint_raises_without_key(self):
        provider = XAIProvider()
        with self.assertRaises(XAIProviderError):
            provider.explain_approach("test", "Python")

    def test_explain_code_raises_without_key(self):
        provider = XAIProvider()
        with self.assertRaises(XAIProviderError):
            provider.explain_code("x = 1", "Python")

    def test_debug_raises_without_key(self):
        provider = XAIProvider()
        with self.assertRaises(XAIProviderError):
            provider.debug_code("x = 1", "Python", "error")


class TestMockProviderMultiLanguage(unittest.TestCase):
    """Test support for Java, JavaScript, and C in MockProvider."""

    def setUp(self):
        self.provider = MockProvider()

    def test_java_constructs(self):
        code = "public class Main {\n    public static void main(String[] args) {\n        System.out.println(42);\n    }\n}"
        constructs = _detect_language_constructs(code, "Java")
        self.assertTrue(any("class" in c.lower() for c in constructs))
        self.assertTrue(any("main" in c.lower() for c in constructs))
        self.assertTrue(any("print" in c.lower() for c in constructs))

    def test_java_issues_missing_semicolon(self):
        code = "int x = 10\nSystem.out.println(x);"
        issues = _detect_common_java_issues(code)
        self.assertTrue(any("semicolon" in i.lower() for i in issues))

    def test_java_issues_system_case(self):
        code = "system.out.println(10);"
        issues = _detect_common_java_issues(code)
        self.assertTrue(any("System.out" in i for i in issues))

    def test_js_constructs(self):
        code = "const solve = (arr) => {\n    console.log(arr);\n    return arr.length;\n};"
        constructs = _detect_language_constructs(code, "JavaScript")
        self.assertTrue(any("arrow" in c.lower() for c in constructs))
        self.assertTrue(any("const" in c.lower() for c in constructs))
        self.assertTrue(any("console.log" in c.lower() for c in constructs))

    def test_js_equality_issue(self):
        code = "if (a == b) { console.log('match'); }"
        issues = _detect_common_js_issues(code)
        self.assertTrue(any("===" in i for i in issues))

    def test_c_constructs(self):
        code = "#include <stdio.h>\nint main(void) {\n    printf(\"Hello\\n\");\n    return 0;\n}"
        constructs = _detect_language_constructs(code, "C")
        self.assertTrue(any("include" in c.lower() for c in constructs))
        self.assertTrue(any("main" in c.lower() for c in constructs))
        self.assertTrue(any("printf" in c.lower() for c in constructs))

    def test_c_missing_stdio(self):
        code = "int main(void) {\n    printf(\"Hello\\n\");\n    return 0;\n}"
        issues = _detect_common_c_issues(code)
        self.assertTrue(any("stdio.h" in i for i in issues))

    def test_hint_templates_new_languages(self):
        for lang in ["Java", "JavaScript", "C"]:
            hint = self.provider.generate_hint("find maximum element", lang, 4)
            self.assertIn("Hint 4", hint)
            self.assertIn(lang.lower(), hint.lower())

    def test_debug_suggestions_new_languages(self):
        java_res = self.provider.debug_code("String s = null; s.length();", "Java", "NullPointerException")
        self.assertIn("null", java_res.lower())

        js_res = self.provider.debug_code("let obj; obj.test()", "JavaScript", "TypeError: Cannot read properties of undefined")
        self.assertIn("undefined", js_res.lower())

        c_res = self.provider.debug_code("int *p = NULL; *p = 1;", "C", "Segmentation fault (core dumped)")
        self.assertIn("segmentation fault", c_res.lower())


class TestXAIProviderLiveExecution(unittest.TestCase):
    """Test XAIProvider with mocked API calls."""

    def setUp(self):
        self.provider = XAIProvider(api_key="mock_secret_key_123", model="grok-2", base_url="https://api.x.ai/v1")

    @patch("requests.post")
    def test_generate_hint_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Here is an intuitive hint for your problem."}}]
        }
        mock_post.return_value = mock_response

        res = self.provider.generate_hint("Find maximum subarray", "Python", 1)
        self.assertEqual(res, "Here is an intuitive hint for your problem.")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["model"], "grok-2")
        self.assertIn("Bearer mock_secret_key_123", kwargs["headers"]["Authorization"])

    @patch("requests.post")
    def test_explain_approach_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Kadane's algorithm is optimal."}}]
        }
        mock_post.return_value = mock_response

        res = self.provider.explain_approach("Find maximum subarray", "Python")
        self.assertIn("Kadane", res)

    @patch("requests.post")
    def test_explain_code_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This loop computes prefix sums."}}]
        }
        mock_post.return_value = mock_response

        res = self.provider.explain_code("total += x", "Python")
        self.assertIn("prefix sums", res)

    @patch("requests.post")
    def test_debug_code_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "The bug is an off-by-one indexing error."}}]
        }
        mock_post.return_value = mock_response

        res = self.provider.debug_code("for i in range(len(a) + 1): print(a[i])", "Python", "IndexError")
        self.assertIn("off-by-one", res)

    @patch("requests.post")
    def test_timeout_handling(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timed out")

        with self.assertRaises(XAIProviderError) as ctx:
            self.provider.generate_hint("test", "Python", 1)
        self.assertIn("timed out", str(ctx.exception).lower())

    @patch("requests.post")
    def test_unauthorized_401(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(XAIProviderError) as ctx:
            self.provider.generate_hint("test", "Python", 1)
        self.assertIn("401", str(ctx.exception))

    @patch("requests.post")
    def test_rate_limit_429(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with self.assertRaises(XAIProviderError) as ctx:
            self.provider.generate_hint("test", "Python", 1)
        self.assertIn("429", str(ctx.exception))



class TestPracticeQuestionsDataIntegrity(unittest.TestCase):
    """Ensure the practice_questions.json file is well-formed."""

    def test_json_loads_successfully(self):
        path = os.path.join(PROJECT_ROOT, "data", "practice_questions.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 10)

    def test_all_required_keys_present(self):
        path = os.path.join(PROJECT_ROOT, "data", "practice_questions.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required_keys = {"title", "topic", "difficulty", "statement",
                         "example_input", "example_output"}
        for i, q in enumerate(data):
            for key in required_keys:
                self.assertIn(key, q, f"Question {i} missing key '{key}'")

    def test_difficulty_values_valid(self):
        path = os.path.join(PROJECT_ROOT, "data", "practice_questions.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid = {"Easy", "Medium", "Hard"}
        for q in data:
            self.assertIn(q["difficulty"], valid,
                          f"Invalid difficulty for '{q['title']}'")


if __name__ == "__main__":
    unittest.main()
