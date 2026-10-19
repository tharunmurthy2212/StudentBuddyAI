# 📝 Student Buddy AI — Project Notes (Resume & Interview Preparation)

This document helps you explain the project confidently during interviews and write accurate resume bullet points.

---

## 1. Problem Being Addressed

Students often copy coding solutions without understanding the logic. This tool provides structured learning support — progressive hints, approach breakdowns, basic code analysis, and debugging checklists — so students build problem-solving skills instead of memorizing answers.

---

## 2. Architecture & Why the Provider Interface Exists

The project follows a **layered architecture**:

```
UI (Streamlit) → Service Layer → Provider Interface → Concrete Provider
```

**Why a provider interface?**

- The `BaseProvider` abstract class defines a contract (required methods) that any AI backend must implement.
- The `MockProvider` implements this contract using built-in rules (no API needed).
- The `XAIProvider` is a placeholder that implements the same contract for future xAI/Grok integration.
- The `AssistantService` calls the provider without knowing which concrete class is active.

**Benefit:** To add a new AI provider, you only create a new class that inherits `BaseProvider`. The UI, service layer, database, and session management remain untouched. This is the **Strategy design pattern**.

**Interview explanation:**
> "I used the Strategy pattern through a base provider interface. The service layer calls abstract methods, and the concrete provider is selected at runtime based on configuration. This means I can switch from offline rules to a real AI API by changing one config value — no UI code changes needed."

---

## 3. How Offline Mode Works

The `MockProvider` uses:

- **Keyword matching** — scans the problem description for words like "sort", "search", "reverse" to provide slightly tailored hints.
- **Regex-based code analysis** — counts lines, identifies language constructs (functions, loops, imports), and detects common syntax errors.
- **Error-message parsing** — matches error keywords (NameError, TypeError, etc.) to specific debugging suggestions.
- **Static practice questions** — loaded from `data/practice_questions.json`, filtered by topic and difficulty.

**What it does NOT do:**
- It does not understand what arbitrary code *does* logically.
- It does not generate problem-specific solutions.
- All responses include a disclaimer stating they are rule-based.

**Interview explanation:**
> "The demo mode uses pattern matching and predefined templates. It detects common syntax errors like missing colons in Python or missing semicolons in C++ using regular expressions. It doesn't claim to be AI — every response is clearly labelled as coming from built-in rules."

---

## 4. How Streamlit Session State Works

Streamlit re-runs the entire script on every user interaction. To preserve data across these re-runs, we use `st.session_state` — a dictionary that persists for the duration of a browser session.

We store:
- `history` — list of past interactions (newest first)
- `hint_levels` — maps each problem text to its current hint level (1–4)
- `session_id` — anonymous UUID for optional database persistence
- `service` — the `AssistantService` instance (created once)
- `db` — the `DatabaseConnection` instance (created once)

**When the browser tab closes**, session state is lost (unless MySQL persistence is enabled).

**Interview explanation:**
> "Streamlit re-executes the script on every interaction. I used `st.session_state` to persist the hint level tracker, interaction history, and service instances across re-runs. This avoids re-creating expensive objects like database connections on every click."

---

## 5. How Optional MySQL Persistence Works

The `DatabaseConnection` class:

1. Checks if MySQL credentials are configured (via Streamlit secrets or environment variables).
2. If yes, connects to MySQL and auto-creates the `interaction_history` table.
3. If no, sets `is_available = False` and stores an error message.
4. The app checks `db.is_available` before every database operation. If MySQL is unavailable, it silently falls back to session-only mode.

**Parameterized queries** prevent SQL injection — user input is never concatenated into SQL strings.

**Interview explanation:**
> "MySQL is optional. The app checks for credentials at startup. If MySQL is available, interactions are persisted in a database table. If not, everything stays in Streamlit's session state. I used parameterized queries with `%s` placeholders to prevent SQL injection."

---

## 6. Why API Keys Must Remain Private

- API keys are passwords for paid services. Exposing them in GitHub means anyone can use (and bill) your account.
- `.streamlit/secrets.toml` is gitignored so it never enters version control.
- The `secrets.toml.example` file contains only placeholder values.
- The code never logs, displays, or stores API keys in the database.

**Interview explanation:**
> "I used Streamlit's secrets management system. The real secrets file is gitignored, and only a template with placeholder values is committed. The code reads secrets through `st.secrets` and never exposes them in logs, error messages, or the UI."

---

## 7. How the Live AI Provider (xAI / Grok) Works

The live provider (`ai_providers/xai_provider.py`) connects to any OpenAI-compatible chat completions endpoint (including xAI Grok, Groq, OpenAI, or local Ollama).

1. Reads credentials and endpoint via `config.py` (`get_xai_api_key()`, `get_xai_model()`, `get_xai_base_url()`).
2. Constructs tailored Socratic prompts:
   - **Hint 1**: Clarifies the problem intuition and edge cases without algorithms.
   - **Hint 2**: Suggests algorithm patterns and data structure strategies.
   - **Hint 3**: Outlines step-by-step logic and pseudocode.
   - **Hint 4**: Provides language-specific code skeleton with TODOs.
3. Implements comprehensive error handling:
   - Graceful detection of HTTP 401 (Invalid API Key), 429 (Rate Limits/Quota), 500 (Server Errors), and 30s timeouts.
4. Seamlessly toggles via `.streamlit/secrets.toml`: `[ai] provider = "xai"`.

**Interview explanation:**
> "I implemented a live AI provider adhering to the OpenAI chat completions specification. Rather than simply giving answers, it enforces Socratic pedagogical prompting across 4 progressive hint tiers. It includes comprehensive network timeout handling, HTTP error parsing, and fallback to offline rule-based mode."

---

## 8. Main Capabilities & Current Scope

1. **Dual Modes** — Seamlessly toggles between offline demo mode (rule-based scanner) and live AI mode (xAI / OpenAI-compatible API).
2. **5 Supported Programming Languages** — Full analysis and debugging support for Python, C++, Java, JavaScript, and C.
3. **Personal Study Notes & Bookmarks** — Students can bookmark key explanations and export a complete Markdown study sheet (`.md`) with one click.
4. **49 Curated Practice Questions** — Filterable across 10 topics (including Stacks, Queues, Binary Trees, and Sorting).
5. **Session & MySQL Storage** — Zero configuration required; automatically persists to MySQL if credentials exist.

---

## 9. Resume Bullet Points

1. **Engineered an educational AI coding assistant** in Python and Streamlit using the Strategy Pattern to decouple UI logic from pluggable offline rules and live LLM providers (xAI Grok / OpenAI API).

2. **Implemented a 4-tier Socratic progressive hint system** and algorithmic approach explainer supporting Python, C++, Java, JavaScript, and C.

3. **Developed deterministic syntax and error diagnostic scanners** with regular expressions to detect common beginner mistakes (indentation, pointer issues, case errors, missing semicolons) with actionable remediation steps.

4. **Built study bookmarks and Markdown export engine**, enabling students to curate custom revision sheets and study guides for technical interviews and exams.

5. **Designed resilient persistence layer** with parameterized MySQL queries and in-memory fallback, achieving 100% test pass rate across 86 automated unit tests.

---

## 10. Likely Interview Questions & Answers

### Q1: What does your project do?
> It's an educational coding assistant designed to build true problem-solving skills rather than encourage copying. It delivers 4-level progressive hints, structured algorithmic breakdowns, code explanations, and multi-language debugging for Python, C++, Java, JavaScript, and C. It supports both offline demo mode and live AI integration via xAI Grok.

### Q2: How does the AI provider architecture work?
> I implemented the Strategy pattern using an abstract base class `BaseProvider`. Both `MockProvider` (offline rule-based) and `XAIProvider` (live HTTP chat completions) implement the same contract. The service layer inspects configuration and routes calls without the UI knowing which provider is active.

### Q3: How do you handle security for API keys?
> Secrets are strictly isolated in `.streamlit/secrets.toml`, which is gitignored and excluded from version control. The repository only contains a sanitized `secrets.toml.example`. The application reads credentials through `st.secrets` or environment variables without logging or exposing them.

### Q4: How does the progressive hint system prevent copying?
> The system tracks hint levels (1 to 4) in session state per problem. Level 1 only offers conceptual clues, Level 2 suggests algorithmic patterns, Level 3 provides pseudocode, and Level 4 shows a code skeleton with TODOs. Students cannot skip straight to the answer without actively thinking through each step.

### Q5: How do you test the application?
> I developed an 86-test automated test suite using Python's `unittest` framework. It uses `unittest.mock` to simulate API responses, network timeouts, and HTTP status codes (401, 429) without requiring external network calls or paid API keys.

---

*Prepare honest, specific answers. All described features are fully implemented and verified with unit tests.*

