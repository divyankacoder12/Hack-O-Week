"""
Entity Extraction for Dates, Course Codes, and Semester Numbers
Extracts structured entities from natural language academic queries.
"""

import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# Data Model
# ──────────────────────────────────────────────

@dataclass
class ExtractedEntities:
    dates: list[str] = field(default_factory=list)
    course_codes: list[str] = field(default_factory=list)
    semesters: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    intent: Optional[str] = None

    def has_any(self) -> bool:
        return any([self.dates, self.course_codes, self.semesters, self.subjects])


# ──────────────────────────────────────────────
# Patterns
# ──────────────────────────────────────────────

# Semester: SEM 5, Semester 3, 5th sem, S3
SEMESTER_PATTERNS = [
    r'\bsem(?:ester)?\s*(\d{1,2})\b',          # SEM 5, semester 3
    r'\b(\d{1,2})(?:st|nd|rd|th)\s+sem\b',      # 5th sem
    r'\bs(\d{1,2})\b',                           # S3
    r'\bsem-(\d{1,2})\b',                        # SEM-4
]

# Course Codes: CS101, ECE-302, MATH 201, BCA3, CS, ECE, MATH
COURSE_CODE_PATTERNS = [
    r'\b([A-Z]{2,5}[-\s]?\d{3,4})\b',           # CS101, ECE-302, MATH 201
    r'\b([A-Z]{2,5}\d{1,2})\b',                  # BCA3, CS6
    r'\b(CS|ECE|EEE|MECH|CIVIL|IT|BCA|MCA|MBA|AI|ML|DS|MATH|PHY|CHEM|BIO)\b',  # Subject tags
]

# Date patterns
DATE_PATTERNS = [
    # DD/MM/YYYY or DD-MM-YYYY
    (r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', '%d/%m/%Y'),
    # Month name: 25 January 2025, January 25 2025
    (r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4})\b', '%d %B %Y'),
    (r'\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{4})\b', '%B %d %Y'),
    # Relative dates
    (r'\b(today|tomorrow|yesterday)\b', None),
    # Month + Year: January 2025
    (r'\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4})\b', None),
    # YYYY-MM-DD
    (r'\b(\d{4}-\d{2}-\d{2})\b', '%Y-%m-%d'),
]

# Intent keywords
INTENT_MAP = {
    'exam_schedule': ['exam', 'test', 'quiz', 'schedule', 'timetable', 'when is'],
    'result':        ['result', 'score', 'grade', 'marks', 'pass', 'fail'],
    'syllabus':      ['syllabus', 'curriculum', 'topics', 'subjects', 'course content'],
    'admission':     ['admission', 'enroll', 'apply', 'application', 'deadline'],
    'fee':           ['fee', 'fees', 'payment', 'cost', 'tuition'],
    'holiday':       ['holiday', 'vacation', 'break', 'off', 'leave'],
}


# ──────────────────────────────────────────────
# Extractor
# ──────────────────────────────────────────────

class EntityExtractor:
    def __init__(self):
        self.semester_patterns = [re.compile(p, re.IGNORECASE) for p in SEMESTER_PATTERNS]
        self.course_patterns   = [re.compile(p, re.IGNORECASE) for p in COURSE_CODE_PATTERNS]
        self.date_patterns     = [(re.compile(p, re.IGNORECASE), fmt) for p, fmt in DATE_PATTERNS]

    # ---------- Semester ----------
    def _extract_semesters(self, text: str) -> list[str]:
        found = []
        for pattern in self.semester_patterns:
            for match in pattern.finditer(text):
                sem_num = match.group(1)
                label = f"SEM {sem_num}"
                if label not in found:
                    found.append(label)
        return found

    # ---------- Course Codes ----------
    def _extract_courses(self, text: str) -> list[str]:
        found = []
        seen  = set()
        for pattern in self.course_patterns:
            for match in pattern.finditer(text):
                code = match.group(1).upper().replace(' ', '-').replace('--', '-')
                if code not in seen:
                    seen.add(code)
                    found.append(code)
        return found

    # ---------- Dates ----------
    def _extract_dates(self, text: str) -> list[str]:
        found = []
        seen  = set()
        for pattern, fmt in self.date_patterns:
            for match in pattern.finditer(text):
                raw = match.group(1).strip()
                if raw.lower() in seen:
                    continue
                seen.add(raw.lower())
                # Normalize if format is known
                if fmt:
                    try:
                        normalized = raw.replace('-', '/') if '%d/%m/%Y' in fmt else raw
                        dt = datetime.strptime(normalized, fmt)
                        found.append(dt.strftime('%d %b %Y'))
                        continue
                    except ValueError:
                        pass
                found.append(raw)
        return found

    # ---------- Intent ----------
    def _detect_intent(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for intent, keywords in INTENT_MAP.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        return 'general'

    # ---------- Main ----------
    def extract(self, text: str) -> ExtractedEntities:
        entities = ExtractedEntities(
            dates        = self._extract_dates(text),
            course_codes = self._extract_courses(text),
            semesters    = self._extract_semesters(text),
            intent       = self._detect_intent(text),
        )
        return entities


# ──────────────────────────────────────────────
# Response Generator
# ──────────────────────────────────────────────

def generate_response(question: str, entities: ExtractedEntities) -> str:
    """Generate a human-readable response using extracted entities."""
    parts = []

    if not entities.has_any():
        return "I couldn't find specific course, semester, or date information in your question. Could you please be more specific?"

    # Build context string
    context_parts = []
    if entities.semesters:
        context_parts.append(f"**Semester:** {', '.join(entities.semesters)}")
    if entities.course_codes:
        context_parts.append(f"**Course(s):** {', '.join(entities.course_codes)}")
    if entities.dates:
        context_parts.append(f"**Date(s):** {', '.join(entities.dates)}")

    # Intent-specific response
    intent_responses = {
        'exam_schedule': "Here is the exam schedule information I found",
        'result':        "Here are the result details I found",
        'syllabus':      "Here is the syllabus information",
        'admission':     "Here are the admission details",
        'fee':           "Here are the fee-related details",
        'holiday':       "Here are the holiday/break details",
        'general':       "Here is what I found",
    }

    intro = intent_responses.get(entities.intent, "Here is what I found")
    parts.append(f"📌 {intro} from your question:\n")
    parts.extend(context_parts)

    # Compose a natural summary
    summary_parts = []
    if entities.semesters:
        summary_parts.append(entities.semesters[0])
    if entities.course_codes:
        summary_parts.append(entities.course_codes[0])

    if entities.intent == 'exam_schedule':
        subject = ' '.join(summary_parts) if summary_parts else 'your course'
        if entities.dates:
            parts.append(f"\n✅ The exam for **{subject}** is scheduled on **{entities.dates[0]}**.")
        else:
            parts.append(f"\n✅ You asked about the exam schedule for **{subject}**. Please check the official portal for exact dates.")
    elif entities.intent == 'result':
        subject = ' '.join(summary_parts) if summary_parts else 'your course'
        parts.append(f"\n✅ Fetching result details for **{subject}**...")
    else:
        if summary_parts:
            parts.append(f"\n✅ Processing query for: **{' | '.join(summary_parts)}**")

    return '\n'.join(parts)


# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

def run_demo():
    extractor = EntityExtractor()

    test_questions = [
        "When is SEM 5 CS exam?",
        "What is the result of ECE-302 for semester 3?",
        "Is there a holiday on 25 December 2025?",
        "Show me the syllabus for MATH201 in 2nd sem",
        "When does the BCA3 admission close? Deadline is 15/08/2025",
        "CS101 and ECE 202 exam timetable for S6?",
        "What are the fees for MBA semester 1?",
        "Tell me about the 3rd sem AI exam on January 10 2026",
    ]

    print("=" * 65)
    print("       ENTITY EXTRACTION — ACADEMIC QUERY PARSER")
    print("=" * 65)

    for q in test_questions:
        print(f"\n🔷 Question: {q}")
        entities = extractor.extract(q)

        print(f"   📦 Entities Extracted:")
        print(f"      Semesters   : {entities.semesters or '—'}")
        print(f"      Courses     : {entities.course_codes or '—'}")
        print(f"      Dates       : {entities.dates or '—'}")
        print(f"      Intent      : {entities.intent}")

        response = generate_response(q, entities)
        print(f"\n   💬 Response:\n   {response.replace(chr(10), chr(10) + '   ')}")
        print("-" * 65)


if __name__ == "__main__":
    run_demo()
