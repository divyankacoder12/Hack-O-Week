
import re
import string

# ── Stopwords (common English words to remove) ──────────────
STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "can", "i", "me", "my", "we", "our", "you", "your", "he",
    "she", "they", "them", "their", "this", "that", "these",
    "those", "what", "which", "who", "how", "when", "where",
    "with", "from", "by", "about", "as", "into", "through",
    "so", "if", "its", "also", "just", "up", "out", "than",
    "then", "some", "any", "no", "more", "very", "too", "much",
    "get", "got", "please", "tell", "let", "know", "want",
    "need", "hi", "hello", "hey"
}

# ── Spelling Normalization Dictionary ───────────────────────
# Common misspellings and abbreviations used by students
SPELLING_MAP = {
    # Abbreviations
    "u": "you",
    "r": "are",
    "ur": "your",
    "hw": "homework",
    "hm": "homework",
    "hmwrk": "homework",
    "asgn": "assignment",
    "assgn": "assignment",
    "assgnmt": "assignment",
    "sem": "semester",
    "semstr": "semester",
    "dept": "department",
    "lib": "library",
    "msg": "message",
    "plz": "please",
    "pls": "please",
    "thnx": "thanks",
    "thx": "thanks",
    "btw": "by the way",
    "tbh": "to be honest",
    "asap": "as soon as possible",
    "fyi": "for your information",
    "wrt": "with respect to",

    # Common misspellings
    "admsion": "admission",
    "admision": "admission",
    "admisn": "admission",
    "addmission": "admission",
    "addmision": "admission",
    "libary": "library",
    "libraery": "library",
    "librery": "library",
    "schdule": "schedule",
    "schedual": "schedule",
    "shcedule": "schedule",
    "scheduale": "schedule",
    "tution": "tuition",
    "tuision": "tuition",
    "totion": "tuition",
    "feees": "fees",
    "fes": "fees",
    "coures": "courses",
    "cources": "courses",
    "corses": "courses",
    "corse": "course",
    "courese": "course",
    "hostle": "hostel",
    "hostell": "hostel",
    "hstel": "hostel",
    "examn": "exam",
    "exame": "exam",
    "exams": "exams",
    "collage": "college",
    "colege": "college",
    "univeristy": "university",
    "univercity": "university",
    "universty": "university",
    "proffesor": "professor",
    "professer": "professor",
    "proffessor": "professor",
    "semister": "semester",
    "semeseter": "semester",
    "semster": "semester",
    "assigment": "assignment",
    "assignement": "assignment",
    "assignmnt": "assignment",
    "timetabel": "timetable",
    "timetbale": "timetable",
    "recieve": "receive",
    "beleive": "believe",
    "occured": "occurred",
    "grammer": "grammar",
    "writting": "writing",
    "studing": "studying",
    "calender": "calendar",
    "freind": "friend",
    "begining": "beginning",
    "seperete": "separate",
    "definately": "definitely",
    "goverment": "government",
    "labrotory": "laboratory",
    "labratory": "laboratory",
    "laborotory": "laboratory",
}


# ════════════════════════════════════════════════════════════
#  PREPROCESSING PIPELINE — STEP BY STEP
# ════════════════════════════════════════════════════════════

def step1_lowercase(text: str) -> str:
    """Step 1: Convert all text to lowercase."""
    return text.lower()


def step2_punctuation_handling(text: str) -> str:
    """
    Step 2: Handle punctuation.
    - Preserve apostrophes in contractions (don't → dont)
    - Replace all other punctuation with a space
    """
    # Remove apostrophes (contractions)
    text = re.sub(r"'", "", text)
    # Replace punctuation/special chars with space
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def step3_tokenize(text: str) -> list:
    """Step 3: Split text into individual word tokens."""
    tokens = text.split()
    return tokens


def step4_remove_stopwords(tokens: list) -> list:
    """Step 4: Remove common stopwords from token list."""
    filtered = [token for token in tokens if token not in STOPWORDS]
    return filtered


def step5_spelling_normalization(tokens: list) -> list:
    """
    Step 5: Normalize spellings using the dictionary map.
    Corrects abbreviations and common misspellings.
    """
    normalized = [SPELLING_MAP.get(token, token) for token in tokens]
    return normalized


def preprocess(query: str) -> dict:
    """
    Full preprocessing pipeline.
    Returns a dict with each step's output for transparency.
    """
    original = query

    s1 = step1_lowercase(original)
    s2 = step2_punctuation_handling(s1)
    s3 = step3_tokenize(s2)
    s4 = step4_remove_stopwords(s3)
    s5 = step5_spelling_normalization(s4)

    return {
        "original":              original,
        "1_lowercased":          s1,
        "2_punctuation_cleaned": s2,
        "3_tokens":              s3,
        "4_stopwords_removed":   s4,
        "5_normalized":          s5,
        "final_query":           " ".join(s5)
    }


# ════════════════════════════════════════════════════════════
#  DISPLAY HELPER
# ════════════════════════════════════════════════════════════

def print_pipeline(result: dict):
    """Print only the input query and final preprocessed output."""
    divider = "─" * 60
    print(f"\n{divider}")
    print(f"  INPUT  : {result['original']}")
    print(f"  OUTPUT : {result['final_query']}")
    print(divider)


# ════════════════════════════════════════════════════════════
#  DEMO — Sample Student Queries
# ════════════════════════════════════════════════════════════

SAMPLE_QUERIES = [
    "What are the FEES for BTech admision?",
    "Plz tell me the HOSTLE facilities!!",
    "Is the collage open on Saturday or not?",
    "Hi, can u tell me abt the coures offered?",
    
]


def main():
    print("=" * 60)
    print("   STUDENT QUERY PREPROCESSING PIPELINE")
    print("=" * 60)

    print("\n  DEMO — Sample Student Queries")
    print("━" * 60)

    for query in SAMPLE_QUERIES:
        result = preprocess(query)
        print_pipeline(result)

    # Interactive mode
    print("\n" + "=" * 60)
    print("  INTERACTIVE MODE — Enter your own query")
    print("  (type 'exit' to quit)")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n  Enter query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Exiting. Goodbye!]")
            break

        if not user_input:
            print("  Please enter a query.")
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print("  Exiting preprocessor. Goodbye!")
            break

        result = preprocess(user_input)
        print_pipeline(result)


if __name__ == "__main__":
    main()