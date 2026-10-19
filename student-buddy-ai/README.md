# 🎓 Student Buddy AI — Your Personal Coding Learning Assistant

A clean, portfolio-ready Python application that helps computer science students **understand** coding problems instead of just copying solutions. Built with Streamlit for the interface and designed with a pluggable AI provider architecture for future extensibility.

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Motivation](#-motivation)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Running the App](#-running-the-app)
- [Running Tests](#-running-tests)
- [Optional MySQL Setup](#-optional-mysql-setup)
- [Demo Mode Limitations](#-demo-mode-limitations)
- [Future AI Integration](#-future-ai-integration)
- [Security Practices](#-security-practices)
- [Screenshots](#-screenshots)
- [Known Limitations & Future Improvements](#-known-limitations--future-improvements)

---

## 🎯 Problem Statement

Many students rely on copying solutions from the internet without understanding the underlying concepts. This leads to poor problem-solving skills and difficulty during exams and interviews.

**Student Buddy AI** provides a structured learning approach: progressive hints, approach explanations, code analysis, debugging checklists, and curated practice exercises — encouraging students to think through problems step by step.

---

## 💡 Motivation

As a first-year B.E. Computer Science student, I wanted to build a project that:

1. **Solves a real learning problem** — helping students understand code, not just copy it.
2. **Demonstrates clean software architecture** — provider interfaces, service layers, and separation of concerns.
3. **Works immediately without external dependencies** — no API keys, no paid services.
4. **Is ready for future enhancement** — a real AI provider can be plugged in without rewriting the app.
5. **Showcases practical skills** — Python, Streamlit, MySQL (optional), testing, and Git.

---

## ✅ Features

### Working Features (Demo / Offline Mode)

| Feature | Description |
|---------|-------------|
| **Live AI Integration** | Full OpenAI-compatible chat completion provider (xAI Grok, Groq, OpenAI, Ollama) with Socratic educational prompting |
| **Progressive Hints** | 4-level hint system: conceptual clue → algorithm suggestion → step-by-step approach → sample solution template |
| **Approach Explanation** | Structured breakdown: problem understanding, input/output, algorithm, steps, dry run, complexity |
| **Code Explanation** | Structural and semantic analysis: line count, construct detection, idiom review, complexity |
| **Debugging Assistant** | Multi-language syntax and error scanner (Python, C++, Java, JavaScript, C) with targeted error checklists |
| **Practice Questions** | 49 curated exercises across 10 topics with difficulty filtering and direct transfer to Problem Assistant |
| **Bookmarks & Study Notes** | Save useful explanations and export complete Markdown study guides for offline revision |
| **Multi-Language Support** | Python, C++, Java, JavaScript, and C supported across all tools |
| **Session History** | In-memory history with review and clear functionality |
| **Mode Indicator** | Real-time status showing demo mode vs. live AI mode |
| **Optional MySQL** | Persistent storage when configured; session-only mode otherwise |

---

## 🛠️ Technology Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Application logic |
| **Streamlit** | Web-based user interface |
| **Requests** | HTTP client for live AI completions |
| **mysql-connector-python** | Optional MySQL persistence |
| **unittest** | Automated testing (86 test suite) |
| **Git / GitHub** | Version control and publishing |

No React, Node.js, Flask, Django, SQLite, or external AI APIs are required.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              Streamlit UI (app.py)           │
│  - Problem Assistant  - Code Explainer      │
│  - Debugger           - Practice Questions  │
│  - Session History    - Settings             │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│         AssistantService (services/)         │
│  - Input validation                          │
│  - Provider routing                          │
│  - Error handling                            │
└──────────────────────┬──────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│ MockProvider │ │ XAI      │ │ Future   │
│ (offline)    │ │ Provider │ │ Provider │
│ ✅ Working    │ │ (placeholder)│ │         │
└──────────────┘ └──────────┘ └──────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│    Optional: MySQL (database/connection.py)  │
│    Falls back to Streamlit session state     │
└──────────────────────────────────────────────┘
```

**Key Design Principle:** The UI never talks directly to a provider. It calls `AssistantService`, which delegates to whichever `BaseProvider` is active. Swapping providers requires zero UI changes.

---

## 📁 Project Structure

```
student-buddy-ai/
├── app.py                          # Main Streamlit application
├── config.py                       # Centralized configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── PROJECT_NOTES.md                # Interview & resume preparation
├── .gitignore                      # Git ignore rules
├── .streamlit/
│   └── secrets.toml.example        # Safe secrets template (no real keys)
├── ai_providers/
│   ├── __init__.py
│   ├── base.py                     # Abstract provider interface
│   ├── mock_provider.py            # Offline rule-based provider ✅
│   └── xai_provider.py             # Future xAI/Grok placeholder
├── services/
│   ├── __init__.py
│   └── assistant_service.py        # Service layer (UI ↔ Provider bridge)
├── database/
│   ├── __init__.py
│   ├── connection.py               # Optional MySQL connection handler
│   └── schema.sql                  # Database setup script
├── data/
│   └── practice_questions.json     # 35 curated coding exercises
└── tests/
    ├── __init__.py
    ├── test_providers.py           # Provider unit tests
    └── test_services.py            # Service & config unit tests
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10 or newer** installed
- **VS Code** (recommended editor)
- **Git** installed

### Step-by-Step Setup (Windows 11 / PowerShell)

```powershell
# 1. Navigate to the project folder
cd path\to\student-buddy-ai

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.venv\Scripts\Activate.ps1

# If PowerShell blocks activation due to execution policy, use:
.venv\Scripts\python.exe -m pip install -r requirements.txt
# and run the app with: .venv\Scripts\python.exe -m streamlit run app.py

# 4. Install dependencies
pip install -r requirements.txt
```

> **Note:** If `python` is not recognized, try `python3` or use the full path to your Python installation.

---

## ▶️ Running the App

```powershell
# With virtual environment activated:
streamlit run app.py

# Or without activation:
.venv\Scripts\python.exe -m streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

**No API key is needed. No MySQL is needed.** The app runs immediately in demo mode.

---

## 🧪 Running Tests

```powershell
# With virtual environment activated:
python -m unittest discover -s tests -v

# Or without activation:
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

All tests run without an API key or MySQL connection.

---

## 🗄️ Optional MySQL Setup

MySQL is **optional**. The app works perfectly without it using in-memory session state.

### If you want persistent storage:

1. **Install MySQL** (if not already installed).

2. **Create the database:**
   ```sql
   mysql -u root -p < database/schema.sql
   ```
   Or open MySQL and run:
   ```sql
   CREATE DATABASE IF NOT EXISTS student_buddy_ai
       CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Create a MySQL user** (optional but recommended):
   ```sql
   CREATE USER 'student_buddy'@'localhost' IDENTIFIED BY 'your_password';
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE
       ON student_buddy_ai.* TO 'student_buddy'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. **Configure credentials** — copy the secrets template:
   ```powershell
   copy .streamlit\secrets.toml.example .streamlit\secrets.toml
   ```
   Edit `.streamlit/secrets.toml` and fill in your MySQL credentials:
   ```toml
   [mysql]
   host = "localhost"
   port = 3306
   user = "student_buddy"
   password = "your_password"
   database = "student_buddy_ai"
   ```

5. **Restart the app.** Check Settings & Status to confirm the connection.

---

## ⚠️ Demo Mode Limitations

The offline / demo mode provides:

- ✅ Progressive hints with keyword-based tailoring
- ✅ Structured approach templates
- ✅ Basic code structure analysis (line count, construct detection)
- ✅ Common syntax error detection (Python & C++)
- ✅ Error-message-specific debugging checklists
- ✅ 35 curated practice questions

**It does NOT provide:**

- ❌ Deep semantic understanding of arbitrary code
- ❌ Problem-specific tailored solutions
- ❌ Natural language reasoning about code logic
- ❌ AI-generated practice questions

All demo-mode responses are clearly labelled with a disclaimer stating they come from built-in rules, not a live AI model.

---

## 🔮 Future AI Integration

The project is designed so a real AI provider can be added without changing the UI or service layer.

### How to add a real provider:

1. **Choose a provider** (e.g., xAI/Grok, OpenAI, etc.)
2. **Implement the methods** in the appropriate provider file (e.g., `ai_providers/xai_provider.py`)
3. **Add credentials** to `.streamlit/secrets.toml`:
   ```toml
   [ai]
   provider = "xai"
   
   [xai]
   api_key = "your_actual_api_key"
   model = "model_name_from_official_docs"
   ```
4. **Restart the app** — the service layer automatically routes to the new provider.

The provider interface (`BaseProvider`) defines all required methods with consistent signatures.

---

## 🔒 Security Practices

- **No API keys in source code** — credentials go in `.streamlit/secrets.toml` (gitignored)
- **No real secrets in templates** — `secrets.toml.example` contains placeholders only
- **No `eval()` or code execution** — user-submitted code is never executed
- **Parameterized SQL queries** — no SQL injection risk
- **No personal data collection** — no real names, emails, or identifiers required
- **Session IDs are anonymous UUIDs** — not linked to any identity

---

## 📸 Screenshots

> Add screenshots of your running application here.
>
> Suggested captures:
> 1. Main Problem Assistant page
> 2. Progressive hints (showing hint levels 1-4)
> 3. Code Explainer output
> 4. Debugging Assistant output
> 5. Practice Questions browser
> 6. Session History view
> 7. Settings & Status page

---

## 📝 Known Limitations & Future Improvements

### Current Limitations

- Demo-mode responses are generic templates, not problem-specific solutions
- Code analysis is structural only (line counting, pattern matching)
- Debugging detection covers common beginner mistakes but not all scenarios
- No persistent session across browser refreshes without MySQL
- Single-user design (no authentication or multi-tenancy)

### Completed in v1.1.0

- [x] Integrate real AI provider (xAI Grok / OpenAI-compatible endpoint) with Socratic tutoring
- [x] Support 5 programming languages: Python, C++, Java, JavaScript, C
- [x] Add Bookmarks & Personal Study Notes with one-click Markdown export
- [x] Expand curated practice questions (49 problems across 10 topics)
- [x] Add quick starter problem & code templates
- [x] Full test suite with 86 unit tests covering offline & live execution

### Next Planned Improvements

- [ ] Add Streamlit Cloud deployment guide & GitHub Actions CI
- [ ] Add interactive code runner sandbox (e.g., Pyodide / Judge0 API)
- [ ] Add user authentication (Streamlit-Authenticator)
- [ ] Add spaced-repetition flashcards for algorithmic patterns

---

## 📄 License

This project is created for educational and portfolio purposes.

---

*Built with ❤️ by a B.E. Computer Science student learning to code better, one problem at a time.*
