# ============================================================
#  SIT FAQ Chatbot — Rule-Based (Pattern Matching)
#  Symbiosis Institute of Technology, Nagpur
# ============================================================

import re

# ── FAQ Knowledge Base ───────────────────────────────────────

FAQ_RULES = [
    {
        "patterns": ["course", "program", "branch", "btech", "engineering",
                     "cs", "cse", "computer science", "stream", "degree"],
        "topic": "COURSES",
        "response": (
            "Symbiosis Institute of Technology offers BTech programs in "
            "Computer Science, Electronics & Telecommunication, Mechanical "
            "Engineering, and other specialisations under Symbiosis International University."
        )
    },
    {
        "patterns": ["fee", "fees", "cost", "price", "tuition", "payment",
                     "scholarship", "amount", "charges"],
        "topic": "FEES",
        "response": (
            "The fee structure varies by course and category. Please visit "
            "the official Symbiosis website at symbiosis.ac.in for exact details."
        )
    },
    {
        "patterns": ["admission", "apply", "application", "entrance", "exam",
                     "merit", "eligibility", "criteria", "selection", "seat", "enroll", "join"],
        "topic": "ADMISSION",
        "response": (
            "Admissions are based on entrance exams and merit as per Symbiosis guidelines. "
            "Candidates typically need to qualify SET (Symbiosis Entrance Test) along with "
            "a personal interaction round."
        )
    },
    {
        "patterns": ["timing", "time", "hours", "schedule", "open",
                     "class", "lecture", "when", "office hours"],
        "topic": "COLLEGE TIMING",
        "response": (
            "College timing is from 9:00 AM to 5:00 PM, Monday to Friday. "
            "Administrative offices generally follow the same schedule."
        )
    },
    {
        "patterns": ["location", "address", "where", "place", "city", "nagpur",
                     "situated", "campus", "map", "route", "distance"],
        "topic": "LOCATION",
        "response": (
            "Symbiosis Institute of Technology is located in Nagpur, Maharashtra. "
            "The campus is well-connected by road and public transport."
        )
    },
    {
        "patterns": ["contact", "phone", "email", "call", "reach",
                     "helpline", "number", "enquiry", "inquiry"],
        "topic": "CONTACT",
        "response": (
            "You can contact the college office through the official Symbiosis website "
            "(symbiosis.ac.in) or visit the campus admissions desk during working hours."
        )
    },
    {
        "patterns": ["hostel", "accommodation", "stay", "dorm", "dormitory",
                     "residential", "room", "pg", "living"],
        "topic": "HOSTEL",
        "response": (
            "Yes, hostel facilities are available for students. Separate hostels are provided "
            "for male and female students with basic amenities, Wi-Fi, and mess facilities."
        )
    },
    {
        "patterns": ["library", "book", "books", "reading", "study",
                     "resource", "reference", "journal", "digital library"],
        "topic": "LIBRARY",
        "response": (
            "The library is open from 9:00 AM to 6:00 PM on working days. It houses a wide "
            "collection of technical books, journals, research papers, and digital resources."
        )
    },
    {
        "patterns": ["principal", "director", "head", "management", "authority",
                     "vice chancellor", "chancellor", "dean", "administration", "university"],
        "topic": "MANAGEMENT",
        "response": (
            "The institute is managed under Symbiosis International University (SIU), "
            "a deemed-to-be university recognised by UGC and accredited with NAAC."
        )
    },
    {
        "patterns": ["placement", "job", "recruit", "company", "hiring",
                     "salary", "package", "career"],
        "topic": "PLACEMENTS",
        "response": (
            "SIT has an active Training & Placement Cell that facilitates campus recruitment drives. "
            "Several reputed companies visit for placements each year. "
            "For statistics, check the official website."
        )
    },
    {
        "patterns": ["sports", "gym", "ground", "football", "cricket",
                     "basketball", "game", "activity", "club", "extracurricular"],
        "topic": "SPORTS & ACTIVITIES",
        "response": (
            "The campus offers sports facilities including grounds for cricket, football, "
            "and other activities. Various student clubs and cultural events are organised "
            "throughout the year."
        )
    },
    {
        "patterns": ["canteen", "food", "mess", "cafeteria", "eat",
                     "lunch", "tiffin", "restaurant"],
        "topic": "CANTEEN",
        "response": (
            "The campus has a canteen and mess facility providing meals throughout "
            "the day at reasonable rates."
        )
    },
    {
        "patterns": ["transport", "bus", "commute", "pickup", "drop", "vehicle", "travel"],
        "topic": "TRANSPORT",
        "response": (
            "The college does not operate its own fleet, but Nagpur city buses and "
            "auto-rickshaws provide connectivity. For hostel students, transport to "
            "key city areas may be coordinated."
        )
    },
    {
        "patterns": ["wifi", "internet", "network", "connectivity", "broadband", "lan"],
        "topic": "INTERNET",
        "response": (
            "High-speed Wi-Fi internet is available across the campus, including "
            "classrooms, labs, the library, and hostel buildings."
        )
    },
    {
        "patterns": ["lab", "laboratory", "computer lab", "research",
                     "equipment", "infrastructure", "facility"],
        "topic": "LABS & INFRASTRUCTURE",
        "response": (
            "SIT has well-equipped computer labs, electronics labs, and research facilities. "
            "The infrastructure supports modern engineering education with up-to-date equipment."
        )
    },
]

# ── Rule-Based Engine ────────────────────────────────────────

def get_response(user_input: str) -> tuple[str, str]:
    """
    Rule-based FAQ responder using pattern matching.
    Returns (topic, response) tuple.
    """
    text = user_input.lower().strip()

    # ── if-elif chain for special intents ──────────────────
    if re.search(r"\b(hi|hello|hey|good morning|good evening|namaste)\b", text):
        return ("GREETING",
                "Hello! Welcome to the SIT Help Desk 🎓. "
                "Ask me anything about courses, fees, admissions, hostel, "
                "library, or any other campus-related query!")

    elif re.search(r"\b(thank|thanks|thank you|thx|ty|appreciate)\b", text):
        return ("THANKS",
                "You're welcome! Feel free to ask if you have more questions "
                "about Symbiosis Institute of Technology.")

    elif re.search(r"\b(bye|goodbye|see you|exit|quit|take care)\b", text):
        return ("GOODBYE",
                "Goodbye! Best of luck with your academic journey at SIT. "
                "Don't hesitate to return if you have more questions!")

    elif re.search(r"\b(help|menu|what can you|options|topics)\b", text):
        topics = [rule["topic"] for rule in FAQ_RULES]
        return ("HELP",
                "I can answer questions on: " + ", ".join(topics) + ". Just ask!")

    # ── pattern matching loop for FAQ rules ────────────────
    for rule in FAQ_RULES:
        for keyword in rule["patterns"]:
            if keyword in text:
                return (rule["topic"], rule["response"])

    # ── fallback (else branch) ─────────────────────────────
    return ("UNKNOWN",
            "I'm not sure about that. You can ask me about: courses, fees, "
            "admission, timing, location, contact, hostel, library, placements, "
            "labs, Wi-Fi, sports, canteen, or transport. "
            "Or visit symbiosis.ac.in for full details.")


# ── CLI Chat Loop ────────────────────────────────────────────

def print_divider():
    print("─" * 58)

def main():
    print_divider()
    print("  🎓 SIT FAQ Chatbot — Symbiosis Institute of Technology")
    print("     Nagpur, Maharashtra | Rule-Based Assistant")
    print_divider()
    print("  Type your question below. Type 'bye' to exit.")
    print_divider()

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  [Exiting chatbot. Goodbye!]")
            break

        if not user_input:
            print("  Bot: Please type a question.")
            continue

        topic, response = get_response(user_input)

        print(f"\n  [{topic}]")
        print(f"  Bot: {response}")

        # Exit on goodbye
        if topic == "GOODBYE":
            break

    print_divider()


if __name__ == "__main__":
    main()