
from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from difflib import get_close_matches
from enum import Enum, auto
from typing import Optional


# ══════════════════════════════════════════════════════════════════
# 1.  ENUMERATIONS & CONSTANTS
# ══════════════════════════════════════════════════════════════════

class Intent(Enum):
    EXAM        = auto()
    FEE         = auto()
    SCHEDULE    = auto()
    RESULT      = auto()
    ADMISSION   = auto()
    HOSTEL      = auto()
    SCHOLARSHIP = auto()
    CONTACT     = auto()
    HUMAN       = auto()   # user explicitly wants a human
    GREETING    = auto()
    HELP        = auto()
    UNKNOWN     = auto()


class FallbackStage(Enum):
    """Escalation ladder."""
    NONE         = 0   # no failure yet
    CLARIFY      = 1   # first miss  → ask clarifying question
    SUGGEST      = 2   # second miss → offer topic suggestions
    HANDOVER     = 3   # third miss  → route to human advisor


HANDOVER_INFO = {
    "email":   "advisor@college.edu",
    "portal":  "https://college.edu/helpdesk",
    "desk":    "Admin Block, Room 101, Mon–Fri 9 AM – 5 PM",
    "phone":   "+91-712-000-1234",
}

MAX_HISTORY = 12   # rolling window size


# ══════════════════════════════════════════════════════════════════
# 2.  KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════

KB: dict[Intent, dict] = {
    Intent.EXAM: {
        "first year":  "First-year exams: Theory **May 15**, Practicals **May 22**.",
        "second year": "Second-year exams: Theory **May 20**, Practicals **May 28**.",
        "third year":  "Third-year exams: Theory **June 1**, Practicals **June 8**.",
        "fourth year": "Fourth-year exams: Theory **June 10**, Practicals **June 17**.",
        "_general":    "Exam dates differ by year. Which year are you asking about?",
    },
    Intent.FEE: {
        "first year":  "First-year tuition: **₹85,000/semester**.",
        "second year": "Second-year tuition: **₹87,000/semester**.",
        "third year":  "Third-year tuition: **₹89,000/semester**.",
        "fourth year": "Fourth-year tuition: **₹91,000/semester**.",
        "_general":    "Fees vary by year. Which year would you like details for?",
    },
    Intent.SCHEDULE: {
        "first year":  "First-year: Mon–Fri, 9 AM – 4 PM.",
        "second year": "Second-year: Mon–Fri, 9 AM – 5 PM.",
        "third year":  "Third-year: Mon–Sat, 8 AM – 5 PM (Saturday = lab day).",
        "fourth year": "Fourth-year: varies by elective — check the notice board.",
        "_general":    "Schedules vary by year. Which year are you asking about?",
    },
    Intent.RESULT: {
        "first year":  "First-year results within **45 days** of exams.",
        "second year": "Second-year results within **40 days** of exams.",
        "third year":  "Third-year results within **35 days** of exams.",
        "fourth year": "Fourth-year results within **30 days** of exams.",
        "_general":    "Results timelines differ by year. Which year are you asking about?",
    },
    Intent.ADMISSION: {
        "_general": (
            "Admissions open every June. Apply at https://college.edu/admissions. "
            "Documents required: 10th & 12th marksheets, ID proof, passport photo."
        ),
    },
    Intent.HOSTEL: {
        "_general": (
            "Hostel seats are limited. Apply via the student portal. "
            "Fees: **₹40,000/year** (double-occupancy). Contact: hostel@college.edu"
        ),
    },
    Intent.SCHOLARSHIP: {
        "_general": (
            "Merit scholarships available for students scoring >75 % in the previous year. "
            "Apply at https://college.edu/scholarships before July 31."
        ),
    },
    Intent.CONTACT: {
        "_general": (
            f"📧 Email  : {HANDOVER_INFO['email']}\n"
            f"🌐 Portal : {HANDOVER_INFO['portal']}\n"
            f"🏢 Desk   : {HANDOVER_INFO['desk']}\n"
            f"📞 Phone  : {HANDOVER_INFO['phone']}"
        ),
    },
}

# Map keyword lists → Intent
INTENT_PATTERNS: list[tuple[Intent, list[str]]] = [
    (Intent.EXAM,        ["exam", "test", "examination", "paper", "papers"]),
    (Intent.FEE,         ["fee", "fees", "tuition", "cost", "payment", "pay"]),
    (Intent.SCHEDULE,    ["schedule", "timetable", "timing", "class", "classes", "lecture"]),
    (Intent.RESULT,      ["result", "results", "marks", "score", "scorecard", "grade"]),
    (Intent.ADMISSION,   ["admission", "admissions", "apply", "application", "enroll", "enrolment"]),
    (Intent.HOSTEL,      ["hostel", "dorm", "dormitory", "accommodation", "housing", "room"]),
    (Intent.SCHOLARSHIP, ["scholarship", "scholarships", "financial aid", "grant", "merit"]),
    (Intent.CONTACT,     ["contact", "phone", "email", "address", "reach", "helpdesk", "support"]),
    (Intent.HUMAN,       ["human", "agent", "advisor", "staff", "person", "speak to", "talk to",
                          "help desk", "real person", "live agent", "escalate"]),
    (Intent.GREETING,    ["hi", "hello", "hey", "good morning", "good afternoon", "good evening",
                          "howdy", "what's up", "sup"]),
    (Intent.HELP,        ["help", "what can you", "what do you know", "topics", "menu", "options",
                          "capabilities"]),
]

YEAR_PATTERNS: list[tuple[str, list[str]]] = [
    ("first year",  ["1st", "first", r"\b1\b", "fy", "year 1", "first year"]),
    ("second year", ["2nd", "second", r"\b2\b", "sy", "year 2", "second year"]),
    ("third year",  ["3rd", "third", r"\b3\b", "ty", "year 3", "third year"]),
    ("fourth year", ["4th", "fourth", r"\b4\b", "be", "year 4", "fourth year", "final year"]),
]


# ══════════════════════════════════════════════════════════════════
# 3.  EXTRACTION HELPERS
# ══════════════════════════════════════════════════════════════════

def extract_intent(text: str) -> Intent:
    lower = text.lower()
    for intent, keywords in INTENT_PATTERNS:
        if any(re.search(rf"\b{re.escape(kw)}\b", lower) for kw in keywords):
            return intent
    return Intent.UNKNOWN


def fuzzy_intent(text: str) -> Optional[Intent]:
    """
    Secondary pass: fuzzy-match individual words in the query against
    the full keyword vocabulary and return the best-matching intent.
    """
    all_keywords: dict[str, Intent] = {}
    for intent, keywords in INTENT_PATTERNS:
        for kw in keywords:
            all_keywords[kw] = intent

    words = re.findall(r"\w+", text.lower())
    for word in words:
        matches = get_close_matches(word, all_keywords.keys(), n=1, cutoff=0.82)
        if matches:
            return all_keywords[matches[0]]
    return None


def extract_year(text: str) -> Optional[str]:
    lower = text.lower()
    for canonical, aliases in YEAR_PATTERNS:
        if any(re.search(rf"{alias}", lower) for alias in aliases):
            return canonical
    return None


# ══════════════════════════════════════════════════════════════════
# 4.  CONVERSATION STATE
# ══════════════════════════════════════════════════════════════════

@dataclass
class ConversationState:
    last_intent:      Optional[Intent]       = None
    last_year:        Optional[str]          = None
    pending_slot:     Optional[str]          = None   # "year" | "topic"
    fallback_stage:   FallbackStage          = FallbackStage.NONE
    consecutive_fails: int                   = 0
    history:          list[dict]             = field(default_factory=list)

    # ── helpers ──────────────────────────────────────────────────

    def record_success(self, intent: Intent, year: Optional[str] = None):
        self.last_intent       = intent
        self.last_year         = year or self.last_year
        self.pending_slot      = None
        self.fallback_stage    = FallbackStage.NONE
        self.consecutive_fails = 0

    def record_fail(self) -> FallbackStage:
        self.consecutive_fails += 1
        if self.consecutive_fails == 1:
            self.fallback_stage = FallbackStage.CLARIFY
        elif self.consecutive_fails == 2:
            self.fallback_stage = FallbackStage.SUGGEST
        else:
            self.fallback_stage = FallbackStage.HANDOVER
        return self.fallback_stage

    def push(self, user: str, bot: str):
        self.history.append({"user": user, "bot": bot})
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)

    def reset(self):
        self.last_intent       = None
        self.last_year         = None
        self.pending_slot      = None
        self.fallback_stage    = FallbackStage.NONE
        self.consecutive_fails = 0


# ══════════════════════════════════════════════════════════════════
# 5.  RESPONSE BUILDERS
# ══════════════════════════════════════════════════════════════════

def _answer(intent: Intent, year: Optional[str]) -> str:
    topic_data = KB.get(intent, {})
    if year and year in topic_data:
        return topic_data[year]
    return topic_data.get("_general", "I don't have details on that yet.")


def _clarification_prompt(user_text: str) -> str:
    return (
        "I'm not quite sure what you mean. Could you rephrase?\n"
        "For example, try asking:\n"
        "  • 'When is the third-year exam?'\n"
        "  • 'What is the fee for second year?'\n"
        "  • 'Tell me about hostel facilities.'"
    )


def _suggestion_prompt() -> str:
    topics = [
        "📅 Exam dates",
        "💰 Tuition fees",
        "🕐 Class schedule",
        "📊 Results",
        "🎓 Admissions",
        "🏠 Hostel",
        "🏅 Scholarships",
        "📞 Contact / Helpdesk",
    ]
    lines = "\n".join(f"  {t}" for t in topics)
    return (
        "I'm still having trouble understanding your question.\n"
        "Here are the topics I can help with — just pick one:\n"
        f"{lines}\n\n"
        "Or type **'advisor'** to reach a human helper right away."
    )


def _handover_response(reason: str = "") -> str:
    prefix = (
        f"It looks like I haven't been able to help with: *\"{reason}\"*\n\n"
        if reason else ""
    )
    return (
        f"{prefix}"
        "Let me connect you with a human advisor who can assist you further:\n\n"
        f"  📧 **Email**   : {HANDOVER_INFO['email']}\n"
        f"  🌐 **Portal**  : {HANDOVER_INFO['portal']}\n"
        f"  🏢 **Walk-in** : {HANDOVER_INFO['desk']}\n"
        f"  📞 **Phone**   : {HANDOVER_INFO['phone']}\n\n"
        "They are available **Mon–Fri, 9 AM – 5 PM**. "
        "You can also email anytime and expect a reply within 24 hours."
    )


# ══════════════════════════════════════════════════════════════════
# 6.  CHATBOT ENGINE
# ══════════════════════════════════════════════════════════════════

class FallbackChatbot:
    """
    Chatbot with a three-stage fallback ladder:
        Stage 1 → Ask clarification
        Stage 2 → Offer topic suggestions
        Stage 3 → Route to human advisor
    """

    def __init__(self):
        self.state = ConversationState()

    # ── public API ───────────────────────────────────────────────

    def chat(self, user_input: str) -> str:
        user_input = user_input.strip()
        if not user_input:
            return "Please type your question and I'll do my best to help!"

        response = self._process(user_input)
        self.state.push(user_input, response)
        return response

    # ── internal routing ─────────────────────────────────────────

    def _process(self, text: str) -> str:
        # ── admin / meta commands ──────────────────────────────
        lower = text.lower()
        if lower in ("reset", "start over", "clear"):
            self.state.reset()
            return "Context cleared. What would you like to know?"

        if lower == "state":   # debug
            return str(self._debug_state())

        # ── greetings ──────────────────────────────────────────
        if extract_intent(text) == Intent.GREETING:
            self.state.record_success(Intent.GREETING)
            return (
                "Hello! 👋 I'm your college information assistant.\n"
                "Ask me about exams, fees, schedules, results, admissions, "
                "hostel, or scholarships.\nType **'help'** to see all topics."
            )

        # ── help ───────────────────────────────────────────────
        if extract_intent(text) == Intent.HELP:
            self.state.record_success(Intent.HELP)
            return _suggestion_prompt()

        # ── explicit human-handover request ────────────────────
        if extract_intent(text) == Intent.HUMAN:
            self.state.record_success(Intent.HUMAN)
            return _handover_response()

        # ── primary intent detection ───────────────────────────
        intent = extract_intent(text)

        # ── secondary: fuzzy match ────────────────────────────
        if intent == Intent.UNKNOWN:
            intent = fuzzy_intent(text) or Intent.UNKNOWN

        # ── context carry-over ────────────────────────────────
        year = extract_year(text)

        # User gave just a year (follow-up to previous topic)
        if year and intent == Intent.UNKNOWN and self.state.last_intent:
            intent = self.state.last_intent

        # User gave intent but no year → inherit remembered year
        if intent != Intent.UNKNOWN and not year:
            year = self.state.last_year

        # ── handle known intents ──────────────────────────────
        if intent != Intent.UNKNOWN:
            answer = _answer(intent, year)
            self.state.record_success(intent, year)
            return answer

        # ══════════════════════════════════════════════════════
        #  FALLBACK LADDER
        # ══════════════════════════════════════════════════════
        stage = self.state.record_fail()

        if stage == FallbackStage.CLARIFY:
            return _clarification_prompt(text)

        if stage == FallbackStage.SUGGEST:
            return _suggestion_prompt()

        # FallbackStage.HANDOVER (stage 3+)
        return _handover_response(reason=text)

    # ── debug ────────────────────────────────────────────────────

    def _debug_state(self) -> dict:
        s = self.state
        return {
            "last_intent":        s.last_intent.name if s.last_intent else None,
            "last_year":          s.last_year,
            "pending_slot":       s.pending_slot,
            "fallback_stage":     s.fallback_stage.name,
            "consecutive_fails":  s.consecutive_fails,
            "history_len":        len(s.history),
        }


# ══════════════════════════════════════════════════════════════════
# 7.  DEMO RUNNER
# ══════════════════════════════════════════════════════════════════

DEMO_SCENARIOS: list[tuple[str, list[str]]] = [
    (
        "Scenario 1 — Happy path (full question)",
        ["When is the exam for third year?"],
    ),
    (
        "Scenario 2 — Intent only → general answer + clarification",
        ["Tell me about fees"],
        # bot answers generally; user follows up with year
    ),
    (
        "Scenario 3 — Year follow-up after topic",
        ["When are exams?", "Second year"],
    ),
    (
        "Scenario 4 — Out-of-scope → Clarify → Suggest → Handover",
        [
            "bloop zap quantum physics",      # 1st fail → clarify
            "something something blah blah",  # 2nd fail → suggest
            "xyzzy nonsense again",           # 3rd fail → handover
        ],
    ),
    (
        "Scenario 5 — Fuzzy match (typo: 'shcedule')",
        ["What is the shcedule for first year?"],
    ),
    (
        "Scenario 6 — Explicit human handover request",
        ["I want to talk to a real person"],
    ),
    (
        "Scenario 7 — Hostel + scholarship queries",
        ["Tell me about hostel facilities", "Are there any scholarships?"],
    ),
    (
        "Scenario 8 — Context reset mid-conversation",
        ["Exam dates for second year?", "reset", "What are the fees?"],
    ),
]


def _print_turn(user: str, bot: str, state_info: dict):
    print(f"  You : {user}")
    for i, line in enumerate(bot.split("\n")):
        prefix = "  Bot : " if i == 0 else "        "
        print(prefix + line)
    print(
        f"  [state] intent={state_info['last_intent']}  "
        f"year={state_info['last_year']}  "
        f"fails={state_info['consecutive_fails']}  "
        f"stage={state_info['fallback_stage']}"
    )


def run_demo():
    print("\n" + "═" * 64)
    print("  FALLBACK & HANDOVER CHATBOT — DEMO")
    print("═" * 64)

    for title, turns in DEMO_SCENARIOS:
        bot = FallbackChatbot()
        print(f"\n{'─'*64}")
        print(f"  {title}")
        print(f"{'─'*64}")
        for turn in turns:
            reply = bot.chat(turn)
            _print_turn(turn, reply, bot._debug_state())
            print()


# ══════════════════════════════════════════════════════════════════
# 8.  INTERACTIVE REPL
# ══════════════════════════════════════════════════════════════════

def run_interactive():
    bot = FallbackChatbot()
    print("\n" + "═" * 64)
    print("  COLLEGE CHATBOT  (type 'quit' to exit, 'state' to inspect)")
    print("═" * 64 + "\n")
    while True:
        try:
            user_input = input("You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Bot : Goodbye! 👋")
            break
        if not user_input:
            continue
        reply = bot.chat(user_input)
        print(f"Bot : {reply}\n")


# ══════════════════════════════════════════════════════════════════
# 9.  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    if "--interactive" in sys.argv:
        run_interactive()
    else:
        run_demo()
        print("\n" + "─" * 64)
        print("  Run with --interactive for a live chat session.")
        print("─" * 64 + "\n")
