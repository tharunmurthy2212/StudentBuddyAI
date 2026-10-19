"""
Mock (offline) AI provider for Student Buddy AI.

This provider delivers useful rule‑based responses without any network
calls or API keys.  All responses are clearly labelled as coming from
built‑in rules, not a live AI model.

The provider performs basic deterministic analysis on user code where
practical (line counting, simple pattern matching for common mistakes)
and returns structured learning templates for everything else.
"""

import json
import os
import re
from typing import Dict, List

from ai_providers.base import BaseProvider

# ---------------------------------------------------------------------------
# Load the curated practice‑question bank once at import time
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_QUESTIONS_PATH = os.path.join(_DATA_DIR, "practice_questions.json")

_PRACTICE_QUESTIONS: List[Dict] = []

if os.path.isfile(_QUESTIONS_PATH):
    try:
        with open(_QUESTIONS_PATH, "r", encoding="utf-8") as fh:
            _PRACTICE_QUESTIONS = json.load(fh)
    except (json.JSONDecodeError, OSError):
        _PRACTICE_QUESTIONS = []


# ---------------------------------------------------------------------------
# Helpers for basic code analysis
# ---------------------------------------------------------------------------

def _count_lines(code: str) -> int:
    return len(code.strip().splitlines())


def _detect_language_constructs(code: str, language: str) -> List[str]:
    """Identify common constructs present in *code*."""
    constructs: List[str] = []

    if language == "Python":
        mapping = {
            r"\bdef\b": "function definition (def)",
            r"\bclass\b": "class definition",
            r"\bfor\b": "for loop",
            r"\bwhile\b": "while loop",
            r"\bif\b": "conditional (if)",
            r"\breturn\b": "return statement",
            r"\bimport\b": "import statement",
            r"\bprint\s*\(": "print call",
            r"\binput\s*\(": "input call",
            r"\btry\b": "try/except block",
            r"\bwith\b": "context manager (with)",
            r"\blambda\b": "lambda expression",
            r"\[\s*.*\s+for\s+": "list comprehension",
        }
    elif language == "C++":
        mapping = {
            r"#include": "include directive",
            r"\bint\s+main\b": "main function",
            r"\bcout\b": "cout output",
            r"\bcin\b": "cin input",
            r"\bfor\s*\(": "for loop",
            r"\bwhile\s*\(": "while loop",
            r"\bif\s*\(": "conditional (if)",
            r"\breturn\b": "return statement",
            r"\bclass\b": "class definition",
            r"\bvector\b": "vector usage",
            r"\bstruct\b": "struct definition",
        }
    elif language == "Java":
        mapping = {
            r"\bpublic\s+class\b": "public class definition",
            r"\bclass\b": "class definition",
            r"\bpublic\s+static\s+void\s+main\b": "main method entrypoint",
            r"System\.out\.print": "System.out print statement",
            r"\bScanner\b": "Scanner input reader",
            r"\bArrayList\b": "ArrayList collection",
            r"\bfor\s*\(": "for loop",
            r"\bwhile\s*\(": "while loop",
            r"\bif\s*\(": "conditional (if)",
            r"\breturn\b": "return statement",
            r"\btry\b": "try/catch block",
            r"\bnew\b": "object instantiation (new)",
        }
    elif language == "JavaScript":
        mapping = {
            r"\bfunction\b": "function declaration",
            r"=>": "arrow function",
            r"\bconst\b": "const variable declaration",
            r"\blet\b": "let variable declaration",
            r"\bvar\b": "var variable declaration",
            r"console\.log": "console.log output",
            r"\bfor\s*\(": "for loop",
            r"\bwhile\s*\(": "while loop",
            r"\bif\s*\(": "conditional (if)",
            r"\breturn\b": "return statement",
            r"\basync\b": "async function",
            r"\bawait\b": "await expression",
            r"\bPromise\b": "Promise usage",
        }
    elif language == "C":
        mapping = {
            r"#include": "preprocessor include directive",
            r"\bint\s+main\b": "main function entrypoint",
            r"\bprintf\s*\(": "printf output",
            r"\bscanf\s*\(": "scanf input",
            r"\bmalloc\s*\(": "dynamic memory allocation (malloc)",
            r"\bfree\s*\(": "memory deallocation (free)",
            r"\bstruct\b": "struct definition",
            r"\bfor\s*\(": "for loop",
            r"\bwhile\s*\(": "while loop",
            r"\bif\s*\(": "conditional (if)",
            r"\breturn\b": "return statement",
            r"\*": "pointer usage / dereference",
        }
    else:
        mapping = {}

    for pattern, label in mapping.items():
        if re.search(pattern, code):
            constructs.append(label)

    return constructs


def _detect_common_python_issues(code: str) -> List[str]:
    """Detect frequent beginner Python mistakes with simple regex rules."""
    issues: List[str] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue

        # Missing colon after common block statements
        for keyword in ("if", "elif", "else", "for", "while", "def", "class", "try", "except", "finally", "with"):
            pattern = rf"^\s*{keyword}\b.*[^:]\s*$"
            if keyword == "else":
                pattern = rf"^\s*else\s*[^:]*$"
            if re.match(pattern, stripped):
                # Avoid false positives on continued lines
                if not stripped.endswith("\\"):
                    issues.append(
                        f"Line {i}: possible missing colon after `{keyword}` statement."
                    )

        # Using = instead of == in a condition
        if re.match(r"^\s*(if|elif|while)\b", stripped):
            # Rough check: single = that is not ==, !=, <=, >=
            condition_part = stripped.split(":", 1)[0]
            single_eq = re.findall(r"(?<!=)=(?!=)", condition_part)
            if single_eq and "==" not in condition_part:
                issues.append(
                    f"Line {i}: possible use of `=` (assignment) instead of `==` (comparison)."
                )

        # print without parentheses (Python 2 style)
        if re.match(r"^\s*print\s+[^(]", stripped):
            issues.append(
                f"Line {i}: `print` should be called as a function — use `print(...)` with parentheses."
            )

        # Mismatched brackets (very basic)
        open_count = stripped.count("(") + stripped.count("[") + stripped.count("{")
        close_count = stripped.count(")") + stripped.count("]") + stripped.count("}")
        if open_count != close_count:
            issues.append(
                f"Line {i}: unmatched brackets — check opening/closing parentheses, brackets, or braces."
            )

    # Tab/space mix detection
    has_tabs = any("\t" in line for line in lines)
    has_spaces = any(line.startswith("    ") for line in lines)
    if has_tabs and has_spaces:
        issues.append(
            "Mixed tabs and spaces detected — Python requires consistent indentation.  "
            "Configure your editor to use 4 spaces per indent."
        )

    return issues


def _detect_common_cpp_issues(code: str) -> List[str]:
    """Detect frequent beginner C++ mistakes with simple regex rules."""
    issues: List[str] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("//"):
            continue

        # Missing semicolons (rough heuristic)
        if (
            not stripped.endswith(";")
            and not stripped.endswith("{")
            and not stripped.endswith("}")
            and not stripped.endswith(":")
            and not stripped.endswith("\\")
            and not stripped.startswith("#")
            and not stripped.startswith("//")
            and "{" not in stripped
            and "}" not in stripped
            and not re.match(r"^\s*(if|else|for|while|do|switch|case|class|struct|namespace)\b", stripped)
        ):
            # Check if line looks like a statement
            if re.search(r"[a-zA-Z0-9_\)\]]\s*$", stripped):
                issues.append(
                    f"Line {i}: possible missing semicolon at end of statement."
                )

        # Missing `using namespace std;` or std:: prefix
        if ("cout" in stripped or "cin" in stripped) and "std::" not in stripped:
            if not any("using namespace std" in l for l in lines):
                issues.append(
                    f"Line {i}: `cout`/`cin` used without `std::` prefix and "
                    f"no `using namespace std;` found."
                )
                break  # Report once

    # Check for missing #include <iostream>
    uses_io = any("cout" in l or "cin" in l for l in lines)
    has_iostream = any("#include" in l and "iostream" in l for l in lines)
    if uses_io and not has_iostream:
        issues.append(
            "Missing `#include <iostream>` — required for cout/cin."
        )

    return issues


def _detect_common_java_issues(code: str) -> List[str]:
    """Detect frequent beginner Java mistakes with regex rules."""
    issues: List[str] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        # Missing semicolon
        if (
            not stripped.endswith(";")
            and not stripped.endswith("{")
            and not stripped.endswith("}")
            and not stripped.endswith(":")
            and not stripped.endswith("\\")
            and not stripped.startswith("@")
            and not stripped.startswith("//")
            and "{" not in stripped
            and "}" not in stripped
            and not re.match(r"^\s*(public|private|protected|class|interface|if|else|for|while|do|switch|case|try|catch|finally)\b", stripped)
        ):
            if re.search(r"[a-zA-Z0-9_\)\]]\s*$", stripped):
                issues.append(f"Line {i}: possible missing semicolon `;` at end of statement.")

        # system.out vs System.out
        if re.search(r"\bsystem\.out\b", stripped):
            issues.append(f"Line {i}: Java is case-sensitive; use `System.out` with a capital `S`.")

        # String equality using == instead of .equals()
        if re.search(r'".*"\s*==|==\s*".*"', stripped):
            issues.append(f"Line {i}: comparing strings with `==` compares references; use `.equals()` to compare string contents.")

        # Unmatched brackets
        open_count = stripped.count("(") + stripped.count("[") + stripped.count("{")
        close_count = stripped.count(")") + stripped.count("]") + stripped.count("}")
        if open_count != close_count:
            issues.append(f"Line {i}: unmatched brackets — check opening/closing parentheses, brackets, or braces.")

    return issues


def _detect_common_js_issues(code: str) -> List[str]:
    """Detect frequent beginner JavaScript mistakes with regex rules."""
    issues: List[str] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
            continue

        # Using == instead of ===
        if re.search(r"(?<!=)==(?!=)", stripped):
            issues.append(f"Line {i}: consider using strict equality `===` instead of loose equality `==`.")

        # console.log misspellings or python print
        if re.search(r"\bconsole\.print\b|\bprint\s*\(", stripped) and "console.log" not in stripped:
            issues.append(f"Line {i}: in JavaScript, use `console.log(...)` to print output to the console.")

        # Unmatched brackets
        open_count = stripped.count("(") + stripped.count("[") + stripped.count("{")
        close_count = stripped.count(")") + stripped.count("]") + stripped.count("}")
        if open_count != close_count:
            issues.append(f"Line {i}: unmatched brackets — check opening/closing parentheses, brackets, or braces.")

    return issues


def _detect_common_c_issues(code: str) -> List[str]:
    """Detect frequent beginner C mistakes with regex rules."""
    issues: List[str] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
            continue

        # Missing semicolons
        if (
            not stripped.endswith(";")
            and not stripped.endswith("{")
            and not stripped.endswith("}")
            and not stripped.endswith(":")
            and not stripped.endswith("\\")
            and not stripped.startswith("#")
            and not stripped.startswith("//")
            and "{" not in stripped
            and "}" not in stripped
            and not re.match(r"^\s*(if|else|for|while|do|switch|case|struct|union|enum)\b", stripped)
        ):
            if re.search(r"[a-zA-Z0-9_\)\]]\s*$", stripped):
                issues.append(f"Line {i}: possible missing semicolon `;` at end of statement.")

        # Assignment = inside if condition
        if re.match(r"^\s*if\s*\(", stripped):
            condition_part = stripped.split(")", 1)[0]
            single_eq = re.findall(r"(?<!=)=(?!=)", condition_part)
            if single_eq and "==" not in condition_part:
                issues.append(f"Line {i}: possible assignment `=` instead of equality `==` in condition.")

        # Unmatched brackets
        open_count = stripped.count("(") + stripped.count("[") + stripped.count("{")
        close_count = stripped.count(")") + stripped.count("]") + stripped.count("}")
        if open_count != close_count:
            issues.append(f"Line {i}: unmatched brackets — check parentheses or braces.")

    # Missing #include <stdio.h>
    uses_io = any("printf" in l or "scanf" in l for l in lines)
    has_stdio = any("#include" in l and "stdio.h" in l for l in lines)
    if uses_io and not has_stdio:
        issues.append("Missing `#include <stdio.h>` — required for printf/scanf.")

    return issues


# ===========================================================================
# Mock provider class
# ===========================================================================

class MockProvider(BaseProvider):
    """Rule‑based offline provider that works without any API key."""

    _DISCLAIMER = (
        "\n\n---\n"
        "📌 *This response was generated by **built‑in rules and sample content**, "
        "not a live AI model.  It may not fully understand your specific problem.  "
        "Connect a real AI provider for detailed, problem‑specific assistance.*"
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        return "Mock / Demo Provider (Offline)"

    def is_live_ai(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Progressive hints
    # ------------------------------------------------------------------

    def generate_hint(self, problem: str, language: str, hint_level: int) -> str:
        problem_lower = problem.lower().strip()

        # Attempt simple keyword matching to give slightly tailored hints
        topic_hints = self._match_topic(problem_lower)

        if hint_level == 1:
            text = (
                "### 💡 Hint 1 — Conceptual Clue\n\n"
                "Think carefully about the **input and output** of this problem.\n\n"
                "- What data type(s) are you working with?\n"
                "- Are there constraints on the size of the input?\n"
                "- Can you solve a smaller version of the problem first?\n"
            )
            if topic_hints.get("clue"):
                text += f"\n🔹 Additional thought: {topic_hints['clue']}\n"

        elif hint_level == 2:
            text = (
                "### 💡 Hint 2 — Algorithm / Data Structure\n\n"
                "Consider which algorithm or data structure fits this problem:\n\n"
            )
            if topic_hints.get("ds"):
                text += f"- This problem might benefit from: **{topic_hints['ds']}**\n"
            else:
                text += (
                    "- **Arrays / Lists** — for ordered collections\n"
                    "- **Hash maps / Dictionaries** — for fast lookups\n"
                    "- **Sorting** — if order matters\n"
                    "- **Two pointers / Sliding window** — for sub‑array problems\n"
                    "- **Recursion / Divide & conquer** — for problems that decompose\n"
                )
            text += (
                "\nAsk yourself: *Does the problem require searching, counting, "
                "ordering, or comparing?*\n"
            )

        elif hint_level == 3:
            text = (
                "### 💡 Hint 3 — Step‑by‑Step Approach\n\n"
                "Here is a general strategy:\n\n"
                "1. **Parse the input** — read or accept the data.\n"
                "2. **Initialize** — set up variables, counters, or containers.\n"
                "3. **Process** — iterate through the data applying the core logic.\n"
                "4. **Edge cases** — handle empty input, single element, duplicates.\n"
                "5. **Return / print** the result.\n"
            )
            if topic_hints.get("steps"):
                text += f"\n🔹 Problem‑specific tip: {topic_hints['steps']}\n"

        elif hint_level >= 4:
            text = (
                "### 💡 Hint 4 — Sample Solution\n\n"
                "Below is a **generic template** to get you started.  "
                "You will need to adapt it to your specific problem.\n\n"
            )
            if language == "Python":
                text += (
                    "```python\n"
                    "def solve(data):\n"
                    "    # Step 1: Parse / validate input\n"
                    "    if not data:\n"
                    "        return None\n"
                    "\n"
                    "    # Step 2: Initialize variables\n"
                    "    result = 0\n"
                    "\n"
                    "    # Step 3: Core logic\n"
                    "    for item in data:\n"
                    "        # Process each item\n"
                    "        result += item  # Replace with actual logic\n"
                    "\n"
                    "    # Step 4: Return result\n"
                    "    return result\n"
                    "\n"
                    "\n"
                    "# Example usage\n"
                    "print(solve([1, 2, 3, 4, 5]))\n"
                    "```\n"
                )
            elif language == "C++":
                text += (
                    "```cpp\n"
                    "#include <iostream>\n"
                    "#include <vector>\n"
                    "using namespace std;\n"
                    "\n"
                    "int solve(vector<int>& data) {\n"
                    "    // Step 1: Validate input\n"
                    "    if (data.empty()) return -1;\n"
                    "\n"
                    "    // Step 2: Initialize variables\n"
                    "    int result = 0;\n"
                    "\n"
                    "    // Step 3: Core logic\n"
                    "    for (size_t i = 0; i < data.size(); i++) {\n"
                    "        result += data[i];  // Replace with actual logic\n"
                    "    }\n"
                    "\n"
                    "    // Step 4: Return result\n"
                    "    return result;\n"
                    "}\n"
                    "\n"
                    "int main() {\n"
                    "    vector<int> v = {1, 2, 3, 4, 5};\n"
                    '    cout << solve(v) << endl;\n'
                    "    return 0;\n"
                    "}\n"
                    "```\n"
                )
            elif language == "Java":
                text += (
                    "```java\n"
                    "public class Solution {\n"
                    "    public static int solve(int[] data) {\n"
                    "        // Step 1: Validate input\n"
                    "        if (data == null || data.length == 0) return -1;\n\n"
                    "        // Step 2: Initialize variables\n"
                    "        int result = 0;\n\n"
                    "        // Step 3: Core logic\n"
                    "        for (int item : data) {\n"
                    "            result += item;  // Replace with actual logic\n"
                    "        }\n\n"
                    "        // Step 4: Return result\n"
                    "        return result;\n"
                    "    }\n\n"
                    "    public static void main(String[] args) {\n"
                    "        int[] test = {1, 2, 3, 4, 5};\n"
                    "        System.out.println(solve(test));\n"
                    "    }\n"
                    "}\n"
                    "```\n"
                )
            elif language == "JavaScript":
                text += (
                    "```javascript\n"
                    "function solve(data) {\n"
                    "    // Step 1: Validate input\n"
                    "    if (!data || data.length === 0) return null;\n\n"
                    "    // Step 2: Initialize variables\n"
                    "    let result = 0;\n\n"
                    "    // Step 3: Core logic\n"
                    "    for (const item of data) {\n"
                    "        result += item; // Replace with actual logic\n"
                    "    }\n\n"
                    "    // Step 4: Return result\n"
                    "    return result;\n"
                    "}\n\n"
                    "// Example usage\n"
                    "console.log(solve([1, 2, 3, 4, 5]));\n"
                    "```\n"
                )
            elif language == "C":
                text += (
                    "```c\n"
                    "#include <stdio.h>\n\n"
                    "int solve(int data[], int size) {\n"
                    "    // Step 1: Validate input\n"
                    "    if (size <= 0) return -1;\n\n"
                    "    // Step 2: Initialize variables\n"
                    "    int result = 0;\n\n"
                    "    // Step 3: Core logic\n"
                    "    for (int i = 0; i < size; i++) {\n"
                    "        result += data[i]; // Replace with actual logic\n"
                    "    }\n\n"
                    "    // Step 4: Return result\n"
                    "    return result;\n"
                    "}\n\n"
                    "int main(void) {\n"
                    "    int test[] = {1, 2, 3, 4, 5};\n"
                    "    printf(\"%d\\n\", solve(test, 5));\n"
                    "    return 0;\n"
                    "}\n"
                    "```\n"
                )
            else:
                text += (
                    "```\n"
                    "// Starter template for " + language + "\n"
                    "// Step 1: Validate input\n"
                    "// Step 2: Core loop and transformation\n"
                    "// Step 3: Return result\n"
                    "```\n"
                )
            text += (
                "\n⚠️ This is a **generic template**, not a tailored solution.  "
                "Modify the logic to match your problem requirements.\n"
            )
        else:
            text = "Invalid hint level."

        return text + self._DISCLAIMER

    # ------------------------------------------------------------------
    # Approach explanation
    # ------------------------------------------------------------------

    def explain_approach(self, problem: str, language: str) -> str:
        topic = self._match_topic(problem.lower())
        text = (
            "### 📝 Approach Explanation\n\n"
            "#### 1. Problem Understanding\n"
            f"You need to solve: *\"{problem[:200]}\"*\n\n"
            "Read the problem statement carefully.  Identify:\n"
            "- What **input** is given?\n"
            "- What **output** is expected?\n"
            "- Are there **constraints** (size limits, value ranges)?\n\n"
            "#### 2. Input & Output Interpretation\n"
            "- Determine the data types of your inputs (numbers, strings, lists).\n"
            "- Clarify the expected output format (single value, list, True/False).\n\n"
            "#### 3. Relevant Concept / Algorithm\n"
        )
        if topic.get("ds"):
            text += f"- This problem likely relates to: **{topic['ds']}**\n\n"
        else:
            text += (
                "- Consider whether the problem involves searching, sorting, "
                "counting, or transforming data.\n"
                "- Match the requirement to a known algorithm or data structure.\n\n"
            )
        text += (
            "#### 4. Step‑by‑Step Approach\n"
            "1. Read and parse the input.\n"
            "2. Choose the right data structure.\n"
            "3. Implement the core processing loop.\n"
            "4. Handle edge cases (empty input, extreme values, duplicates).\n"
            "5. Return or print the result.\n\n"
        )
        if topic.get("steps"):
            text += f"🔹 *Tip:* {topic['steps']}\n\n"
        text += (
            "#### 5. Example / Dry Run\n"
            "Try running through a small example by hand:\n"
            "- Pick a simple input (e.g., a list of 3–5 elements).\n"
            "- Execute each step mentally or on paper.\n"
            "- Verify your output matches expectations.\n\n"
            "#### 6. Complexity\n"
            "- **Time complexity**: Depends on your approach — "
            "a single loop is O(n), nested loops are O(n²).\n"
            "- **Space complexity**: Extra data structures add to space usage.\n"
            "- Aim for the most efficient solution you can understand.\n"
        )
        return text + self._DISCLAIMER

    # ------------------------------------------------------------------
    # Code explanation
    # ------------------------------------------------------------------

    def explain_code(self, code: str, language: str) -> str:
        if not code.strip():
            return "⚠️ **No code provided.**  Please paste your code to get an explanation."

        line_count = _count_lines(code)
        constructs = _detect_language_constructs(code, language)

        text = (
            "### 🔍 Code Analysis\n\n"
            f"**Language:** {language}  \n"
            f"**Lines:** {line_count}  \n\n"
        )

        if constructs:
            text += "**Detected constructs:**\n"
            for c in constructs:
                text += f"- {c}\n"
            text += "\n"
        else:
            text += "No common language constructs were detected by the basic scanner.\n\n"

        text += (
            "#### General Reading Guide\n"
            "1. **Start at the top** — look for imports, includes, or global declarations.\n"
            "2. **Find the entry point** — `main()` in C++, or the top‑level code / `if __name__` block in Python.\n"
            "3. **Trace the flow** — follow function calls, loops, and conditionals.\n"
            "4. **Check data flow** — what variables are created, modified, and returned?\n"
            "5. **Look for edge‑case handling** — does the code handle empty input or errors?\n\n"
            "#### ⚠️ Limitation\n"
            "Full semantic code explanation (understanding what the code *does* logically) "
            "requires a real AI provider.  The analysis above is a basic structural scan.\n"
        )
        return text + self._DISCLAIMER

    # ------------------------------------------------------------------
    # Debugging
    # ------------------------------------------------------------------

    def debug_code(self, code: str, language: str, error_message: str) -> str:
        if not code.strip():
            return "⚠️ **No code provided.**  Please paste your code to get debugging help."

        text = "### 🐛 Debugging Assistance\n\n"

        # Detect common issues
        if language == "Python":
            issues = _detect_common_python_issues(code)
        elif language == "C++":
            issues = _detect_common_cpp_issues(code)
        elif language == "Java":
            issues = _detect_common_java_issues(code)
        elif language == "JavaScript":
            issues = _detect_common_js_issues(code)
        elif language == "C":
            issues = _detect_common_c_issues(code)
        else:
            issues = []

        if issues:
            text += "**Potential issues found:**\n\n"
            for issue in issues:
                text += f"- ⚠️ {issue}\n"
            text += "\n"
        else:
            text += "No common syntax issues were detected by the basic scanner.\n\n"

        # If user provided an error message, offer tailored checklist
        if error_message.strip():
            text += f"**Your error message:** `{error_message.strip()[:300]}`\n\n"
            text += self._error_checklist(error_message, language)
        else:
            text += "💡 *Tip:* Paste the exact error message for more targeted suggestions.\n\n"

        text += (
            "#### General Debugging Checklist\n"
            "1. ✅ Read the error message carefully — it usually tells you the line number.\n"
            "2. ✅ Check for typos in variable and function names.\n"
            "3. ✅ Verify indentation (Python) or braces (C++).\n"
            "4. ✅ Make sure all variables are initialized before use.\n"
            "5. ✅ Check data types — are you mixing strings and numbers?\n"
            "6. ✅ Test with a small, simple input first.\n"
            "7. ✅ Add `print()` statements (Python) or `cout` (C++) to trace values.\n"
            "8. ✅ Compare your code against a working example.\n\n"
            "#### ⚠️ Limitation\n"
            "Precise bug identification for arbitrary code requires a real AI provider "
            "or a full compiler/interpreter.  The suggestions above are rule‑based checks.\n"
        )
        return text + self._DISCLAIMER

    # ------------------------------------------------------------------
    # Practice questions
    # ------------------------------------------------------------------

    def get_practice_questions(self, topic: str, difficulty: str) -> List[Dict]:
        """Filter and return matching practice questions."""
        results = []
        for q in _PRACTICE_QUESTIONS:
            topic_match = (topic.lower() == "all" or
                           q.get("topic", "").lower() == topic.lower())
            diff_match = (difficulty.lower() == "all" or
                          q.get("difficulty", "").lower() == difficulty.lower())
            if topic_match and diff_match:
                results.append(q)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_topic(self, problem_lower: str) -> Dict[str, str]:
        """Very basic keyword matching to provide slightly tailored hints."""
        topic: Dict[str, str] = {}

        if any(w in problem_lower for w in ("sort", "arrange", "order")):
            topic["clue"] = "Think about comparison‑based ordering."
            topic["ds"] = "Sorting (e.g., bubble sort, merge sort)"
            topic["steps"] = "Compare adjacent elements or divide the array and merge."
        elif any(w in problem_lower for w in ("search", "find", "lookup", "locate")):
            topic["clue"] = "Is the data already sorted? That determines your approach."
            topic["ds"] = "Searching (linear search or binary search)"
            topic["steps"] = "For sorted data, try binary search — halve the range each step."
        elif any(w in problem_lower for w in ("sum", "total", "add")):
            topic["clue"] = "You need to accumulate values — think about a running total."
            topic["ds"] = "Accumulation / Prefix sums"
            topic["steps"] = "Initialize a counter at 0 and add each element in a loop."
        elif any(w in problem_lower for w in ("reverse", "palindrome", "mirror")):
            topic["clue"] = "Compare elements from both ends moving inward."
            topic["ds"] = "Two pointers / String reversal"
            topic["steps"] = "Use two pointers (start and end) and swap or compare."
        elif any(w in problem_lower for w in ("fibonacci", "factorial", "recursi")):
            topic["clue"] = "This problem has a recursive structure — each answer depends on smaller sub‑problems."
            topic["ds"] = "Recursion / Dynamic programming"
            topic["steps"] = "Define a base case, then express the answer in terms of smaller inputs."
        elif any(w in problem_lower for w in ("matrix", "2d array", "grid")):
            topic["clue"] = "You are working with rows and columns — use nested loops."
            topic["ds"] = "2D arrays / Matrices"
            topic["steps"] = "Iterate row by row (outer loop) and column by column (inner loop)."
        elif any(w in problem_lower for w in ("string", "character", "substring", "anagram")):
            topic["clue"] = "Think about how you process text character by character."
            topic["ds"] = "Strings / Character frequency"
            topic["steps"] = "Iterate through the string and use a dictionary/map to count characters."
        elif any(w in problem_lower for w in ("dictionary", "hash", "map", "count", "frequency")):
            topic["clue"] = "A hash map lets you associate keys with values for O(1) lookup."
            topic["ds"] = "Hash map / Dictionary"
            topic["steps"] = "Create a dict, iterate over data, and update counts or associations."
        elif any(w in problem_lower for w in ("stack", "bracket", "parenthes")):
            topic["clue"] = "LIFO (Last In, First Out) — think about what was added most recently."
            topic["ds"] = "Stack"
            topic["steps"] = "Push opening symbols, pop for closing, and check for matches."
        elif any(w in problem_lower for w in ("queue", "fifo", "bfs", "level")):
            topic["clue"] = "FIFO (First In, First Out) — process elements in arrival order."
            topic["ds"] = "Queue / BFS"
            topic["steps"] = "Use a queue to track elements to process next."
        elif any(w in problem_lower for w in ("linked list", "node", "pointer")):
            topic["clue"] = "Each element points to the next — traversal is sequential."
            topic["ds"] = "Linked list"
            topic["steps"] = "Traverse with a pointer, updating `current = current.next`."
        elif any(w in problem_lower for w in ("tree", "binary tree", "bst")):
            topic["clue"] = "Think about parent‑child relationships and recursive traversal."
            topic["ds"] = "Trees (binary tree, BST)"
            topic["steps"] = "Use recursion or a stack/queue for traversal (inorder, preorder, postorder, level‑order)."
        elif any(w in problem_lower for w in ("prime", "divisor", "factor", "gcd", "lcm")):
            topic["clue"] = "Number theory — think about divisibility and modular arithmetic."
            topic["ds"] = "Mathematical reasoning"
            topic["steps"] = "Check divisors up to √n for efficiency."
        elif any(w in problem_lower for w in ("max", "min", "largest", "smallest")):
            topic["clue"] = "Track the extreme value as you iterate through the data."
            topic["ds"] = "Linear scan for extremes"
            topic["steps"] = "Initialize with the first element and compare each subsequent element."

        return topic

    def _error_checklist(self, error_message: str, language: str) -> str:
        """Provide specific suggestions based on common error keywords."""
        error_lower = error_message.lower()
        suggestions: List[str] = []

        if language == "Python":
            if "syntaxerror" in error_lower:
                suggestions.append("Check for missing colons, parentheses, or quotes.")
                suggestions.append("Verify that indentation is consistent (4 spaces per level).")
            if "indentationerror" in error_lower or "indent" in error_lower:
                suggestions.append("Make sure you use consistent indentation — 4 spaces, no tabs.")
                suggestions.append("Check that all lines inside a block are indented equally.")
            if "nameerror" in error_lower:
                suggestions.append("A variable or function is used before it is defined.")
                suggestions.append("Check for typos in variable names (Python is case‑sensitive).")
            if "typeerror" in error_lower:
                suggestions.append("You may be mixing incompatible types (e.g., adding a string to a number).")
                suggestions.append("Check function arguments — wrong number or wrong type?")
            if "indexerror" in error_lower:
                suggestions.append("You are accessing a list index that doesn't exist.")
                suggestions.append("Remember: list indices start at 0 and end at len(list)−1.")
            if "keyerror" in error_lower:
                suggestions.append("The dictionary key you are accessing does not exist.")
                suggestions.append("Use `.get(key, default)` to safely access dictionary values.")
            if "valueerror" in error_lower:
                suggestions.append("The value you passed is the right type but an invalid value.")
                suggestions.append("Example: `int('abc')` causes a ValueError.")
            if "attributeerror" in error_lower:
                suggestions.append("You are calling a method or attribute that doesn't exist on this object.")
                suggestions.append("Check the type of your variable — is it what you expect?")
            if "zerodivisionerror" in error_lower:
                suggestions.append("You are dividing by zero. Add a check before division.")
            if "filenotfounderror" in error_lower:
                suggestions.append("The file path is incorrect or the file doesn't exist.")
                suggestions.append("Check the spelling and make sure the file is in the right directory.")
            if "modulenotfounderror" in error_lower or "importerror" in error_lower:
                suggestions.append("The module is not installed. Try `pip install <module_name>`.")
                suggestions.append("Check spelling — module names are case‑sensitive.")
        elif language == "C++":
            if "undeclared" in error_lower or "not declared" in error_lower:
                suggestions.append("A variable or function is used before it is declared.")
                suggestions.append("Check for typos and make sure #include directives are correct.")
            if "expected" in error_lower and ";" in error_lower:
                suggestions.append("A semicolon is missing at the end of a statement.")
            if "no matching function" in error_lower:
                suggestions.append("The arguments passed don't match any function signature.")
            if "segmentation fault" in error_lower or "sigsegv" in error_lower:
                suggestions.append("You are accessing memory that doesn't belong to your program.")
                suggestions.append("Common causes: array out of bounds, null pointer dereference.")
            if "cannot convert" in error_lower or "invalid conversion" in error_lower:
                suggestions.append("There is a type mismatch — check the types of your variables.")
        elif language == "Java":
            if "nullpointer" in error_lower:
                suggestions.append("Attempted to access a method or field on an object reference that is `null`.")
                suggestions.append("Check if the object was initialized with `new` before use.")
            if "arrayindexoutofbounds" in error_lower:
                suggestions.append("Array index out of range. Remember Java arrays are 0-indexed up to `length - 1`.")
            if "cannot find symbol" in error_lower:
                suggestions.append("The compiler cannot find the variable, method, or class name.")
                suggestions.append("Check spelling, case sensitivity, and import statements.")
            if "classnotfound" in error_lower or "noclassdeffound" in error_lower:
                suggestions.append("The specified class is missing from the classpath.")
            if "incompatible types" in error_lower:
                suggestions.append("Type mismatch. Check assignments and return types.")
        elif language == "JavaScript":
            if "typeerror" in error_lower or "undefined is not" in error_lower or "cannot read properties of undefined" in error_lower:
                suggestions.append("Attempted to access a property or method on `undefined` or `null`.")
                suggestions.append("Use optional chaining `?.` or check that the object exists first.")
            if "referenceerror" in error_lower:
                suggestions.append("A variable was used before being declared with `const`, `let`, or `var`.")
                suggestions.append("Check for typos in variable or function names.")
            if "syntaxerror" in error_lower:
                suggestions.append("Syntax error in JavaScript. Check for missing brackets, parentheses, or unclosed quotes.")
            if "rangeerror" in error_lower:
                suggestions.append("Maximum call stack size exceeded (infinite recursion) or invalid array length.")
        elif language == "C":
            if "segmentation fault" in error_lower or "sigsegv" in error_lower:
                suggestions.append("Segmentation Fault: Illegal memory access.")
                suggestions.append("Common causes: Dereferencing a NULL pointer, uninitialized pointer, or buffer overflow.")
            if "implicit declaration" in error_lower:
                suggestions.append("Function used before declaration. Did you include the correct header file (e.g., `<stdio.h>`)?")
            if "conflicting types" in error_lower:
                suggestions.append("Function definition doesn't match its prototype or earlier usage.")
            if "expected" in error_lower and ";" in error_lower:
                suggestions.append("Missing semicolon at the end of a statement.")

        if not suggestions:
            suggestions.append("Carefully read the full error message — it often contains the line number.")
            suggestions.append("Search the error message online for similar issues.")

        text = "**Suggestions based on your error:**\n\n"
        for s in suggestions:
            text += f"- 💡 {s}\n"
        text += "\n"
        return text
