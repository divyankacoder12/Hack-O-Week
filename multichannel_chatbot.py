"""
╔══════════════════════════════════════════════════════════════════════════╗
║          MULTICHANNEL COLLEGE CHATBOT — DEPLOYMENT MOCKUP               ║
║                                                                          ║
║  Channels simulated via CLI:                                             ║
║    1. WEB      — rich HTML-style markdown, quick-reply buttons,          ║
║                  typing indicators, session cookies                       ║
║    2. MOBILE   — compact plain-text, push-notification banners,          ║
║                  haptic hints, abbreviated menus                          ║
║    3. WHATSAPP — WhatsApp Business API format, numbered menus,           ║
║                  emoji-only formatting, 1600-char message cap,           ║
║                  template messages for first contact                     ║
║                                                                          ║
║  Core engine is CHANNEL-AGNOSTIC; each channel adapter transforms        ║
║  the raw BotResponse into its channel-native representation.             ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import re
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ══════════════════════════════════════════════════════════════
# 0.  TERMINAL COLOURS  (pure ANSI — no dependencies)
# ══════════════════════════════════════════════════════════════

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    # foregrounds
    WHITE  = "\033[97m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    RED    = "\033[91m"
    GRAY   = "\033[90m"
    # backgrounds
    BG_DARK  = "\033[40m"
    BG_BLUE  = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_WA    = "\033[48;2;18;140;126m"   # WhatsApp teal


def c(color: str, text: str) -> str:
    return f"{color}{text}{C.RESET}"


# ══════════════════════════════════════════════════════════════
# 1.  CHANNEL ENUM
# ══════════════════════════════════════════════════════════════

class Channel(Enum):
    WEB       = "web"
    MOBILE    = "mobile"
    WHATSAPP  = "whatsapp"


# ══════════════════════════════════════════════════════════════
# 2.  CORE DATA STRUCTURES
# ══════════════════════════════════════════════════════════════

@dataclass
class QuickReply:
    """A tappable suggestion chip / numbered menu option."""
    label: str
    payload: str          # machine-readable value


@dataclass
class BotResponse:
    """
    Channel-agnostic response produced by the core engine.
    Adapters translate this into channel-native format.
    """
    text: str
    quick_replies: list[QuickReply]   = field(default_factory=list)
    is_handover:   bool               = False
    needs_year:    bool               = False
    intent_tag:    str                = ""
    confidence:    float              = 1.0   # 0–1


@dataclass
class ChannelMessage:
    """Inbound message envelope — normalised across all channels."""
    channel:    Channel
    user_id:    str
    session_id: str
    text:       str
    timestamp:  float = field(default_factory=time.time)
    # channel-specific metadata
    meta:       dict  = field(default_factory=dict)


@dataclass
class ConversationState:
    last_intent:       Optional[str] = None
    last_year:         Optional[str] = None
    consecutive_fails: int           = 0
    turn_count:        int           = 0
    history:           list          = field(default_factory=list)

    def push(self, user: str, bot: str):
        self.history.append({"u": user, "b": bot})
        if len(self.history) > 10:
            self.history.pop(0)
        self.turn_count += 1


# ══════════════════════════════════════════════════════════════
# 3.  KNOWLEDGE BASE  (shared across all channels)
# ══════════════════════════════════════════════════════════════

KB = {
    "exam": {
        "first year":  "First-year exams: Theory May 15, Practicals May 22.",
        "second year": "Second-year exams: Theory May 20, Practicals May 28.",
        "third year":  "Third-year exams: Theory June 1, Practicals June 8.",
        "fourth year": "Fourth-year exams: Theory June 10, Practicals June 17.",
        "_general":    "Exam dates vary by year. Which year are you asking about?",
    },
    "fee": {
        "first year":  "First-year tuition: Rs 85,000 per semester.",
        "second year": "Second-year tuition: Rs 87,000 per semester.",
        "third year":  "Third-year tuition: Rs 89,000 per semester.",
        "fourth year": "Fourth-year tuition: Rs 91,000 per semester.",
        "_general":    "Fees vary by year. Which year would you like details for?",
    },
    "schedule": {
        "first year":  "First-year: Mon-Fri, 9 AM - 4 PM.",
        "second year": "Second-year: Mon-Fri, 9 AM - 5 PM.",
        "third year":  "Third-year: Mon-Sat, 8 AM - 5 PM (Sat = lab day).",
        "fourth year": "Fourth-year schedule varies by elective — check notice board.",
        "_general":    "Schedules differ by year. Which year are you asking about?",
    },
    "result": {
        "first year":  "First-year results declared within 45 days of exams.",
        "second year": "Second-year results declared within 40 days of exams.",
        "third year":  "Third-year results declared within 35 days of exams.",
        "fourth year": "Fourth-year results declared within 30 days of exams.",
        "_general":    "Result timelines differ by year. Which year are you asking about?",
    },
    "admission": {
        "_general": "Admissions open every June. Apply at college.edu/admissions. Docs: 10th & 12th marksheets, ID proof, passport photo.",
    },
    "hostel": {
        "_general": "Hostel fees: Rs 40,000/year (double occupancy). Apply via student portal. Contact: hostel@college.edu",
    },
    "scholarship": {
        "_general": "Merit scholarships for students scoring >75% in previous year. Apply at college.edu/scholarships before July 31.",
    },
}

HANDOVER_CONTACTS = {
    "email":  "advisor@college.edu",
    "portal": "college.edu/helpdesk",
    "desk":   "Admin Block, Room 101, Mon-Fri 9AM-5PM",
    "phone":  "+91-712-000-1234",
}

INTENT_MAP = {
    "exam":        ["exam", "test", "examination", "paper"],
    "fee":         ["fee", "fees", "tuition", "cost", "payment"],
    "schedule":    ["schedule", "timetable", "timing", "class", "classes"],
    "result":      ["result", "results", "marks", "score", "grade"],
    "admission":   ["admission", "admissions", "apply", "enroll"],
    "hostel":      ["hostel", "dorm", "accommodation", "housing"],
    "scholarship": ["scholarship", "financial aid", "grant", "merit"],
    "contact":     ["contact", "phone", "email", "helpdesk", "support", "reach"],
    "human":       ["human", "agent", "advisor", "real person", "live", "escalate", "staff"],
    "greeting":    ["hi", "hello", "hey", "good morning", "good afternoon"],
    "help":        ["help", "menu", "options", "topics", "what can"],
}

YEAR_MAP = {
    "first year":  [r"\b1st\b", r"\bfirst\b", r"\b1\b", r"\bfy\b"],
    "second year": [r"\b2nd\b", r"\bsecond\b", r"\b2\b", r"\bsy\b"],
    "third year":  [r"\b3rd\b", r"\bthird\b", r"\b3\b", r"\bty\b"],
    "fourth year": [r"\b4th\b", r"\bfourth\b", r"\b4\b", r"\bfinal\b", r"\bbe\b"],
}

TOPIC_QR = [
    QuickReply("Exam Dates",   "exam"),
    QuickReply("Fees",         "fee"),
    QuickReply("Schedule",     "schedule"),
    QuickReply("Results",      "result"),
    QuickReply("Admissions",   "admission"),
    QuickReply("Hostel",       "hostel"),
    QuickReply("Scholarship",  "scholarship"),
    QuickReply("Talk to Human","human"),
]

YEAR_QR = [
    QuickReply("1st Year", "first year"),
    QuickReply("2nd Year", "second year"),
    QuickReply("3rd Year", "third year"),
    QuickReply("4th Year", "fourth year"),
]


# ══════════════════════════════════════════════════════════════
# 4.  CORE ENGINE  (channel-agnostic)
# ══════════════════════════════════════════════════════════════

class CoreEngine:
    """Pure logic layer — knows nothing about channels."""

    def __init__(self):
        self._sessions: dict[str, ConversationState] = {}

    def _state(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState()
        return self._sessions[session_id]

    # ── extraction ────────────────────────────────────────────

    @staticmethod
    def _intent(text: str) -> Optional[str]:
        low = text.lower()
        for intent, kws in INTENT_MAP.items():
            if any(re.search(rf"\b{re.escape(k)}\b", low) for k in kws):
                return intent
        return None

    @staticmethod
    def _year(text: str) -> Optional[str]:
        low = text.lower()
        for canonical, pats in YEAR_MAP.items():
            if any(re.search(p, low) for p in pats):
                return canonical
        return None

    # ── answer lookup ─────────────────────────────────────────

    @staticmethod
    def _answer(intent: str, year: Optional[str]) -> tuple[str, bool]:
        """Returns (answer_text, needs_year_clarification)."""
        data = KB.get(intent, {})
        if year and year in data:
            return data[year], False
        general = data.get("_general", "I don't have info on that yet.")
        needs_year = any(k != "_general" for k in data)
        return general, needs_year

    # ── handover text ─────────────────────────────────────────

    @staticmethod
    def _handover_text() -> str:
        c = HANDOVER_CONTACTS
        return (
            f"Let me connect you with a human advisor:\n"
            f"Email: {c['email']}\n"
            f"Portal: {c['portal']}\n"
            f"Walk-in: {c['desk']}\n"
            f"Phone: {c['phone']}"
        )

    # ── main process ──────────────────────────────────────────

    def process(self, msg: ChannelMessage) -> BotResponse:
        state  = self._state(msg.session_id)
        text   = msg.text.strip()
        intent = self._intent(text)
        year   = self._year(text)

        # ── greeting ──────────────────────────────────────────
        if intent == "greeting":
            state.consecutive_fails = 0
            resp = BotResponse(
                text="Hello! I'm your college assistant. How can I help you today?",
                quick_replies=TOPIC_QR,
                intent_tag="greeting",
            )
            state.push(text, resp.text)
            return resp

        # ── help / menu ───────────────────────────────────────
        if intent == "help":
            state.consecutive_fails = 0
            resp = BotResponse(
                text="Here's what I can help you with:",
                quick_replies=TOPIC_QR,
                intent_tag="help",
            )
            state.push(text, resp.text)
            return resp

        # ── explicit human request ────────────────────────────
        if intent == "human" or intent == "contact":
            state.consecutive_fails = 0
            resp = BotResponse(
                text=self._handover_text(),
                is_handover=True,
                intent_tag="handover",
            )
            state.push(text, resp.text)
            return resp

        # ── context: year-only follow-up ──────────────────────
        if year and not intent and state.last_intent:
            intent = state.last_intent

        # ── context: topic-only, inherit year ─────────────────
        if intent and not year:
            year = state.last_year

        # ── known topic ───────────────────────────────────────
        if intent and intent in KB:
            answer, needs_year = self._answer(intent, year)
            state.last_intent       = intent
            state.last_year         = year
            state.consecutive_fails = 0
            qr = YEAR_QR if needs_year else []
            resp = BotResponse(
                text=answer,
                quick_replies=qr,
                needs_year=needs_year,
                intent_tag=intent,
                confidence=0.95,
            )
            state.push(text, resp.text)
            return resp

        # ── fallback ladder ───────────────────────────────────
        state.consecutive_fails += 1

        if state.consecutive_fails == 1:
            resp = BotResponse(
                text="I'm not sure I understood that. Could you rephrase?\nOr choose a topic below:",
                quick_replies=TOPIC_QR,
                intent_tag="clarify",
                confidence=0.3,
            )
        elif state.consecutive_fails == 2:
            resp = BotResponse(
                text="Still having trouble. Here are the topics I can help with:",
                quick_replies=TOPIC_QR,
                intent_tag="suggest",
                confidence=0.15,
            )
        else:
            resp = BotResponse(
                text=self._handover_text(),
                is_handover=True,
                intent_tag="handover",
                confidence=0.0,
            )

        state.push(text, resp.text)
        return resp


# ══════════════════════════════════════════════════════════════
# 5.  CHANNEL ADAPTERS
# ══════════════════════════════════════════════════════════════

class BaseAdapter:
    """Shared utilities for all adapters."""
    WRAP = 70

    def _wrap(self, text: str, width: int = None) -> str:
        w = width or self.WRAP
        lines = text.split("\n")
        wrapped = []
        for line in lines:
            if len(line) <= w:
                wrapped.append(line)
            else:
                wrapped.extend(textwrap.wrap(line, w))
        return "\n".join(wrapped)


# ──────────────────────────────────────────────────────────────
# 5a.  WEB ADAPTER
# ──────────────────────────────────────────────────────────────

class WebAdapter(BaseAdapter):
    """
    Simulates a browser chat widget:
      • Rich markdown-style formatting (bold, bullets)
      • Quick-reply chips displayed as [Button] rows
      • Typing indicator animation
      • Session cookie shown in header
      • Timestamp on each bubble
    """

    BANNER_W = 68

    def render_banner(self, session_id: str):
        border = "─" * self.BANNER_W
        print(f"\n{c(C.BLUE+C.BOLD, '╔' + '═'*self.BANNER_W + '╗')}")
        print(c(C.BLUE+C.BOLD, "║") +
              c(C.CYAN+C.BOLD, "  🌐  COLLEGE ASSISTANT  ·  WEB CHANNEL".center(self.BANNER_W)) +
              c(C.BLUE+C.BOLD, "║"))
        print(c(C.BLUE+C.BOLD, "║") +
              c(C.GRAY, f"  Session: {session_id[:24]}...".ljust(self.BANNER_W)) +
              c(C.BLUE+C.BOLD, "║"))
        print(f"{c(C.BLUE+C.BOLD, '╚' + '═'*self.BANNER_W + '╝')}")

    def render_user(self, text: str):
        ts = time.strftime("%H:%M")
        bubble = f"  {text}  "
        pad    = self.BANNER_W - len(bubble) - 8
        print(
            " " * pad +
            c(C.BG_BLUE + C.WHITE, bubble) +
            c(C.GRAY, f"  {ts}")
        )

    def render_typing(self):
        print(c(C.GRAY + C.DIM, "  Bot is typing  ● ● ●"))
        time.sleep(0.3)

    def render_bot(self, resp: BotResponse):
        ts = time.strftime("%H:%M")
        # Format text: **bold** → ANSI bold, bullets
        text = resp.text
        text = re.sub(r"\*\*(.+?)\*\*", lambda m: c(C.BOLD+C.WHITE, m.group(1)), text)

        lines = self._wrap(text).split("\n")
        for i, line in enumerate(lines):
            prefix = c(C.GREEN, "  🤖 ") if i == 0 else "     "
            print(prefix + line)

        if resp.is_handover:
            print(c(C.YELLOW, "  ⚠  Transferring to human advisor..."))

        if resp.quick_replies:
            print()
            chips = "  " + "  ".join(
                c(C.BG_DARK + C.CYAN, f" {qr.label} ") for qr in resp.quick_replies[:5]
            )
            print(chips)
            if len(resp.quick_replies) > 5:
                extra = "  " + "  ".join(
                    c(C.BG_DARK + C.CYAN, f" {qr.label} ") for qr in resp.quick_replies[5:]
                )
                print(extra)

        print(c(C.GRAY, f"  {ts}  ·  intent: {resp.intent_tag}  ·  conf: {resp.confidence:.0%}"))
        print()

    def chat_loop(self, engine: CoreEngine, demo_inputs: list[str] = None):
        session_id = str(uuid.uuid4())
        user_id    = "web_user_001"
        self.render_banner(session_id)

        inputs = iter(demo_inputs) if demo_inputs else None
        while True:
            if inputs:
                try:
                    raw = next(inputs)
                    print(c(C.GRAY, f"\n  [auto-input]: ") + raw)
                except StopIteration:
                    break
            else:
                try:
                    raw = input(c(C.CYAN, "\n  You ❯ "))
                except (EOFError, KeyboardInterrupt):
                    break
                if raw.lower() in ("quit", "exit"):
                    break

            self.render_user(raw)
            self.render_typing()
            msg  = ChannelMessage(Channel.WEB, user_id, session_id, raw)
            resp = engine.process(msg)
            self.render_bot(resp)


# ──────────────────────────────────────────────────────────────
# 5b.  MOBILE ADAPTER
# ──────────────────────────────────────────────────────────────

class MobileAdapter(BaseAdapter):
    """
    Simulates an iOS / Android chat app:
      • Compact single-line bubbles (max 50 chars before wrap)
      • Push notification banner for first message
      • Abbreviated quick-reply row (icons + short label)
      • Battery / signal bar in header
      • Haptic hint labels  [TAP]  [VIBRATE]
    """

    WRAP    = 48
    ICON_MAP = {
        "exam": "📅", "fee": "💰", "schedule": "🕐", "result": "📊",
        "admission": "🎓", "hostel": "🏠", "scholarship": "🏅",
        "human": "👤", "greeting": "👋", "help": "❓", "handover": "🔴",
        "clarify": "🤔", "suggest": "💡",
    }

    def render_banner(self):
        bar = "▂▄▆█ ●●●●  WiFi ▲  🔋98%"
        print()
        print(c(C.MAGENTA+C.BOLD, "┌" + "─"*46 + "┐"))
        print(c(C.MAGENTA+C.BOLD, "│") +
              c(C.GRAY, f"  {bar}".ljust(46)) +
              c(C.MAGENTA+C.BOLD, "│"))
        print(c(C.MAGENTA+C.BOLD, "│") +
              c(C.WHITE+C.BOLD,  "  📱  College App  —  MOBILE CHANNEL".center(46)) +
              c(C.MAGENTA+C.BOLD, "│"))
        print(c(C.MAGENTA+C.BOLD, "└" + "─"*46 + "┘"))

    def push_notification(self, text: str):
        short = text[:55] + "…" if len(text) > 55 else text
        print(c(C.GRAY, "\n  ┌─ PUSH NOTIFICATION ─────────────────────┐"))
        print(c(C.GRAY, "  │ ") + c(C.WHITE, "🔔 College Assistant: ") + c(C.GRAY, short))
        print(c(C.GRAY, "  └──────────────────────────────────────────┘"))
        print(c(C.GRAY, "  [TAP to open]"))

    def render_user(self, text: str):
        ts = time.strftime("%H:%M")
        print()
        for i, line in enumerate(self._wrap(text, self.WRAP).split("\n")):
            pad = 48 - len(line) - 2
            if i == 0:
                print(" " * pad + c(C.BG_BLUE + C.WHITE, f" {line} ") + c(C.GRAY, f" {ts}"))
            else:
                print(" " * pad + c(C.BG_BLUE + C.WHITE, f" {line} "))

    def render_bot(self, resp: BotResponse, first_msg: bool = False):
        if first_msg:
            self.push_notification(resp.text)
        ts   = time.strftime("%H:%M")
        icon = self.ICON_MAP.get(resp.intent_tag, "🤖")

        print()
        lines = self._wrap(resp.text, self.WRAP).split("\n")
        for i, line in enumerate(lines):
            prefix = f"  {icon} " if i == 0 else "     "
            print(prefix + c(C.WHITE, line))

        if resp.is_handover:
            print(c(C.RED, "  🔴 HANDOVER — advisor notified  [VIBRATE]"))

        if resp.quick_replies:
            # Mobile: show max 4 abbreviated chips
            chips = resp.quick_replies[:4]
            row   = "  " + "  ".join(
                c(C.MAGENTA, f"[{qr.label[:8]}]") for qr in chips
            )
            if len(resp.quick_replies) > 4:
                row += c(C.GRAY, f"  +{len(resp.quick_replies)-4} more")
            print(row + c(C.GRAY, "  [TAP]"))

        print(c(C.GRAY, f"  {ts} ✓✓  {resp.intent_tag}"))

    def chat_loop(self, engine: CoreEngine, demo_inputs: list[str] = None):
        session_id = "mob_" + str(uuid.uuid4())[:8]
        user_id    = "+91-9876543210"
        self.render_banner()

        inputs  = iter(demo_inputs) if demo_inputs else None
        is_first = True
        while True:
            if inputs:
                try:
                    raw = next(inputs)
                    print(c(C.GRAY, f"\n  [auto]: ") + raw)
                except StopIteration:
                    break
            else:
                try:
                    raw = input(c(C.MAGENTA, "\n  You ❯ "))
                except (EOFError, KeyboardInterrupt):
                    break
                if raw.lower() in ("quit", "exit"):
                    break

            self.render_user(raw)
            msg  = ChannelMessage(Channel.MOBILE, user_id, session_id, raw)
            resp = engine.process(msg)
            self.render_bot(resp, first_msg=is_first)
            is_first = False


# ──────────────────────────────────────────────────────────────
# 5c.  WHATSAPP ADAPTER
# ──────────────────────────────────────────────────────────────

class WhatsAppAdapter(BaseAdapter):
    """
    Simulates WhatsApp Business API:
      • Template message on first contact (opt-in flow)
      • Plain text only — no markdown, no HTML
      • Numbered list menus  (1. Exam  2. Fees …)
      • 1600-char message cap (hard truncation)
      • Double-tick delivery receipts ✓✓
      • WA-style timestamp  [DD/MM HH:MM]
      • Handover as WA Business CTA with vCard snippet
    """

    MAX_LEN  = 1600
    WA_GREEN = C.BG_WA

    def render_banner(self, phone: str):
        print()
        print(c(self.WA_GREEN + C.WHITE + C.BOLD,
                "  WhatsApp Business  ·  College Assistant  ".center(52)))
        print(c(C.GRAY, f"  To: {phone}  ·  End-to-end encrypted 🔒"))
        print(c(C.GRAY, "  " + "─" * 50))

    def _template_message(self) -> str:
        """WhatsApp requires approved template for first outbound message."""
        return (
            "Hello! 👋 I am the College Assistant on WhatsApp.\n\n"
            "I can help you with exams, fees, schedule, results, "
            "admissions, hostel and scholarships.\n\n"
            "Reply *MENU* to see all options or ask your question directly."
        )

    def _wa_format(self, text: str) -> str:
        """Strip markdown, apply WA bold (*word*), cap at MAX_LEN."""
        # convert **bold** → *bold*  (WA uses single asterisk)
        text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
        # strip leftover markdown
        text = re.sub(r"[`#>~]", "", text)
        # ensure within cap
        if len(text) > self.MAX_LEN:
            text = text[:self.MAX_LEN - 3] + "..."
        return text

    def _numbered_menu(self, qrs: list[QuickReply]) -> str:
        lines = ["Reply with a number:"]
        for i, qr in enumerate(qrs, 1):
            lines.append(f"  {i}. {qr.label}")
        return "\n".join(lines)

    def _resolve_numbered(self, text: str, last_qrs: list[QuickReply]) -> str:
        """If user sent '3', return the payload of the 3rd quick reply."""
        m = re.match(r"^\s*(\d+)\s*$", text.strip())
        if m and last_qrs:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(last_qrs):
                return last_qrs[idx].payload
        return text

    def render_user(self, text: str):
        ts = time.strftime("%d/%m %H:%M")
        print(c(C.GRAY, f"\n  [{ts}]"))
        print(c(C.WHITE+C.BOLD, f"  You: ") + text)

    def render_bot(self, text: str, qrs: list[QuickReply],
                   is_handover: bool = False, is_template: bool = False):
        ts    = time.strftime("%d/%m %H:%M")
        label = "TEMPLATE" if is_template else "College Assistant"
        body  = self._wa_format(text)

        print()
        print(c(self.WA_GREEN + C.WHITE, f"  [{label}]  {ts} ✓✓"))
        # WA message bubble
        for line in body.split("\n"):
            print(c(C.GREEN, "  │ ") + line)

        if qrs:
            print(c(C.GREEN, "  │"))
            menu = self._numbered_menu(qrs)
            for line in menu.split("\n"):
                print(c(C.GREEN, "  │ ") + c(C.YELLOW, line))

        if is_handover:
            vcard = (
                "\n  ┌─── CONTACT CARD ───────────────────┐\n"
                f"  │  👤 College Advisor                 │\n"
                f"  │  📞 {HANDOVER_CONTACTS['phone']}         │\n"
                f"  │  📧 {HANDOVER_CONTACTS['email']}  │\n"
                "  └────────────────────────────────────┘"
            )
            print(c(C.YELLOW, vcard))

        print(c(C.GRAY, f"  └── {len(body)} chars  ·  {'TEMPLATE' if is_template else 'SESSION'} msg"))

    def chat_loop(self, engine: CoreEngine, demo_inputs: list[str] = None):
        phone      = "+91-8765432109"
        session_id = "wa_" + str(uuid.uuid4())[:8]
        self.render_banner(phone)

        # ── Template message (first contact) ──────────────────
        tmpl = self._template_message()
        self.render_bot(tmpl, [], is_template=True)

        last_qrs: list[QuickReply] = []
        inputs  = iter(demo_inputs) if demo_inputs else None

        while True:
            if inputs:
                try:
                    raw = next(inputs)
                    print(c(C.GRAY, f"\n  [auto]: ") + raw)
                except StopIteration:
                    break
            else:
                try:
                    raw = input(c(C.BG_WA + C.WHITE, "\n  You ❯ ") + C.RESET + " ")
                except (EOFError, KeyboardInterrupt):
                    break
                if raw.lower() in ("quit", "exit"):
                    break

            # resolve numbered reply
            resolved = self._resolve_numbered(raw, last_qrs)
            self.render_user(raw + (f"  → '{resolved}'" if resolved != raw else ""))

            msg  = ChannelMessage(Channel.WHATSAPP, phone, session_id, resolved)
            resp = engine.process(msg)
            self.render_bot(resp.text, resp.quick_replies, resp.is_handover)
            last_qrs = resp.quick_replies


# ══════════════════════════════════════════════════════════════
# 6.  ORCHESTRATOR
# ══════════════════════════════════════════════════════════════

class MultichannelOrchestrator:
    """
    Routes an inbound message to the correct adapter.
    In production this would sit behind a webhook / message-bus.
    """

    def __init__(self):
        self.engine   = CoreEngine()
        self.adapters = {
            Channel.WEB:      WebAdapter(),
            Channel.MOBILE:   MobileAdapter(),
            Channel.WHATSAPP: WhatsAppAdapter(),
        }

    def run_channel(self, channel: Channel, demo_inputs: list[str] = None):
        adapter = self.adapters[channel]
        adapter.chat_loop(self.engine, demo_inputs)


# ══════════════════════════════════════════════════════════════
# 7.  DEMO RUNNER
# ══════════════════════════════════════════════════════════════

DEMO_INPUTS = [
    "Hello",
    "When is the exam?",
    "Third year",
    "What about fees?",
    "random gibberish abc",
    "more nonsense xyz",
    "I need to talk to someone",
]

WA_INPUTS = [
    "Hi",
    "1",        # selects first quick-reply (Exam Dates)
    "2nd year",
    "fees",
    "3",        # selects 3rd quick-reply after fees menu
    "blah blah unknown",
    "escalate",
]


def run_full_demo():
    orch = MultichannelOrchestrator()

    print(c(C.BOLD + C.WHITE, "\n\n" + "█"*70))
    print(c(C.BOLD + C.CYAN,  "  MULTICHANNEL CHATBOT — DEPLOYMENT MOCKUP"))
    print(c(C.BOLD + C.WHITE, "█"*70))
    print(c(C.GRAY,
        "  Same core engine, three channel-native experiences:\n"
        "  WEB (rich markdown)  ·  MOBILE (compact)  ·  WHATSAPP (plain-text + numbered menu)\n"
    ))
    time.sleep(0.4)

    # ── WEB ───────────────────────────────────────────────────
    print(c(C.BOLD + C.BLUE, "\n\n" + "▓"*70))
    print(c(C.BOLD + C.BLUE, "  CHANNEL 1 OF 3 — WEB"))
    print(c(C.BOLD + C.BLUE, "▓"*70))
    orch.run_channel(Channel.WEB, DEMO_INPUTS)

    # ── MOBILE ────────────────────────────────────────────────
    print(c(C.BOLD + C.MAGENTA, "\n\n" + "▓"*70))
    print(c(C.BOLD + C.MAGENTA, "  CHANNEL 2 OF 3 — MOBILE APP"))
    print(c(C.BOLD + C.MAGENTA, "▓"*70))
    orch.run_channel(Channel.MOBILE, DEMO_INPUTS)

    # ── WHATSAPP ──────────────────────────────────────────────
    print(c(C.BOLD + C.GREEN, "\n\n" + "▓"*70))
    print(c(C.BOLD + C.GREEN, "  CHANNEL 3 OF 3 — WHATSAPP"))
    print(c(C.BOLD + C.GREEN, "▓"*70))
    orch.run_channel(Channel.WHATSAPP, WA_INPUTS)

    # ── summary ───────────────────────────────────────────────
    print("\n\n" + "═"*70)
    print(c(C.BOLD + C.WHITE, "  ARCHITECTURE SUMMARY"))
    print("═"*70)
    rows = [
        ("Layer",         "WEB",             "MOBILE",           "WHATSAPP"),
        ("Format",        "Markdown/HTML",   "Plain text",       "WA plain text"),
        ("Quick replies", "Button chips",    "Abbreviated chips","Numbered list"),
        ("Max msg len",   "No limit",        "~300 chars",       "1600 chars"),
        ("First contact", "Welcome msg",     "Push notification","Template msg"),
        ("Handover",      "Advisor links",   "VIBRATE + links",  "vCard + links"),
        ("Typing hint",   "● ● ●",           "—",                "—"),
        ("Session ID",    "UUID cookie",     "mob_XXXX",         "wa_XXXX"),
    ]
    col = [22, 18, 18, 18]
    sep = "  " + "─"*(sum(col)+6)
    print(sep)
    for i, row in enumerate(rows):
        line = "  " + "│".join(
            (c(C.CYAN+C.BOLD, v) if i == 0 else c(C.WHITE, v)).ljust(
                w + (len(c(C.CYAN+C.BOLD,"")) if i == 0 else len(c(C.WHITE,"")))
            )
            for v, w in zip(row, col)
        )
        print(line)
        if i == 0:
            print(sep)
    print(sep + "\n")


# ══════════════════════════════════════════════════════════════
# 8.  INTERACTIVE MODE
# ══════════════════════════════════════════════════════════════

def run_interactive():
    orch = MultichannelOrchestrator()
    print(c(C.BOLD + C.WHITE, "\n  Choose a channel:"))
    print("  1. Web\n  2. Mobile\n  3. WhatsApp")
    choice = input(c(C.CYAN, "\n  Enter 1 / 2 / 3 ❯ ")).strip()
    ch = {
        "1": Channel.WEB,
        "2": Channel.MOBILE,
        "3": Channel.WHATSAPP,
    }.get(choice, Channel.WEB)
    orch.run_channel(ch)


# ══════════════════════════════════════════════════════════════
# 9.  ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    if "--interactive" in sys.argv:
        run_interactive()
    else:
        run_full_demo()
        print(c(C.GRAY, "  Run with --interactive to chat live on a chosen channel.\n"))
