"""
Analytics and Continuous Improvement System
============================================
Logs all chatbot interactions, labels a small sample, and proposes
improvements (new intents, new FAQs, better patterns) based on observed
student queries.
"""

import json
import random
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
# 1.  DATABASE SETUP
# ─────────────────────────────────────────────

DB_PATH = Path("chatbot_analytics.db")


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create tables if they don't exist and return a connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # All interactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT    NOT NULL,
            timestamp     TEXT    NOT NULL,
            user_query    TEXT    NOT NULL,
            bot_response  TEXT    NOT NULL,
            intent        TEXT,           -- detected intent
            confidence    REAL,           -- intent-confidence score (0–1)
            resolved      INTEGER DEFAULT 0,  -- 1 = student got answer
            feedback      TEXT,           -- 'positive' | 'negative' | NULL
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Labelled sample
    cur.execute("""
        CREATE TABLE IF NOT EXISTS labelled_samples (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction_id  INTEGER REFERENCES interactions(id),
            true_intent     TEXT    NOT NULL,
            suggested_faq   TEXT,
            reviewer_notes  TEXT,
            labelled_at     TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Proposed improvements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS improvement_proposals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_type   TEXT    NOT NULL,  -- 'new_intent'|'new_faq'|'better_pattern'
            title           TEXT    NOT NULL,
            description     TEXT    NOT NULL,
            example_queries TEXT,              -- JSON list
            priority        TEXT    DEFAULT 'medium',  -- low|medium|high
            status          TEXT    DEFAULT 'pending', -- pending|accepted|rejected
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    return conn


# ─────────────────────────────────────────────
# 2.  INTERACTION LOGGER
# ─────────────────────────────────────────────

class InteractionLogger:
    """Persists every chatbot turn to the database."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def log(
        self,
        session_id: str,
        user_query: str,
        bot_response: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        resolved: bool = False,
        feedback: Optional[str] = None,
    ) -> int:
        """Insert one interaction; returns the new row id."""
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO interactions
                (session_id, timestamp, user_query, bot_response,
                 intent, confidence, resolved, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now().isoformat(timespec="seconds"),
                user_query.strip(),
                bot_response.strip(),
                intent,
                confidence,
                int(resolved),
                feedback,
            ),
        )
        self.conn.commit()
        row_id = cur.lastrowid
        print(f"  [Logger] Saved interaction #{row_id}  intent={intent!r}  resolved={resolved}")
        return row_id

    def update_feedback(self, interaction_id: int, feedback: str) -> None:
        """Allow post-hoc feedback ('positive'/'negative')."""
        self.conn.execute(
            "UPDATE interactions SET feedback=? WHERE id=?",
            (feedback, interaction_id),
        )
        self.conn.commit()


# ─────────────────────────────────────────────
# 3.  SAMPLE LABELLER
# ─────────────────────────────────────────────

class SampleLabeller:
    """
    Selects a stratified random sample of interactions and stores
    human (or simulated) labels.

    Sampling strategy
    -----------------
    • Always include interactions where resolved=0 (unanswered).
    • Always include low-confidence detections (confidence < threshold).
    • Fill the rest randomly from the remainder.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        sample_size: int = 20,
        low_confidence_threshold: float = 0.60,
    ):
        self.conn = conn
        self.sample_size = sample_size
        self.threshold = low_confidence_threshold

    # ------------------------------------------------------------------
    def select_sample(self, since_hours: int = 24) -> list[sqlite3.Row]:
        """Return rows chosen for labelling (not already labelled)."""
        since = (datetime.now() - timedelta(hours=since_hours)).isoformat()
        cur = self.conn.cursor()

        # Priority pool: unresolved or low-confidence
        cur.execute(
            """
            SELECT i.* FROM interactions i
            LEFT JOIN labelled_samples ls ON ls.interaction_id = i.id
            WHERE ls.id IS NULL
              AND i.created_at >= ?
              AND (i.resolved = 0 OR i.confidence < ? OR i.confidence IS NULL)
            ORDER BY i.created_at DESC
            """,
            (since, self.threshold),
        )
        priority = cur.fetchall()

        # Random remainder
        cur.execute(
            """
            SELECT i.* FROM interactions i
            LEFT JOIN labelled_samples ls ON ls.interaction_id = i.id
            WHERE ls.id IS NULL
              AND i.created_at >= ?
              AND i.resolved = 1
              AND (i.confidence IS NULL OR i.confidence >= ?)
            ORDER BY RANDOM()
            """,
            (since, self.threshold),
        )
        remainder = cur.fetchall()

        sample = priority[: self.sample_size]
        if len(sample) < self.sample_size:
            sample += remainder[: self.sample_size - len(sample)]

        return sample

    # ------------------------------------------------------------------
    def auto_label(self, row: sqlite3.Row) -> dict:
        """
        Simulate a reviewer labelling a row.
        In production, replace this with a human review UI / crowd-source tool.
        """
        query = row["user_query"].lower()

        # Simple keyword heuristic to assign a 'true intent'
        rules = [
            (r"\b(fee|fees|tuition|payment|pay)\b",          "fee_inquiry"),
            (r"\b(deadline|due date|last date|submit)\b",    "deadline_inquiry"),
            (r"\b(admit|admission|apply|application)\b",     "admission_inquiry"),
            (r"\b(result|grade|mark|score|gpa)\b",           "result_inquiry"),
            (r"\b(hostel|accommodation|room|dorm)\b",        "hostel_inquiry"),
            (r"\b(scholarship|financial aid|bursary)\b",     "scholarship_inquiry"),
            (r"\b(exam|exam schedule|timetable|hall ticket)\b", "exam_inquiry"),
            (r"\b(course|subject|syllabus|curriculum)\b",    "course_inquiry"),
            (r"\b(faculty|professor|teacher|lecturer)\b",    "faculty_inquiry"),
            (r"\b(library|book|borrow|return)\b",            "library_inquiry"),
        ]
        true_intent = "unknown"
        for pattern, intent in rules:
            if re.search(pattern, query):
                true_intent = intent
                break

        # Suggest an FAQ entry when intent differs from detected one
        suggested_faq = None
        if true_intent != row["intent"]:
            suggested_faq = (
                f"Q: {row['user_query']}\n"
                f"A: [Please provide an answer for '{true_intent}']"
            )

        return {
            "interaction_id": row["id"],
            "true_intent":    true_intent,
            "suggested_faq":  suggested_faq,
            "reviewer_notes": (
                "Auto-labelled" if true_intent != "unknown"
                else "Could not determine intent – needs human review"
            ),
        }

    # ------------------------------------------------------------------
    def label_sample(self, since_hours: int = 24) -> list[dict]:
        """Select sample, label each row, persist, return labels."""
        rows   = self.select_sample(since_hours)
        labels = []
        cur    = self.conn.cursor()

        for row in rows:
            label = self.auto_label(row)
            cur.execute(
                """
                INSERT INTO labelled_samples
                    (interaction_id, true_intent, suggested_faq, reviewer_notes)
                VALUES (?, ?, ?, ?)
                """,
                (
                    label["interaction_id"],
                    label["true_intent"],
                    label["suggested_faq"],
                    label["reviewer_notes"],
                ),
            )
            labels.append(label)

        self.conn.commit()
        print(f"  [Labeller] Labelled {len(labels)} interactions.")
        return labels


# ─────────────────────────────────────────────
# 4.  IMPROVEMENT PROPOSER
# ─────────────────────────────────────────────

class ImprovementProposer:
    """
    Analyses logged interactions and labelled samples to propose:
      - New intents     (clusters of 'unknown' queries)
      - New FAQs        (frequently asked, unresolved questions)
      - Better patterns (intents with poor confidence scores)
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        min_cluster_size: int = 3,
        low_confidence_threshold: float = 0.65,
        unresolved_freq_threshold: int = 2,
    ):
        self.conn        = conn
        self.min_cluster = min_cluster_size
        self.low_conf    = low_confidence_threshold
        self.unresolvedN = unresolved_freq_threshold

    # ------------------------------------------------------------------
    def _fetch_recent(self, hours: int = 48) -> list[sqlite3.Row]:
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        return self.conn.execute(
            "SELECT * FROM interactions WHERE created_at >= ?", (since,)
        ).fetchall()

    # ------------------------------------------------------------------
    def propose_new_intents(self, rows: list[sqlite3.Row]) -> list[dict]:
        """
        Find 'unknown' or NULL-intent queries.
        Group by simple keyword fingerprint; flag clusters >= min_cluster_size.
        """
        unknown_queries = [
            r["user_query"]
            for r in rows
            if r["intent"] in (None, "unknown", "fallback")
        ]

        # Fingerprint = most-common meaningful word in query
        stop = {"i","me","my","the","a","an","is","are","was","were",
                "do","does","can","could","would","please","what","how",
                "when","where","why","who","which","will","should","get","have"}

        fingerprints: dict[str, list[str]] = defaultdict(list)
        for q in unknown_queries:
            words = [w for w in re.findall(r"\b[a-z]+\b", q.lower()) if w not in stop]
            key   = words[0] if words else "misc"
            fingerprints[key].append(q)

        proposals = []
        for key, examples in fingerprints.items():
            if len(examples) >= self.min_cluster:
                proposals.append({
                    "proposal_type":   "new_intent",
                    "title":           f"New intent candidate: '{key}'",
                    "description":     (
                        f"{len(examples)} student queries match the keyword '{key}' "
                        f"but were not handled by any existing intent. "
                        f"Consider adding a dedicated intent for this topic."
                    ),
                    "example_queries": examples[:5],
                    "priority":        "high" if len(examples) >= self.min_cluster * 2 else "medium",
                })
        return proposals

    # ------------------------------------------------------------------
    def propose_new_faqs(self, rows: list[sqlite3.Row]) -> list[dict]:
        """
        Unresolved questions that appear repeatedly → good FAQ candidates.
        """
        unresolved = [r["user_query"] for r in rows if not r["resolved"]]
        counts     = Counter(unresolved)

        proposals = []
        for query, cnt in counts.items():
            if cnt >= self.unresolvedN:
                proposals.append({
                    "proposal_type":   "new_faq",
                    "title":           f"Frequent unanswered question ({cnt}×)",
                    "description":     (
                        f"The query \"{query}\" was asked {cnt} times "
                        f"without a satisfactory answer. "
                        f"Add it (or a generalisation) to the FAQ database."
                    ),
                    "example_queries": [query],
                    "priority":        "high" if cnt >= self.unresolvedN * 2 else "medium",
                })
        return proposals

    # ------------------------------------------------------------------
    def propose_better_patterns(self, rows: list[sqlite3.Row]) -> list[dict]:
        """
        Intents that consistently score low confidence → pattern needs work.
        """
        intent_scores: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            if r["intent"] and r["confidence"] is not None:
                intent_scores[r["intent"]].append(r["confidence"])

        proposals = []
        for intent, scores in intent_scores.items():
            avg = sum(scores) / len(scores)
            if avg < self.low_conf and len(scores) >= 2:
                proposals.append({
                    "proposal_type":   "better_pattern",
                    "title":           f"Improve pattern for intent '{intent}'",
                    "description":     (
                        f"Intent '{intent}' has an average confidence of "
                        f"{avg:.0%} across {len(scores)} interactions "
                        f"(threshold: {self.low_conf:.0%}). "
                        f"Expand training examples or refine regex/NLU patterns."
                    ),
                    "example_queries": [
                        r["user_query"] for r in rows
                        if r["intent"] == intent and (r["confidence"] or 1) < self.low_conf
                    ][:5],
                    "priority": "high" if avg < 0.45 else "medium",
                })
        return proposals

    # ------------------------------------------------------------------
    def run(self, hours: int = 48) -> list[dict]:
        """Run all analysers, persist proposals, return them."""
        rows      = self._fetch_recent(hours)
        proposals = (
            self.propose_new_intents(rows)
            + self.propose_new_faqs(rows)
            + self.propose_better_patterns(rows)
        )

        cur = self.conn.cursor()
        for p in proposals:
            cur.execute(
                """
                INSERT INTO improvement_proposals
                    (proposal_type, title, description, example_queries, priority)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    p["proposal_type"],
                    p["title"],
                    p["description"],
                    json.dumps(p["example_queries"]),
                    p["priority"],
                ),
            )
        self.conn.commit()
        print(f"  [Proposer] Generated {len(proposals)} improvement proposals.")
        return proposals


# ─────────────────────────────────────────────
# 5.  ANALYTICS DASHBOARD (text summary)
# ─────────────────────────────────────────────

class AnalyticsDashboard:
    """Prints a readable summary of key metrics."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def report(self, hours: int = 48) -> None:
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cur   = self.conn.cursor()

        total = cur.execute(
            "SELECT COUNT(*) FROM interactions WHERE created_at >= ?", (since,)
        ).fetchone()[0]

        resolved = cur.execute(
            "SELECT COUNT(*) FROM interactions WHERE resolved=1 AND created_at >= ?", (since,)
        ).fetchone()[0]

        unresolved = total - resolved

        top_intents = cur.execute(
            """
            SELECT intent, COUNT(*) as cnt
            FROM interactions
            WHERE created_at >= ? AND intent IS NOT NULL
            GROUP BY intent ORDER BY cnt DESC LIMIT 5
            """,
            (since,),
        ).fetchall()

        low_conf = cur.execute(
            """
            SELECT COUNT(*) FROM interactions
            WHERE confidence < 0.65 AND created_at >= ?
            """,
            (since,),
        ).fetchone()[0]

        proposals = cur.execute(
            "SELECT proposal_type, COUNT(*) cnt FROM improvement_proposals GROUP BY proposal_type"
        ).fetchall()

        neg_feedback = cur.execute(
            "SELECT COUNT(*) FROM interactions WHERE feedback='negative' AND created_at >= ?",
            (since,),
        ).fetchone()[0]

        print("\n" + "═" * 55)
        print(f"  📊  ANALYTICS REPORT  (last {hours}h)")
        print("═" * 55)
        print(f"  Total interactions : {total}")
        print(f"  Resolved           : {resolved}  ({resolved/max(total,1):.0%})")
        print(f"  Unresolved         : {unresolved}")
        print(f"  Low-confidence     : {low_conf}")
        print(f"  Negative feedback  : {neg_feedback}")
        print()
        print("  Top 5 Intents:")
        for row in top_intents:
            print(f"    • {row['intent']:<25} {row['cnt']:>4} queries")
        print()
        print("  Improvement Proposals:")
        for row in proposals:
            print(f"    • {row['proposal_type']:<20} {row['cnt']:>3} proposals")
        print("═" * 55 + "\n")


# ─────────────────────────────────────────────
# 6.  DEMO  –  end-to-end simulation
# ─────────────────────────────────────────────

SAMPLE_INTERACTIONS = [
    # (session_id, query, response, intent, confidence, resolved)
    ("s1", "What is the last date to pay fees?",
     "The fee payment deadline is 15th April.", "deadline_inquiry", 0.91, True),
    ("s1", "How can I get a scholarship?",
     "You can apply via the scholarship portal.", "scholarship_inquiry", 0.85, True),
    ("s2", "When will results be declared?",
     "Results are expected by 30th April.", "result_inquiry", 0.78, True),
    ("s2", "Is the hostel available for girls?",
     "Yes, a dedicated girls hostel is available.", "hostel_inquiry", 0.72, True),
    ("s3", "What documents are needed for admission?",
     "You need mark sheets, ID proof, and photos.", "admission_inquiry", 0.55, True),
    ("s3", "How do I reset my student portal password?",
     "I'm sorry, I don't have that information.", None, None, False),
    ("s4", "Tell me about placement statistics",
     "Fallback: I couldn't find that info.", "fallback", 0.30, False),
    ("s4", "Can I change my course after admission?",
     "Fallback: Please contact the registrar.", "fallback", 0.40, False),
    ("s5", "What are the library timings?",
     "Library is open 8 AM – 10 PM on weekdays.", "library_inquiry", 0.88, True),
    ("s5", "How do I get a bonafide certificate?",
     "I'm not sure about that.", None, None, False),
    ("s6", "Fee structure for engineering?",
     "Engineering fee is ₹80,000/year.", "fee_inquiry", 0.60, True),
    ("s6", "What is the process for internship registration?",
     "Fallback: I don't have details.", "fallback", 0.28, False),
    ("s7", "How to reset my student portal password?",
     "Please contact the IT helpdesk.", None, None, False),
    ("s7", "How to reset my student portal password?",  # repeated unanswered
     "Sorry, I don't know.", None, None, False),
    ("s8", "What are the exam dates for semester 4?",
     "Semester 4 exams start 10th May.", "exam_inquiry", 0.50, True),
    ("s8", "I need my transcript urgently",
     "Fallback: Please visit the admin office.", "fallback", 0.35, False),
    ("s9", "Tell me about placement statistics",      # repeated unknown
     "Fallback.", "fallback", 0.29, False),
    ("s9", "placement statistics for 2024",
     "Fallback.", "fallback", 0.31, False),
    ("s10", "What is the anti-ragging policy?",
     "Fallback: Contact the disciplinary committee.", None, None, False),
    ("s10", "Can I get a duplicate ID card?",
     "Fallback: Visit the admin office.", None, None, False),
]


def run_demo():
    print("\n" + "━" * 55)
    print("  Student Chatbot  –  Analytics & Continuous Improvement")
    print("━" * 55)

    # ── Setup ──
    conn      = init_db()
    logger    = InteractionLogger(conn)
    labeller  = SampleLabeller(conn, sample_size=10, low_confidence_threshold=0.60)
    proposer  = ImprovementProposer(conn, min_cluster_size=2, unresolved_freq_threshold=2)
    dashboard = AnalyticsDashboard(conn)

    # ── Step 1 : Log interactions ──
    print("\n[STEP 1] Logging simulated interactions …")
    interaction_ids = []
    for session, query, response, intent, conf, resolved in SAMPLE_INTERACTIONS:
        iid = logger.log(session, query, response, intent, conf, resolved)
        interaction_ids.append(iid)

    # Simulate some feedback
    logger.update_feedback(interaction_ids[5],  "negative")
    logger.update_feedback(interaction_ids[11], "negative")
    logger.update_feedback(interaction_ids[0],  "positive")
    logger.update_feedback(interaction_ids[2],  "positive")

    # ── Step 2 : Label sample ──
    print("\n[STEP 2] Labelling a sample …")
    labels = labeller.label_sample(since_hours=72)
    print(f"\n  Sample labels (first 5):")
    for lbl in labels[:5]:
        print(f"    id={lbl['interaction_id']:>3}  "
              f"true_intent={lbl['true_intent']:<25} "
              f"notes={lbl['reviewer_notes']}")

    # ── Step 3 : Propose improvements ──
    print("\n[STEP 3] Generating improvement proposals …")
    proposals = proposer.run(hours=72)
    print(f"\n  Proposals (first 6):")
    for p in proposals[:6]:
        print(f"\n  [{p['priority'].upper()}] {p['proposal_type']}")
        print(f"    Title : {p['title']}")
        print(f"    Desc  : {p['description'][:120]}…")
        if p["example_queries"]:
            print(f"    Examples: {p['example_queries'][:2]}")

    # ── Step 4 : Dashboard ──
    print("\n[STEP 4] Analytics Dashboard …")
    dashboard.report(hours=72)

    print("  ✅  Demo complete.  Database saved to:", DB_PATH.resolve())
    conn.close()


if __name__ == "__main__":
    run_demo()
