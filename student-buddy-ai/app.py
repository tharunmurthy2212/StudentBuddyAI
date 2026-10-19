"""
Student Buddy AI — Your Personal Coding Learning Assistant
==========================================================

Main Streamlit application. This file handles the user interface and
delegates all AI/logic operations to the ``AssistantService``.

Run with:
    streamlit run app.py
"""

import datetime
from typing import Optional
import streamlit as st

import config
from services.assistant_service import AssistantService
from database.connection import DatabaseConnection, generate_session_id


# ======================================================================
# Page configuration (must be the FIRST Streamlit call)
# ======================================================================

st.set_page_config(
    page_title=f"{config.APP_TITLE} — {config.APP_SUBTITLE}",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ======================================================================
# Custom CSS for a clean, modern, portfolio-grade UI
# ======================================================================

st.markdown("""
<style>
    /* ---- Main app styling ---- */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1E88E5;
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 1.15rem;
        color: #555;
        margin-top: 0;
        margin-bottom: 1.2rem;
    }
    .mode-banner {
        padding: 0.7rem 1.2rem;
        border-radius: 10px;
        font-size: 0.92rem;
        font-weight: 500;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .mode-demo {
        background-color: #FFF3E0;
        border-left: 5px solid #FF9800;
        color: #E65100;
    }
    .mode-live {
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        color: #1B5E20;
    }
    /* ---- Response area ---- */
    .response-card {
        background-color: #ffffff;
        padding: 1.4rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 1rem;
    }
    /* ---- History & Bookmark items ---- */
    .study-item {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.8rem;
    }
    /* ---- Practice card ---- */
    .practice-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #cbd5e1;
    }
    .difficulty-easy {
        color: #15803d;
        font-weight: 700;
        background: #dcfce7;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .difficulty-medium {
        color: #b45309;
        font-weight: 700;
        background: #fef3c7;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .difficulty-hard {
        color: #b91c1c;
        font-weight: 700;
        background: #fee2e2;
        padding: 2px 8px;
        border-radius: 6px;
    }
    /* Quick chip buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    .block-container {
        padding-top: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)


# ======================================================================
# Session state initialization
# ======================================================================

def _init_session_state() -> None:
    """Initialize session state keys if they don't exist."""
    defaults = {
        "session_id": generate_session_id(),
        "history": [],                 # List of dicts for session history
        "bookmarks": [],               # List of saved notes/explanations
        "hint_levels": {},             # problem_text -> current hint level
        "last_response": "",
        "last_action": "",
        "last_language": "Python",
        "last_input": "",
        "service": None,
        "db": None,
        "prefill_problem": "",
        "prefill_code": "",
        "prefill_error": "",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Create the service and DB connection once per session
    if st.session_state["service"] is None:
        st.session_state["service"] = AssistantService()
    if st.session_state["db"] is None:
        st.session_state["db"] = DatabaseConnection()


_init_session_state()

service: AssistantService = st.session_state["service"]
db: DatabaseConnection = st.session_state["db"]


# ======================================================================
# Helpers — history & bookmark management
# ======================================================================

def _save_to_history(action: str, language: str, question: str, response: str) -> None:
    """Append to session history and optionally persist to MySQL."""
    entry = {
        "action": action,
        "language": language,
        "question": question[:500],
        "response": response,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state["history"].insert(0, entry)
    st.session_state["history"] = st.session_state["history"][:50]

    st.session_state["last_response"] = response
    st.session_state["last_action"] = action
    st.session_state["last_language"] = language
    st.session_state["last_input"] = question

    # Persist to MySQL if available
    if db.is_available:
        db.save_interaction(
            session_id=st.session_state["session_id"],
            action=action,
            language=language,
            question=question,
            response=response,
        )


def _add_bookmark(action: str, language: str, input_text: str, response: str) -> None:
    """Save an interaction into user study bookmarks."""
    # Prevent duplicate bookmarking of identical response
    for bm in st.session_state["bookmarks"]:
        if bm["response"] == response and bm["input"] == input_text:
            return

    entry = {
        "id": len(st.session_state["bookmarks"]) + 1,
        "action": action,
        "language": language,
        "input": input_text,
        "response": response,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state["bookmarks"].insert(0, entry)


def _render_response_card(action_title: str, language: str, input_text: str, response_text: str, key_prefix: str) -> None:
    """Render a styled response card with bookmarking option."""
    st.divider()
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"**Action:** `{action_title}` | **Language:** `{language}`")
    with col2:
        is_bookmarked = any(bm["response"] == response_text for bm in st.session_state["bookmarks"])
        if is_bookmarked:
            st.button("⭐ Saved", key=f"bm_saved_{key_prefix}", disabled=True, use_container_width=True)
        else:
            if st.button("⭐ Bookmark", key=f"bm_{key_prefix}", use_container_width=True):
                _add_bookmark(action_title, language, input_text, response_text)
                st.toast("Saved to study bookmarks! ⭐")
                st.rerun()

    st.markdown(response_text)


def _generate_markdown_study_guide() -> str:
    """Generate Markdown export for bookmarked study notes."""
    lines = [
        f"# 🎓 Student Buddy AI — Personal Study Notes & Explanations",
        f"*Exported on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "---",
        "",
    ]
    for i, bm in enumerate(st.session_state["bookmarks"], 1):
        lines.append(f"## {i}. {bm['action']} — {bm['language']}")
        lines.append(f"*Saved: {bm['timestamp']}*")
        lines.append("")
        lines.append("### Problem / Code Input:")
        lines.append("```")
        lines.append(bm["input"])
        lines.append("```")
        lines.append("")
        lines.append("### Tutor Explanation:")
        lines.append(bm["response"])
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


# ======================================================================
# Sidebar
# ======================================================================

with st.sidebar:
    st.markdown("## 🎓 Student Buddy AI")
    st.caption(f"v{config.APP_VERSION}")

    st.divider()

    # Navigation
    page = st.radio(
        "Navigate",
        options=[
            "💡 Problem Assistant",
            "🔍 Code Explainer",
            "🐛 Debugger",
            "📝 Practice Questions",
            "⭐ Bookmarks & Notes",
            "📜 Session History",
            "⚙️ Settings & Status",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Language selector (available on all pages)
    language = st.selectbox(
        "Programming Language",
        config.SUPPORTED_LANGUAGES,
        help="Select the programming language for your questions and code analysis.",
    )

    st.divider()

    # Mode indicator
    is_live = service.is_live_ai()
    if is_live:
        st.success("🟢 Live AI connected")
    else:
        st.warning("🟡 Demo mode (offline)")

    st.caption(
        f"**Language:** {language}\n\n"
        f"**Bookmarks:** {len(st.session_state.get('bookmarks', []))}\n\n"
        "Built with ❤️ for student learning & interview prep."
    )


# ======================================================================
# Main content area header
# ======================================================================

st.markdown(f'<p class="main-title">🎓 {config.APP_TITLE}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{config.APP_SUBTITLE}</p>', unsafe_allow_html=True)

mode_label = service.get_mode_label()
if service.is_live_ai():
    st.markdown(f'<div class="mode-banner mode-live">{mode_label}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="mode-banner mode-demo">{mode_label}</div>', unsafe_allow_html=True)


# ======================================================================
# PAGE: Problem Assistant (Hints + Approach)
# ======================================================================
if page == "💡 Problem Assistant":
    st.markdown("### 💡 Problem Assistant")
    st.markdown("Get progressive Socratic hints or understand the structured approach to solving a problem.")

    st.caption("Quick sample problems:")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    if q_col1.button("Two Sum", use_container_width=True):
        st.session_state["prefill_problem"] = "Given an array of integers and a target sum, return indices of the two numbers that add up to target."
        st.rerun()
    if q_col2.button("Reverse String", use_container_width=True):
        st.session_state["prefill_problem"] = "Write a function to reverse a string in-place without using built-in string reverse methods."
        st.rerun()
    if q_col3.button("Valid Parentheses", use_container_width=True):
        st.session_state["prefill_problem"] = "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid."
        st.rerun()
    if q_col4.button("Binary Search", use_container_width=True):
        st.session_state["prefill_problem"] = "Implement binary search to find an integer in a sorted array in O(log n) time."
        st.rerun()

    problem_text = st.text_area(
        "Describe your coding problem:",
        value=st.session_state.get("prefill_problem", ""),
        height=140,
        placeholder="Example: Write a function to find the second largest number in a list.",
        key="problem_input",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💡 Get a Hint", use_container_width=True, type="primary"):
            if problem_text.strip():
                key = problem_text.strip()[:200]
                current_level = st.session_state["hint_levels"].get(key, 0) + 1
                if current_level > config.MAX_HINT_LEVEL:
                    current_level = config.MAX_HINT_LEVEL
                st.session_state["hint_levels"][key] = current_level

                with st.spinner(f"Generating Hint {current_level}..."):
                    response = service.generate_hint(problem_text, language, current_level)
                _save_to_history(f"Hint (Level {current_level})", language, problem_text, response)
            else:
                st.warning("⚠️ Please enter a coding problem first.")

    with col2:
        if st.button("📝 Explain Approach", use_container_width=True):
            if problem_text.strip():
                with st.spinner("Generating approach explanation..."):
                    response = service.explain_approach(problem_text, language)
                _save_to_history("Approach Explanation", language, problem_text, response)
            else:
                st.warning("⚠️ Please enter a coding problem first.")

    # Hint progress indicator
    if problem_text.strip():
        key = problem_text.strip()[:200]
        level = st.session_state["hint_levels"].get(key, 0)
        if level > 0:
            progress = level / config.MAX_HINT_LEVEL
            st.progress(progress, text=f"Hint progress: {level}/{config.MAX_HINT_LEVEL}")
            if level >= config.MAX_HINT_LEVEL:
                st.info("✅ You've seen all 4 hint levels for this problem.")

    # Display response if available
    if st.session_state.get("last_response") and ("Hint" in st.session_state.get("last_action", "") or "Approach" in st.session_state.get("last_action", "")):
        _render_response_card(
            st.session_state["last_action"],
            st.session_state.get("last_language", language),
            st.session_state.get("last_input", problem_text),
            st.session_state["last_response"],
            key_prefix="problem_card",
        )


# ======================================================================
# PAGE: Code Explainer
# ======================================================================
elif page == "🔍 Code Explainer":
    st.markdown("### 🔍 Code Explainer")
    st.markdown("Paste your code below to get a line-by-line explanation, construct analysis, and complexity breakdown.")

    st.caption("Quick code templates:")
    c_col1, c_col2, c_col3, c_col4 = st.columns(4)
    if c_col1.button("Python: Memoization", use_container_width=True):
        st.session_state["prefill_code"] = "def fib(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fib(n-1, memo) + fib(n-2, memo)\n    return memo[n]"
        st.rerun()
    if c_col2.button("C++: Two Pointer", use_container_width=True):
        st.session_state["prefill_code"] = "#include <vector>\n#include <iostream>\nusing namespace std;\n\nvoid reverseVector(vector<int>& v) {\n    int l = 0, r = v.size() - 1;\n    while (l < r) {\n        swap(v[l++], v[r--]);\n    }\n}"
        st.rerun()
    if c_col3.button("Java: Binary Search", use_container_width=True):
        st.session_state["prefill_code"] = "public class Search {\n    public static int binarySearch(int[] arr, int target) {\n        int low = 0, high = arr.length - 1;\n        while (low <= high) {\n            int mid = low + (high - low) / 2;\n            if (arr[mid] == target) return mid;\n            else if (arr[mid] < target) low = mid + 1;\n            else high = mid - 1;\n        }\n        return -1;\n    }\n}"
        st.rerun()
    if c_col4.button("JS: Filter & Map", use_container_width=True):
        st.session_state["prefill_code"] = "const getEvenSquares = (nums) => {\n    return nums\n        .filter(n => n % 2 === 0)\n        .map(n => n * n);\n};"
        st.rerun()

    code_input = st.text_area(
        "Paste your code here:",
        value=st.session_state.get("prefill_code", ""),
        height=220,
        placeholder="Paste your code snippet here...",
        key="explain_code_input",
    )

    if st.button("🔍 Explain Code", use_container_width=True, type="primary"):
        if code_input.strip():
            with st.spinner("Analyzing code..."):
                response = service.explain_code(code_input, language)
            _save_to_history("Code Explanation", language, code_input, response)
        else:
            st.warning("⚠️ Please paste your code first.")

    if st.session_state.get("last_response") and st.session_state.get("last_action") == "Code Explanation":
        _render_response_card(
            "Code Explanation",
            st.session_state.get("last_language", language),
            st.session_state.get("last_input", code_input),
            st.session_state["last_response"],
            key_prefix="explain_card",
        )


# ======================================================================
# PAGE: Debugger
# ======================================================================
elif page == "🐛 Debugger":
    st.markdown("### 🐛 Debugging Assistant")
    st.markdown("Paste your code and error message to diagnose issues, understand the root cause, and see how to fix it.")

    st.caption("Quick buggy snippets:")
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    if d_col1.button("Python Bug", use_container_width=True):
        st.session_state["prefill_code"] = "def calculate_sum(nums)\n    total = 0\n    for i in range(len(nums) + 1):\n        total = total + nums[i]\n    return total"
        st.session_state["prefill_error"] = "SyntaxError: expected ':' on line 1"
        st.rerun()
    if d_col2.button("C++ Bug", use_container_width=True):
        st.session_state["prefill_code"] = "int main() {\n    int x = 10\n    cout << x << endl;\n    return 0;\n}"
        st.session_state["prefill_error"] = "error: expected ';' before 'cout'"
        st.rerun()
    if d_col3.button("Java Bug", use_container_width=True):
        st.session_state["prefill_code"] = "public class Buggy {\n    public static void main(String[] args) {\n        String text = null;\n        system.out.println(text.length());\n    }\n}"
        st.session_state["prefill_error"] = "NullPointerException: Cannot invoke 'String.length()' because 'text' is null"
        st.rerun()
    if d_col4.button("JavaScript Bug", use_container_width=True):
        st.session_state["prefill_code"] = "const user = null;\nconsole.log(user.name);\nif (x == 5) {\n    print('match');\n}"
        st.session_state["prefill_error"] = "TypeError: Cannot read properties of null (reading 'name')"
        st.rerun()

    debug_code_input = st.text_area(
        "Paste your code here:",
        value=st.session_state.get("prefill_code", ""),
        height=180,
        placeholder="Paste the code that has an issue...",
        key="debug_code_input",
    )

    error_message = st.text_input(
        "Error message (optional but recommended):",
        value=st.session_state.get("prefill_error", ""),
        placeholder="e.g., NameError: name 'x' is not defined",
        key="error_message_input",
    )

    if st.button("🐛 Debug My Code", use_container_width=True, type="primary"):
        if debug_code_input.strip():
            with st.spinner("Analyzing code for issues..."):
                response = service.debug_code(debug_code_input, language, error_message)
            _save_to_history("Debug", language, debug_code_input, response)
        else:
            st.warning("⚠️ Please paste your code first.")

    if st.session_state.get("last_response") and st.session_state.get("last_action") == "Debug":
        _render_response_card(
            "Debug",
            st.session_state.get("last_language", language),
            st.session_state.get("last_input", debug_code_input),
            st.session_state["last_response"],
            key_prefix="debug_card",
        )


# ======================================================================
# PAGE: Practice Questions
# ======================================================================
elif page == "📝 Practice Questions":
    st.markdown("### 📝 Practice Questions")
    st.markdown("Browse curated coding exercises across 10 essential data structure and algorithmic topics.")
    st.caption("📌 These questions are hand-curated exercises covering core technical interview patterns.")

    col_topic, col_diff = st.columns(2)

    topics = [
        "All",
        "Variables and Conditions",
        "Loops",
        "Strings",
        "Lists and Arrays",
        "Dictionaries and Hash Maps",
        "Functions",
        "Basic Mathematics",
        "Searching and Sorting",
        "Stacks and Queues",
        "Recursion and Trees",
    ]
    difficulties = ["All", "Easy", "Medium", "Hard"]

    with col_topic:
        selected_topic = st.selectbox("Topic", topics, key="practice_topic")
    with col_diff:
        selected_difficulty = st.selectbox("Difficulty", difficulties, key="practice_diff")

    questions = service.get_practice_questions(selected_topic, selected_difficulty)

    if questions:
        st.markdown(f"**Showing {len(questions)} question(s)**")
        for i, q in enumerate(questions):
            diff_class = f"difficulty-{q['difficulty'].lower()}"
            with st.expander(f"📌 {q['title']}  —  {q['topic']} ({q['difficulty']})"):
                st.markdown(f"**Difficulty:** <span class='{diff_class}'>{q['difficulty']}</span> | **Topic:** `{q['topic']}`", unsafe_allow_html=True)
                st.divider()
                st.markdown(f"**Problem:**\n\n{q['statement']}")
                st.markdown(f"**Example Input:**\n```\n{q['example_input']}\n```")
                st.markdown(f"**Example Output:**\n```\n{q['example_output']}\n```")

                if st.button("💡 Solve in Problem Assistant", key=f"solve_btn_{i}"):
                    st.session_state["prefill_problem"] = f"{q['title']}: {q['statement']}"
                    st.toast("Transferred to Problem Assistant! Switch to the Problem Assistant tab to begin.")
    else:
        st.info("No questions match your filters. Try a different topic or difficulty.")


# ======================================================================
# PAGE: Bookmarks & Study Notes
# ======================================================================
elif page == "⭐ Bookmarks & Notes":
    st.markdown("### ⭐ Bookmarks & Personal Study Notes")
    st.markdown("Review and export your saved explanations, algorithm breakdowns, and debugging tips.")

    bookmarks = st.session_state.get("bookmarks", [])

    if not bookmarks:
        st.info("You haven't bookmarked any explanations yet. Click ⭐ **Bookmark** on any response to save it here for exam and interview review!")
    else:
        col_hdr, col_dl, col_del = st.columns([3, 2, 1])
        with col_hdr:
            st.markdown(f"**{len(bookmarks)} saved note(s)**")
        with col_dl:
            study_md = _generate_markdown_study_guide()
            st.download_button(
                label="📥 Download Notes (.md)",
                data=study_md,
                file_name="student_buddy_study_notes.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_del:
            if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                st.session_state["bookmarks"] = []
                st.rerun()

        for idx, item in enumerate(bookmarks):
            with st.expander(f"📌 {item['action']} — {item['language']} ({item['timestamp']})", expanded=(idx == 0)):
                st.markdown(f"**Saved on:** `{item['timestamp']}`")
                st.markdown("**Original Question / Code:**")
                st.code(item["input"], language=None)
                st.markdown("**Tutor Response:**")
                st.markdown(item["response"])


# ======================================================================
# PAGE: Session History
# ======================================================================
elif page == "📜 Session History":
    st.markdown("### 📜 Session History")
    st.markdown("Review your recent interactions from this session.")

    history = st.session_state.get("history", [])

    if not history:
        st.info("No interactions yet in this session. Start by asking a question or debugging some code!")
    else:
        col_info, col_clear = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{len(history)} interaction(s)** recorded.")
        with col_clear:
            if st.button("🗑️ Clear History", type="secondary", use_container_width=True):
                st.session_state["history"] = []
                st.session_state["hint_levels"] = {}
                if db.is_available:
                    db.clear_history(st.session_state["session_id"])
                st.rerun()

        for i, entry in enumerate(history):
            with st.expander(
                f"**{entry['action']}** — {entry['language']} — {entry['timestamp']}",
                expanded=(i == 0),
            ):
                st.markdown(f"**Question / Code:**")
                st.code(entry["question"][:500], language=None)
                st.markdown(f"**Response:**")
                st.markdown(entry["response"])


# ======================================================================
# PAGE: Settings & Status
# ======================================================================
elif page == "⚙️ Settings & Status":
    st.markdown("### ⚙️ Settings & Status")

    # AI Provider status
    st.markdown("#### AI Provider")
    provider_name = service.get_provider_name()
    st.markdown(f"**Active provider:** {provider_name}")
    st.markdown(f"**Is live AI:** {'✅ Yes (HTTP API active)' if service.is_live_ai() else '❌ No (Demo mode)'}")

    if not service.is_live_ai():
        st.info(
            "The application is running in **demo mode** using built‑in rules "
            "and curated responses.  To connect a live AI provider, configure "
            "your API key in `.streamlit/secrets.toml`. See the README for "
            "instructions."
        )

    st.divider()

    # Database status
    st.markdown("#### Database (MySQL)")
    if db.is_available:
        st.success("✅ MySQL is connected. Interactions are being persisted.")
    else:
        st.warning(f"⚠️ {db.error_message}")
        st.info(
            "The app works perfectly without MySQL. Your session history is "
            "stored in memory. To enable persistence, configure MySQL "
            "credentials in `.streamlit/secrets.toml`."
        )

    st.divider()

    # Session info
    st.markdown("#### Session & Study Stats")
    st.markdown(f"**Session ID:** `{st.session_state['session_id']}`")
    st.markdown(f"**Interactions this session:** {len(st.session_state.get('history', []))}")
    st.markdown(f"**Saved study bookmarks:** {len(st.session_state.get('bookmarks', []))}")
    st.markdown(f"**Problems with hints tracked:** {len(st.session_state.get('hint_levels', {}))}")

    st.divider()

    # App info
    st.markdown("#### Application Info")
    st.markdown(f"**Version:** {config.APP_VERSION}")
    st.markdown(f"**Supported languages:** {', '.join(config.SUPPORTED_LANGUAGES)}")
    st.markdown(f"**Curated practice questions:** 49 problems")
    st.markdown(f"**Max hint levels:** {config.MAX_HINT_LEVEL}")
