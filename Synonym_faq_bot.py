import re

SYNONYM_GROUPS = {
    "fees": [
        "fees", "fee", "tuition", "tution", "tuision", "payment",
        "cost", "price", "charges", "amount", "scholarship",
        "expense", "expenditure", "feees", "fes", "pay", "paid",
        "money", "afford", "costly", "cheap", "expensive", "rate"
    ],
    "courses": [
        "courses", "course", "program", "programmes", "branch",
        "btech", "b.tech", "engineering", "degree", "stream",
        "cs", "cse", "computer science", "it", "mechanical",
        "electronics", "specialisation", "coures", "cources",
        "corses", "courese", "corse", "curriculum", "syllabus",
        "subjects", "subject", "field", "discipline", "study"
    ],
    "admission": [
        "admission", "admision", "admsion", "addmission", "admisn",
        "apply", "application", "enroll", "enrolment", "enrollment",
        "entrance", "exam", "merit", "eligibility", "criteria",
        "selection", "seat", "join", "registration", "register",
        "qualify", "set", "entrance test", "cut off", "cutoff",
        "rank", "form", "intake", "procedure", "process"
    ],
    "timing": [
        "timing", "timings", "time", "times", "hours", "hour",
        "schedule", "schedual", "schdule", "timetable", "timetabel",
        "open", "close", "when", "office hours", "working hours",
        "class", "classes", "lecture", "lectures", "start", "end",
        "begin", "beginning", "duration", "period", "shift"
    ],
    "location": [
        "location", "address", "where", "place", "city", "nagpur",
        "situated", "campus", "map", "route", "distance", "near",
        "directions", "how to reach", "reach", "find", "situated",
        "area", "zone", "region", "state", "maharashtra", "pin"
    ],
    "contact": [
        "contact", "phone", "email", "call", "reach", "helpline",
        "number", "enquiry", "inquiry", "query", "support",
        "office", "talk", "speak", "message", "msg", "whatsapp",
        "connect", "communicate", "touch", "info", "details"
    ],
    "hostel": [
        "hostel", "hostle", "hostell", "hstel", "accommodation",
        "stay", "dorm", "dormitory", "residential", "room", "rooms",
        "pg", "living", "residence", "lodge", "lodging", "boarding",
        "bed", "quarter", "flat", "housing", "bunk", "facility"
    ],
    "library": [
        "library", "libary", "libraery", "librery", "lib",
        "book", "books", "reading", "study", "resource",
        "reference", "journal", "journals", "digital library",
        "e-library", "elibrary", "read", "borrow", "issue",
        "return", "catalog", "catalogue", "publication", "periodical"
    ],
    "management": [
        "management", "principal", "director", "head", "authority",
        "vice chancellor", "chancellor", "dean", "administration",
        "university", "siu", "symbiosis international", "naac",
        "ugc", "accreditation", "governing", "board", "trust",
        "leadership", "faculty", "staff", "who runs", "in charge"
    ],
    "placements": [
        "placement", "placements", "job", "jobs", "recruit",
        "recruitment", "company", "companies", "hiring", "hire",
        "campus", "salary", "package", "career", "careers",
        "work", "employment", "opportunity", "offer", "letter",
        "internship", "intern", "industry", "drive", "mnc", "it company"
    ],
    "sports": [
        "sports", "sport", "gym", "gymnasium", "ground", "grounds",
        "football", "cricket", "basketball", "badminton", "chess",
        "game", "games", "activity", "activities", "club", "clubs",
        "extracurricular", "cultural", "event", "events", "fest",
        "competition", "tournament", "playground", "fitness"
    ],
    "canteen": [
        "canteen", "food", "mess", "cafeteria", "eat", "eating",
        "lunch", "dinner", "breakfast", "tiffin", "restaurant",
        "snacks", "meal", "meals", "veg", "menu", "drink",
        "water", "juice", "cafe", "dining", "taste", "hunger"
    ],
    "transport": [
        "transport", "transportation", "bus", "buses", "commute",
        "pickup", "drop", "vehicle", "vehicles", "travel",
        "auto", "auto-rickshaw", "rickshaw", "cab", "taxi",
        "how to come", "conveyance", "shuttle", "connectivity"
    ],
    "internet": [
        "wifi", "wi-fi", "internet", "network", "connectivity",
        "broadband", "lan", "online", "connection", "speed",
        "bandwidth", "data", "hotspot", "access", "signal",
        "router", "wireless", "web", "browse", "browsing"
    ],
    "labs": [
        "lab", "labs", "laboratory", "laboratories", "labrotory",
        "labratory", "laborotory", "computer lab", "research",
        "equipment", "infrastructure", "facility", "facilities",
        "workshop", "practical", "practicals", "experiment",
        "instrument", "instruments", "project", "hardware", "software"
    ],
}

# ════════════════════════════════════════════════════════════
#  FAQ ANSWERS
#  One answer per canonical topic key
# ════════════════════════════════════════════════════════════

FAQ_ANSWERS = {
    "fees": (
        "The fee structure varies by course and category. "
        "Please visit the official Symbiosis website at symbiosis.ac.in "
        "for the most accurate and up-to-date fee details."
    ),
    "courses": (
        "Symbiosis Institute of Technology offers BTech programs in "
        "Computer Science, Electronics & Telecommunication, Mechanical "
        "Engineering, and other specialisations under Symbiosis International University."
    ),
    "admission": (
        "Admissions are based on entrance exams and merit as per Symbiosis guidelines. "
        "Candidates typically need to qualify SET (Symbiosis Entrance Test) along "
        "with a personal interaction round."
    ),
    "timing": (
        "College timing is from 9:00 AM to 5:00 PM, Monday to Friday. "
        "Administrative offices generally follow the same schedule."
    ),
    "location": (
        "Symbiosis Institute of Technology is located in Nagpur, Maharashtra. "
        "The campus is well-connected by road and public transport."
    ),
    "contact": (
        "You can contact the college office through the official Symbiosis website "
        "(symbiosis.ac.in) or visit the campus admissions desk during working hours."
    ),
    "hostel": (
        "Yes, hostel facilities are available for students. Separate hostels are "
        "provided for male and female students with basic amenities, Wi-Fi, and mess."
    ),
    "library": (
        "The library is open from 9:00 AM to 6:00 PM on working days. It houses a "
        "wide collection of technical books, journals, research papers, and digital resources."
    ),
    "management": (
        "The institute is managed under Symbiosis International University (SIU), "
        "a deemed-to-be university recognised by UGC and accredited with NAAC."
    ),
    "placements": (
        "SIT has an active Training & Placement Cell that facilitates campus recruitment "
        "drives. Several reputed companies visit for placements each year. "
        "For statistics, check the official website."
    ),
    "sports": (
        "The campus offers sports facilities including grounds for cricket, football, "
        "and other activities. Various student clubs and cultural events are organised "
        "throughout the year."
    ),
    "canteen": (
        "The campus has a canteen and mess facility providing meals throughout "
        "the day at reasonable rates."
    ),
    "transport": (
        "Nagpur city buses and auto-rickshaws provide connectivity to the campus. "
        "For hostel students, transport to key city areas may be coordinated."
    ),
    "internet": (
        "High-speed Wi-Fi internet is available across the campus, including "
        "classrooms, labs, the library, and hostel buildings."
    ),
    "labs": (
        "SIT has well-equipped computer labs, electronics labs, and research facilities. "
        "The infrastructure supports modern engineering education with up-to-date equipment."
    ),
}

# ════════════════════════════════════════════════════════════
#  BUILD REVERSE LOOKUP: synonym word → canonical topic
# ════════════════════════════════════════════════════════════

def build_lookup(synonym_groups: dict) -> dict:
    lookup = {}
    for topic, synonyms in synonym_groups.items():
        for word in synonyms:
            lookup[word.lower()] = topic
    return lookup

SYNONYM_LOOKUP = build_lookup(SYNONYM_GROUPS)

# ════════════════════════════════════════════════════════════
#  TEXT PREPROCESSING
# ════════════════════════════════════════════════════════════

STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "are", "was", "were", "be",
    "been", "have", "has", "do", "does", "did", "will", "would",
    "could", "should", "can", "i", "me", "my", "we", "our", "you",
    "your", "he", "she", "they", "them", "this", "that", "these",
    "those", "which", "with", "from", "by", "about", "into",
    "so", "if", "just", "get", "got", "please", "tell", "let",
    "know", "want", "hi", "hello", "hey", "what", "how", "when",
    "where", "who", "need", "also", "some", "any", "more", "very"
}

SPELLING_MAP = {
    "u": "you", "r": "are", "ur": "your", "plz": "please",
    "pls": "please", "thx": "thanks", "thnx": "thanks",
    "asap": "as soon as possible", "fyi": "for your information",
    "sem": "semester", "dept": "department", "lib": "library",
    "abt": "about", "wrt": "with respect to",
}

def preprocess(text: str) -> list:
    text = text.lower()
    text = re.sub(r"'", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    tokens = [SPELLING_MAP.get(t, t) for t in tokens]
    tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens

# ════════════════════════════════════════════════════════════
#  SYNONYM-AWARE MATCHING ENGINE
# ════════════════════════════════════════════════════════════

def match_topic(tokens: list) -> str | None:
    """
    Scan each token against the synonym lookup.
    Return the first matched canonical topic, or None.
    """
    for token in tokens:
        if token in SYNONYM_LOOKUP:
            return SYNONYM_LOOKUP[token]
    return None

def get_response(user_input: str) -> tuple:
    """
    Full pipeline: preprocess → synonym match → return answer.
    Returns (matched_topic, matched_word, answer).
    """
    # Special intents first
    text = user_input.lower().strip()

    if re.search(r"\b(hi|hello|hey|good morning|good evening|namaste)\b", text):
        return ("GREETING", "-",
                "Hello! Welcome to the SIT FAQ Bot. Ask me about "
                "fees, courses, admission, hostel, library, placements, and more!")

    if re.search(r"\b(bye|goodbye|exit|quit|take care)\b", text):
        return ("GOODBYE", "-", "Goodbye! Best of luck with your journey at SIT!")

    if re.search(r"\b(thank|thanks|thank you|thx)\b", text):
        return ("THANKS", "-", "You're welcome! Feel free to ask anything else.")

    # Preprocess and match
    tokens = preprocess(user_input)
    topic  = match_topic(tokens)

    if topic:
        matched_word = next(t for t in tokens if SYNONYM_LOOKUP.get(t) == topic)
        return (topic.upper(), matched_word, FAQ_ANSWERS[topic])

    return ("UNKNOWN", "-",
            "Sorry, I couldn't find an answer for that. Try asking about: "
            "fees, courses, admission, timing, location, hostel, library, "
            "placements, sports, canteen, transport, internet, or labs.")

# ════════════════════════════════════════════════════════════
#  DEMO — Test synonym variations
# ════════════════════════════════════════════════════════════

TEST_QUERIES = [
    # fees synonyms
    ("What is the tuition for BTech?",          "fees"),
    ("How much payment do I need to make?",      "fees"),
    ("Tell me the charges for admission",         "fees"),
    # courses synonyms
    ("Which programs are available?",             "courses"),
    ("What is the curriculum here?",              "courses"),
    ("List all the subjects offered",             "courses"),
    # admission synonyms
    ("How do I enroll at SIT?",                  "admission"),
    ("What is the eligibility criteria?",         "admission"),
    ("When does registration open?",              "admission"),
    # hostel synonyms
    ("Is there accommodation available?",         "hostel"),
    ("Do you have dormitory facilities?",         "hostel"),
    ("Can I stay in a room on campus?",           "hostel"),
    # library synonyms
    ("Where can I borrow books?",                 "library"),
    ("Is there a digital e-library?",             "library"),
    ("What are the reading room hours?",          "library"),
    # placements synonyms
    ("What companies come for recruitment?",      "placements"),
    ("What salary package can I expect?",         "placements"),
    ("Are there internship opportunities?",       "placements"),
]

def run_demo():
    divider = "─" * 65
    print("=" * 65)
    print("   SYNONYM-AWARE FAQ BOT — SIT Nagpur")
    print("=" * 65)
    print(f"\n  {'QUERY':<40} {'MATCHED TOPIC':<14} {'TRIGGER WORD'}")
    print(divider)

    for query, expected in TEST_QUERIES:
        topic, word, answer = get_response(query)
        match_status = "✓" if topic.lower() == expected else "✗"
        print(f"  {match_status} {query:<40} {topic:<14} [{word}]")

    print(divider)
    print("\n  Sample Answer (fees):")
    print(f"  → {FAQ_ANSWERS['fees']}\n")

# ════════════════════════════════════════════════════════════
#  INTERACTIVE CHAT LOOP
# ════════════════════════════════════════════════════════════

def chat():
    divider = "─" * 65
    print("\n" + "=" * 65)
    print("   INTERACTIVE MODE  —  type 'bye' to exit")
    print("=" * 65)

    while True:
        try:
            user_input = input("\n  You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Exiting. Goodbye!]")
            break

        if not user_input:
            continue

        topic, word, answer = get_response(user_input)

        print(f"\n  [{topic}]  trigger → '{word}'")
        print(f"  Bot : {answer}")
        print(divider)

        if topic == "GOODBYE":
            break

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_demo()
    chat()
