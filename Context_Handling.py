
from dataclasses import dataclass, field
from typing import Optional
import re


# ─────────────────────────────────────────────
# 1. Data Structures
# ─────────────────────────────────────────────

@dataclass
class ConversationState:
    """
    Minimal state kept between turns.
    Only stores what's necessary to resolve follow-up references.
    """
    last_topic: Optional[str] = None          # e.g. "exam", "fee", "schedule"
    last_entity: Optional[str] = None         # e.g. "third year", "CSE"
    pending_slot: Optional[str] = None        # slot the bot is waiting to fill
    turn_history: list = field(default_factory=list)   # (user, bot) pairs

    def update(self, topic=None, entity=None, pending=None):
        if topic:
            self.last_topic = topic
        if entity:
            self.last_entity = entity
        self.pending_slot = pending  # always overwrite (None clears it)

    def add_turn(self, user_msg: str, bot_response: str):
        self.turn_history.append({"user": user_msg, "bot": bot_response})
        if len(self.turn_history) > 10:          # keep last 10 turns only
            self.turn_history.pop(0)

    def reset(self):
        self.last_topic = None
        self.last_entity = None
        self.pending_slot = None


# ─────────────────────────────────────────────
# 2. Knowledge Base  (mock data)
# ─────────────────────────────────────────────

KNOWLEDGE_BASE = {
    "exam": {
        "first year":  "First-year exams begin on **May 15th** (Theory) and **May 22nd** (Practicals).",
        "second year": "Second-year exams begin on **May 20th** (Theory) and **May 28th** (Practicals).",
        "third year":  "Third-year exams begin on **June 1st** (Theory) and **June 8th** (Practicals).",
        "fourth year": "Fourth-year exams begin on **June 10th** (Theory) and **June 17th** (Practicals).",
    },
    "fee": {
        "first year":  "First-year tuition fee is **₹85,000** per semester.",
        "second year": "Second-year tuition fee is **₹87,000** per semester.",
        "third year":  "Third-year tuition fee is **₹89,000** per semester.",
        "fourth year": "Fourth-year tuition fee is **₹91,000** per semester.",
    },
    "schedule": {
        "first year":  "First-year classes run **Mon–Fri, 9 AM – 4 PM**.",
        "second year": "Second-year classes run **Mon–Fri, 9 AM – 5 PM**.",
        "third year":  "Third-year classes run **Mon–Sat, 8 AM – 5 PM** (lab days on Sat).",
        "fourth year": "Fourth-year schedule varies by elective. Check the notice board.",
    },
    "result": {
        "first year":  "First-year results are declared within **45 days** after exams.",
        "second year": "Second-year results are declared within **40 days** after exams.",
        "third year":  "Third-year results are declared within **35 days** after exams.",
        "fourth year": "Fourth-year results are declared within **30 days** after exams.",
    },
}

TOPIC_ALIASES = {
    "exam": ["exam", "test", "examination", "exams"],
    "fee":  ["fee", "fees", "tuition", "cost", "payment"],
    "schedule": ["schedule", "timetable", "timing", "class", "classes"],
    "result": ["result", "results", "marks", "score", "scores"],
}

YEAR_ALIASES = {
    "first year":  ["1st", "first", "1", "year 1", "first year", "fy"],
    "second year": ["2nd", "second", "2", "year 2", "second year", "sy"],
    "third year":  ["3rd", "third", "3", "year 3", "third year", "ty"],
    "fourth year": ["4th", "fourth", "4", "year 4", "fourth year", "be final", "final year"],
}


# ─────────────────────────────────────────────
# 3. Extraction Helpers
# ─────────────────────────────────────────────

def extract_topic(text: str) -> Optional[str]:
    """Return the canonical topic name found in text, or None."""
    text_lower = text.lower()
    for canonical, aliases in TOPIC_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            return canonical
    return None


def extract_year(text: str) -> Optional[str]:
    """Return the canonical year string found in text, or None."""
    text_lower = text.lower()
    for canonical, aliases in YEAR_ALIASES.items():
        if any(alias in text_lower for alias in aliases):
            return canonical
    return None


# ─────────────────────────────────────────────
# 4. Core Response Builder
# ─────────────────────────────────────────────

def build_response(topic: str, year: str) -> str:
    """Fetch answer from knowledge base."""
    topic_data = KNOWLEDGE_BASE.get(topic)
    if not topic_data:
        return f"Sorry, I don't have information about '{topic}' yet."
    answer = topic_data.get(year)
    if not answer:
        return f"I don't have {topic} details for '{year}'. Try: first, second, third, or fourth year."
    return answer


# ─────────────────────────────────────────────
# 5. Main Context-Aware Chatbot Logic
# ─────────────────────────────────────────────

class ContextualChatbot:
    """
    A chatbot that maintains minimal state across turns to resolve
    follow-up questions correctly.
    """

    GREETING_PATTERNS = re.compile(
        r"\b(hi|hello|hey|good morning|good afternoon|good evening)\b", re.I
    )
    RESET_PATTERNS = re.compile(
        r"\b(reset|start over|new question|clear|forget)\b", re.I
    )
    HELP_PATTERNS = re.compile(
        r"\b(help|what can you|what do you know|topics|options)\b", re.I
    )

    def __init__(self):
        self.state = ConversationState()

    # ── public entry point ──────────────────

    def chat(self, user_input: str) -> str:
        user_input = user_input.strip()
        if not user_input:
            return "Please type something so I can help you!"

        response = self._route(user_input)
        self.state.add_turn(user_input, response)
        return response

    # ── routing ─────────────────────────────

    def _route(self, text: str) -> str:
        # Special commands first
        if self.GREETING_PATTERNS.search(text):
            return self._greet()
        if self.RESET_PATTERNS.search(text):
            self.state.reset()
            return "Conversation context cleared. How can I help you?"
        if self.HELP_PATTERNS.search(text):
            return self._help()

        detected_topic = extract_topic(text)
        detected_year  = extract_year(text)

        # ── Case 1: Both topic AND year in one message ──────────────
        if detected_topic and detected_year:
            self.state.update(topic=detected_topic, entity=detected_year, pending=None)
            return build_response(detected_topic, detected_year)

        # ── Case 2: Topic only – need year (ask for it) ─────────────
        if detected_topic and not detected_year:
            self.state.update(topic=detected_topic, pending="year")
            return (
                f"Sure! Which year are you asking about the **{detected_topic}** for?\n"
                "(e.g., first, second, third, or fourth year)"
            )

        # ── Case 3: Year only – resolve against remembered topic ────
        if detected_year and not detected_topic:
            if self.state.last_topic:
                # Fulfill the pending follow-up
                topic = self.state.last_topic
                self.state.update(entity=detected_year, pending=None)
                return build_response(topic, detected_year)
            else:
                # Year given but no remembered topic → ask for topic
                self.state.update(entity=detected_year, pending="topic")
                return (
                    f"Got it — you're asking about **{detected_year}**. "
                    "What specifically would you like to know?\n"
                    "(exam dates, fee, schedule, or results)"
                )

        # ── Case 4: Neither detected – handle pending slots ──────────
        if self.state.pending_slot == "year":
            # Bot previously asked for a year, user might have said something informal
            return (
                f"I didn't catch which year. Please say something like "
                f"'first year' or 'third year' for the **{self.state.last_topic}** info."
            )

        if self.state.pending_slot == "topic":
            return (
                f"I didn't catch the topic for **{self.state.last_entity}**. "
                "Try: exam, fee, schedule, or result."
            )

        # ── Case 5: Completely unrecognised ──────────────────────────
        return (
            "I'm not sure what you mean. I can help with:\n"
            "  • Exam dates  • Fees  • Class schedule  • Results\n"
            "Try asking: *'When is the third year exam?'*"
        )

    # ── static responses ────────────────────

    @staticmethod
    def _greet() -> str:
        return (
            "Hello! 👋 I'm your college information assistant.\n"
            "Ask me about exam dates, fees, schedules, or results for any year."
        )

    @staticmethod
    def _help() -> str:
        return (
            "I can answer questions about:\n"
            "  📅 **Exams**    – 'When is the exam for third year?'\n"
            "  💰 **Fees**     – 'What is the fee for second year?'\n"
            "  🕐 **Schedule** – 'What is the class schedule for first year?'\n"
            "  📊 **Results**  – 'When are fourth year results declared?'\n\n"
            "You can also ask follow-ups like:\n"
            "  Q: 'When is the exam?'  →  A: (asks which year)\n"
            "  Q: 'Third year'         →  A: (answers with context)"
        )

    # ── debug helper ────────────────────────

    def get_state_summary(self) -> dict:
        return {
            "last_topic":   self.state.last_topic,
            "last_entity":  self.state.last_entity,
            "pending_slot": self.state.pending_slot,
            "turns_so_far": len(self.state.turn_history),
        }


# ─────────────────────────────────────────────
# 6. Demo / Interactive REPL
# ─────────────────────────────────────────────

def run_demo():
    """Run a scripted demo showing multi-turn context handling."""
    bot = ContextualChatbot()

    demo_conversations = [
        # --- Scenario 1: Follow-up year after topic ---
        ("=== Scenario 1: Topic first, then year follow-up ===", None),
        ("When is the exam?",    None),
        ("For third year?",      None),

        # --- Scenario 2: Year first, then topic follow-up ---
        ("=== Scenario 2: Year first, topic follow-up ===", None),
        ("Second year",          None),
        ("What about fees?",     None),

        # --- Scenario 3: Complete question in one shot ---
        ("=== Scenario 3: Full question, no follow-up needed ===", None),
        ("What is the fee for first year?", None),

        # --- Scenario 4: Context switch ---
        ("=== Scenario 4: Switching topics mid-conversation ===", None),
        ("When are results declared?", None),
        ("fourth year",          None),
        ("What about the schedule?", None),  # new topic – should ask year
        ("same year",            None),      # informal; won't match → clarify

        # --- Scenario 5: Greeting + help ---
        ("=== Scenario 5: Greeting and help ===", None),
        ("Hello",                None),
        ("What can you do?",     None),
    ]

    print("\n" + "═" * 60)
    print("  CONTEXT-AWARE COLLEGE CHATBOT DEMO")
    print("═" * 60)

    for item, _ in demo_conversations:
        if item.startswith("==="):
            bot.state.reset()        # fresh context for each scenario
            print(f"\n{item}")
            print("─" * 50)
        else:
            print(f"\n  You : {item}")
            reply = bot.chat(item)
            # Pretty-print multi-line replies
            for i, line in enumerate(reply.split("\n")):
                prefix = "  Bot : " if i == 0 else "        "
                print(f"{prefix}{line}")
            # Show minimal state
            state = bot.get_state_summary()
            print(f"  [state] topic={state['last_topic']!r}  "
                  f"entity={state['last_entity']!r}  "
                  f"pending={state['pending_slot']!r}")


def run_interactive():
    """Interactive REPL for manual testing."""
    bot = ContextualChatbot()
    print("\n" + "═" * 60)
    print("  COLLEGE CHATBOT  (type 'quit' to exit, 'state' to inspect)")
    print("═" * 60 + "\n")

    while True:
        try:
            user_input = input("You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("quit", "exit", "bye"):
            print("Bot : Goodbye! 👋")
            break

        if user_input.lower() == "state":
            print(f"[state] {bot.get_state_summary()}")
            continue

        if not user_input:
            continue

        response = bot.chat(user_input)
        print(f"Bot : {response}\n")


# ─────────────────────────────────────────────
# 7. Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive()
    else:
        run_demo()
        print("\n" + "─" * 60)
        print("Run with --interactive flag for a live chat session.")
        print("─" * 60 + "\n")
