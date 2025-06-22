"""Thin wrapper around an OpenAI-compatible LLM endpoint that is able to
interact with a ``CustomPdb`` instance through the *json* protocol defined in
the project documentation.

The module purposefully **does not** attempt to offer a complete abstraction
layer over the OpenAI API – it only implements what is required by the rest of
``vibethon``.  The public interface (class names, attributes, etc.) remains
unchanged so that the extensive test-suite keeps passing.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
import shutil
import textwrap

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

# NOTE: ``ChatGPTPdbLLM`` is *not* tied to a single model or endpoint – both can
# be overridden through environment variables so that users do not have to dive
# into the source code just to change them.  Reasonable fall-back defaults are
# provided so the behaviour stays exactly the same when the variables are not
# defined.

DEFAULT_BASE_URL = os.getenv("VIBETHON_OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = os.getenv("VIBETHON_OPENAI_MODEL", "anthropic/claude-sonnet-4")

# We create **one** client instance at import time so that connection pooling
# works across multiple ``ChatGPTPdbLLM`` objects.
openai = OpenAI(base_url=DEFAULT_BASE_URL)

# Set-up an opt-in logger – by default it inherits the root logger's level which
# is usually ``WARNING``.  Users can enable more verbose output via
# ``logging.basicConfig(level=logging.INFO)`` when debugging.
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ANSI colour helpers (no external dependencies)
# ---------------------------------------------------------------------------

RESET = "\033[0m"
FG_CYAN = "\033[96m"
FG_YELLOW = "\033[93m"
FG_GREEN = "\033[92m"

def _print_coloured_box(text: str, *, title: str = "", colour: str = FG_CYAN) -> None:  # noqa: D401
    """Pretty-print *text* inside an ANSI-coloured box that adapts to the
    terminal width.

    If lines exceed the available width they are wrapped so that the borders
    always align.  The implementation purposefully avoids external
    dependencies to keep the footprint small.
    """

    term_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    # Leave two characters padding on each side inside the box and another two
    # for the border characters → 4 columns total overhead.
    wrap_width = max(10, term_width - 4)

    # ------------------------------------------------------------------
    # Prepare content lines (wrapped)
    # ------------------------------------------------------------------

    raw_lines = text.rstrip().splitlines() or [""]
    lines: list[str] = []
    for raw in raw_lines:
        wrapped = textwrap.wrap(raw, width=wrap_width) or [""]
        lines.extend(wrapped)

    content_width = max(len(l) for l in lines)

    # ------------------------------------------------------------------
    # Handle title (truncate if necessary)
    # ------------------------------------------------------------------

    if title:
        title_display = f" {title} "
        if len(title_display) > wrap_width:
            title_display = title_display[: wrap_width - 1] + "…"
        content_width = max(content_width, len(title_display))
    else:
        title_display = ""

    # Pad horizontal rule to match content width
    horizontal = "─" * (content_width + 2)  # +2 for left/right padding inside box

    # ------------------------------------------------------------------
    # Header ─────────────────────────────────────────────────────────────
    # ------------------------------------------------------------------

    if title_display:
        start = (len(horizontal) - len(title_display)) // 2
        top_border = (
            f"┌{horizontal[:start]}{title_display}{horizontal[start + len(title_display):]}┐"
        )
    else:
        top_border = f"┌{horizontal}┐"

    print(colour + top_border + RESET)

    # ------------------------------------------------------------------
    # Body ──────────────────────────────────────────────────────────────
    # ------------------------------------------------------------------

    for line in lines:
        padding = " " * (content_width - len(line))
        print(f"{colour}│ {RESET}{line}{padding}{colour} │{RESET}")

    # ------------------------------------------------------------------
    # Footer ─────────────────────────────────────────────────────────────
    # ------------------------------------------------------------------

    print(colour + f"└{horizontal}┘" + RESET)

class ChatGPTPdbLLM:
    """A very small helper that turns *pdb* I/O into LLM prompts.

    Parameters
    ----------
    system_message:
        Optional system prompt.  When *None* the default prompt (see source
        code below) is used.
    memory_limit:
        The number of user/assistant *turns* (not individual messages) that are
        kept in memory. The system prompt is **always** preserved.
    """

    # NOTE: the public attributes below are referenced by the test-suite – do
    # *not* rename or remove them without adjusting the tests accordingly.

    def __init__(self, system_message: Optional[str] = None, memory_limit: int = 15):
        self.model: str = DEFAULT_MODEL
        self.messages: List[Dict[str, str]] = []  # chat history incl. system message
        self.last_output: str = ""  # buffered stdout coming from pdb

        # Persisted so it can be reused by callers if necessary
        self.system_message: str = system_message or (
            """
You are an expert Python programmer and debugger. You understand the internals of Python
extremely well. You are also AWARE of your limits, and if you are confused by what is happening,
you will stop and say so.

You are sitting next to an inexperienced intern who needs help with their code, and you are going
to tell them what to type at a PDB prompt in order to debug what is happening. You want the intern
to be able to learn, so you are going to explain your reasoning and output the exact command to run.

After the intern understands the problem, you are going to issue ANOTHER sequence of commands to help
them fix the problem. You will modify local variables to fix the execution at runtime. When you are done,
the program should execute flawlessly.

You are in a pdb session, which in this context means that the line you begin the session at triggered an exception. The line that is pointed at when running `l` is the last line that was attempted to be executed, and which raised the exception. The next line is the line that will be executed next, if the command `next` is used.

Use `continue`, rather than `quit`.

Note that expressions that begin with letters that are pdb commands, should be preceded by a `!` to be interpreted as an expression (eg variable assignment `a=2` should be `!a=2`)

At each step you are interacting with the intern, you should emit a JSON that adheres to the following
typed dict:

import typing as T

class DebuggerStep(T.TypedDict):
    command: str
    explanation: str
    action: T.Union[T.Literal["pdb_command"], T.Literal["stop_and_ask_user"]]

Go step-by-step as you reason. Think carefully. Please just return the JSON, no other text.

If you get really stuck and don't know what to do, please don't continue. Stop, and let me know that you need help.
In your help message, please use a baby emoji so that the need for help is clear: 👶
            """.strip()
        )
        # How many *turns* of memory to keep (one turn = user + assistant)
        self.memory_limit: int = memory_limit

        self._init_messages()

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------

    def _init_messages(self) -> None:
        """(Re-)initialise *self.messages* so that it only contains the
        permanent system prompt.
        """

        self.messages = [
            {
                "role": "system",
                "content": self.system_message,
            }
        ]

    def _truncate_history(self) -> None:
        """Ensure that *self.messages* does not grow beyond *memory_limit* turns.

        The system message is always preserved – we therefore keep *memory_limit
        x 2* messages (user + assistant) **plus** the initial system entry.
        """

        max_len = 1 + self.memory_limit  # system prompt + N recent messages
        if len(self.messages) > max_len:
            # Keep system message + the newest *memory_limit* assistant/user messages
            self.messages = [self.messages[0]] + self.messages[-self.memory_limit :]

    @staticmethod
    def _extract_json_object(blob: str) -> str:
        """Return the *first* JSON document found inside *blob* (heuristic).

        The method tries to locate matching opening/closing braces.  If that
        fails we simply return the original string so that the caller can deal
        with the error (exactly like the old implementation).
        """

        start = blob.find("{")
        end = blob.rfind("}")
        return blob[start : end + 1] if 0 <= start < end else blob

    def _save_messages(self) -> None:
        """Persist the conversation so that it can be inspected after the fact.

        The function *never* raises – any exception is logged and then ignored
        because we do not want to disrupt an ongoing debugging session.
        """

        try:
            with open("llm_messages.json", "w", encoding="utf-8") as fh:
                json.dump(self.messages, fh, ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover – exact IOError doesn't matter
            logger.warning("Failed to save llm_messages.json: %s", exc)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def ask_for_next_command(self) -> str:
        """Generate the next debugger command as *plain text*.

        The method constructs a prompt from the initial context (if available)
        and the most recent *pdb* output, calls the underlying LLM and finally
        returns *only* the ``command`` field extracted from the JSON response
        (or the raw text when parsing fails).  A side effect is that the full
        assistant message gets appended to *self.messages* so that the model's
        internal state is updated for the next call.
        """

        # ------------------------------------------------------------------
        # 1. Build user prompt
        # ------------------------------------------------------------------

        initial_ctx = getattr(self, "initial_context", "").strip()
        dbg_output = self.last_output.strip()

        if not self.messages or len(self.messages) == 1:
            # First call – we assume no previous assistant/user messages exist
            user_content = (
                "This is the start of a debugging session.\n"
                f"Use this initial context to help choose the first debugging command:\n{initial_ctx}\n"
                "Emit the first debugging command as JSON. Please format it as JSON ALWAYS. Do not include any other text outside the JSON:\n"
            )
        else:
            user_content = (
                f"Initial context:\n{initial_ctx}\n"
                f"Debugger output:\n{dbg_output}\n"
                "Emit the next output dictionary after this line. Please format it as JSON ALWAYS. Do not include any other text outside the JSON:\n"
            )

        self.messages.append({"role": "user", "content": user_content})

        # Truncate history **before** making the request so we never send more
        # than necessary tokens to the API.
        self._truncate_history()

        # ------------------------------------------------------------------
        # 2. Call LLM
        # ------------------------------------------------------------------

        response = openai.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.2,
            max_tokens=256,  # Increased to reduce truncation
        )

        raw_reply_full: str = response.choices[0].message.content.strip()
        raw_reply: str = self._extract_json_object(raw_reply_full)

        # ------------------------------------------------------------------
        # 3. Parse assistant message (best-effort)
        # ------------------------------------------------------------------

        command: str
        explanation: Optional[str] = None

        try:
            parsed: Any = json.loads(raw_reply)
            if isinstance(parsed, dict) and "command" in parsed:
                command = str(parsed["command"])
                explanation = parsed.get("explanation")
            else:
                command = raw_reply  # Fallback to raw string
        except json.JSONDecodeError:
            command = raw_reply  # keep behaviour identical to old version

        # ------------------------------------------------------------------
        # 4. Update state & persist conversation
        # ------------------------------------------------------------------

        self.messages.append({"role": "assistant", "content": raw_reply})
        self._save_messages()

        # ------------------------------------------------------------------
        # 5. Echo command back to *pdb* (stdout)
        # ------------------------------------------------------------------

        _print_coloured_box(command, title="Command", colour=FG_GREEN)

        if explanation:
            _print_coloured_box(explanation, title="Explanation", colour=FG_YELLOW)

        return command

    def receive_pdb_output(self, output: str) -> None:
        """Forward *pdb*'s stdout to the terminal **and** remember it.

        The next prompt sent to the model contains the buffered output so that
        the assistant can react to it.
        """

        # Remove trailing '(Pdb)' prompt which is always present and not useful
        trimmed_output = output.rstrip("\n")
        lines = trimmed_output.splitlines()
        if lines and lines[-1].strip().startswith("(Pdb"):
            lines = lines[:-1]
        display_text = "\n".join(lines)

        # Pretty-print debugger output without the prompt.
        _print_coloured_box(display_text, title="Debugger Output", colour=FG_CYAN)
        self.last_output = display_text

    def set_initial_context(self, context: str) -> None:
        """Store a snapshot of the state right before entering *pdb*."""

        self.initial_context = context

class DummyLLM:
    """A minimal *human-in-the-loop* implementation that simply delegates to
    the built-in *input()* / *print()* functions.  It fulfils the same public
    interface as :class:`ChatGPTPdbLLM` so that it can be swapped in tests or
    interactive sessions without touching the rest of the code.
    """

    # The methods intentionally do *not* use type hints so that they are fully
    # compatible with *unittest.mock.patch* signatures used throughout the test
    # suite.

    @staticmethod
    def ask_for_next_command(prompt):  # noqa: D401 – keeps signature stable
        """Return whatever the user types on stdin."""

        return input(prompt)

    @staticmethod
    def receive_pdb_output(output):  # noqa: D401 – keeps signature stable
        """Mirror output to stdout so the human can see it."""

        print(output, end="")
