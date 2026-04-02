

import re
import math
from collections import Counter

# ════════════════════════════════════════════════════════════
#  FAQ KNOWLEDGE BASE
#  Each entry has: question + answer
# ════════════════════════════════════════════════════════════

FAQ_DB = [
    {
        "question": "What courses and programs are offered at SIT?",
        "answer": (
            "Symbiosis Institute of Technology offers BTech programs in "
            "Computer Science, Electronics & Telecommunication, and Mechanical "
            "Engineering under Symbiosis International University."
        )
    },
    {
        "question": "What is the fee structure and tuition cost?",
        "answer": (
            "The fee structure varies by course and category. Please visit "
            "symbiosis.ac.in for the most accurate and up-to-date fee details."
        )
    },
    {
        "question": "How does the admission and enrollment process work?",
        "answer": (
            "Admissions are based on entrance exams and merit. Candidates must "
            "qualify the SET (Symbiosis Entrance Test) followed by a personal "
            "interaction round."
        )
    },
    {
        "question": "What are the college timings and office hours?",
        "answer": (
            "College timing is from 9:00 AM to 5:00 PM, Monday to Friday. "
            "Administrative offices follow the same schedule."
        )
    },
    {
        "question": "Where is SIT located and what is the campus address?",
        "answer": (
            "Symbiosis Institute of Technology is located in Nagpur, Maharashtra. "
            "The campus is well-connected by road and public transport."
        )
    },
    {
        "question": "How can I contact the college office or helpdesk?",
        "answer": (
            "You can contact the college through the official website symbiosis.ac.in "
            "or visit the admissions desk during working hours."
        )
    },
    {
        "question": "Is hostel accommodation available for students?",
        "answer": (
            "Yes, hostel facilities are available. Separate hostels are provided "
            "for male and female students with amenities, Wi-Fi, and mess."
        )
    },
    {
        "question": "What are the library timings and book borrowing rules?",
        "answer": (
            "The library is open from 9:00 AM to 6:00 PM on working days. "
            "It offers books, journals, research papers, and digital resources."
        )
    },
    {
        "question": "Who manages and runs the institute administration?",
        "answer": (
            "The institute is managed under Symbiosis International University (SIU), "
            "a deemed-to-be university recognised by UGC and accredited with NAAC."
        )
    },
    {
        "question": "What are the placement opportunities and company recruitments?",
        "answer": (
            "SIT has an active Training and Placement Cell. Reputed companies visit "
            "for campus recruitment. For salary packages and statistics, check "
            "the official website."
        )
    },
    {
        "question": "What sports and extracurricular activities are available?",
        "answer": (
            "The campus has grounds for cricket, football, and basketball. "
            "Student clubs, cultural fests, and events are organised throughout the year."
        )
    },
    {
        "question": "Is there a canteen or food facility on campus?",
        "answer": (
            "Yes, the campus has a canteen and mess providing meals, snacks, "
            "and beverages throughout the day at reasonable rates."
        )
    },
    {
        "question": "What transport and commute options are available to reach campus?",
        "answer": (
            "Nagpur city buses and auto-rickshaws connect well to the campus. "
            "Transport coordination may be available for hostel students."
        )
    },
    {
        "question": "Is WiFi and internet connectivity available on campus?",
        "answer": (
            "High-speed Wi-Fi internet is available across the campus including "
            "classrooms, labs, library, and hostel buildings."
        )
    },
    {
        "question": "What laboratory and research infrastructure does SIT have?",
        "answer": (
            "SIT has well-equipped computer labs, electronics labs, and research "
            "facilities supporting modern engineering education with up-to-date equipment."
        )
    },
    {
        "question": "What scholarship and financial aid options are available?",
        "answer": (
            "Symbiosis offers merit-based and need-based scholarships. "
            "Please visit the official website for eligibility criteria and application details."
        )
    },
    {
        "question": "Are there internship programs for students?",
        "answer": (
            "Yes, SIT encourages internships through its placement cell. "
            "Students can apply through the T&P portal and company drives held on campus."
        )
    },
    {
        "question": "What is the examination and grading system?",
        "answer": (
            "SIT follows the Symbiosis International University grading system "
            "with continuous assessment, mid-semester, and end-semester examinations."
        )
    },
]

# ════════════════════════════════════════════════════════════
#  TEXT PREPROCESSING
# ════════════════════════════════════════════════════════════

STOPWORDS = {
    "a","an","the","is","it","in","on","at","to","for","of","and","or",
    "but","not","are","was","were","be","been","have","has","do","does",
    "did","will","would","could","should","can","i","me","my","we","our",
    "you","your","he","she","they","them","this","that","these","those",
    "what","which","who","how","when","where","with","from","by","about",
    "into","so","if","just","get","want","need","tell","let","know","hi",
    "hello","hey","please","some","any","more","very","much","also","than",
    "then","up","out","its","their","there","here","been","being","having"
}

def tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return tokens

# ════════════════════════════════════════════════════════════
#  TF-IDF ENGINE
# ════════════════════════════════════════════════════════════

class TFIDF:
    def __init__(self):
        self.documents   = []   # raw FAQ questions (for display)
        self.token_docs  = []   # tokenized FAQ questions
        self.idf_scores  = {}   # IDF for each term
        self.tfidf_vecs  = []   # TF-IDF vector per FAQ question

    # ── Step 1: Build corpus from FAQ questions ──────────────
    def build(self, faq_list: list):
        self.documents  = [f["question"] for f in faq_list]
        self.token_docs = [tokenize(q) for q in self.documents]
        self._compute_idf()
        self.tfidf_vecs = [self._tfidf_vector(tokens)
                           for tokens in self.token_docs]
        print(f"  [TF-IDF] Indexed {len(self.documents)} FAQ documents.")
        print(f"  [TF-IDF] Vocabulary size: {len(self.idf_scores)} unique terms.\n")

    # ── Step 2: Compute IDF for each term ────────────────────
    def _compute_idf(self):
        N = len(self.token_docs)
        all_terms = set(t for doc in self.token_docs for t in doc)
        for term in all_terms:
            df = sum(1 for doc in self.token_docs if term in doc)
            # IDF = log(N / df) + 1  (smooth to avoid zero)
            self.idf_scores[term] = math.log(N / df) + 1

    # ── Step 3: Build TF-IDF vector for a token list ─────────
    def _tfidf_vector(self, tokens: list) -> dict:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        vector = {}
        for term, count in tf.items():
            tf_score  = count / total
            idf_score = self.idf_scores.get(term, 0)
            vector[term] = tf_score * idf_score
        return vector

    # ── Step 4: Cosine similarity between two vectors ────────
    def _cosine_similarity(self, vec_a: dict, vec_b: dict) -> float:
        common = set(vec_a.keys()) & set(vec_b.keys())
        if not common:
            return 0.0
        dot    = sum(vec_a[t] * vec_b[t] for t in common)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ── Step 5: Retrieve top-N matches for a query ───────────
    def retrieve(self, query: str, top_n: int = 3) -> list:
        query_tokens = tokenize(query)
        query_vec    = self._tfidf_vector(query_tokens)

        scores = []
        for idx, faq_vec in enumerate(self.tfidf_vecs):
            score = self._cosine_similarity(query_vec, faq_vec)
            scores.append((score, idx))

        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_n]

# ════════════════════════════════════════════════════════════
#  CHATBOT RESPONSE
# ════════════════════════════════════════════════════════════

THRESHOLD = 0.05   # minimum similarity score to accept a match

def get_response(query: str, engine: TFIDF, faq_list: list) -> dict:
    # Special intents
    text = query.lower().strip()
    if re.search(r"\b(hi|hello|hey|namaste|good morning|good evening)\b", text):
        return {
            "matched_question": "—",
            "answer": "Hello! Welcome to the SIT FAQ Bot. Ask me anything about "
                      "courses, fees, admission, hostel, library, placements, and more!",
            "score": 1.0,
            "top_matches": []
        }
    if re.search(r"\b(bye|goodbye|exit|quit|take care)\b", text):
        return {
            "matched_question": "—",
            "answer": "Goodbye! Best of luck with your journey at SIT!",
            "score": 1.0,
            "top_matches": []
        }
    if re.search(r"\b(thank|thanks|thank you|thx)\b", text):
        return {
            "matched_question": "—",
            "answer": "You're welcome! Feel free to ask anything else.",
            "score": 1.0,
            "top_matches": []
        }

    # TF-IDF retrieval
    results = engine.retrieve(query, top_n=3)
    best_score, best_idx = results[0]

    if best_score < THRESHOLD:
        return {
            "matched_question": "—",
            "answer": (
                "I couldn't find a relevant answer. Try asking about: "
                "courses, fees, admission, timing, location, hostel, library, "
                "placements, sports, canteen, transport, internet, or labs."
            ),
            "score": best_score,
            "top_matches": []
        }

    return {
        "matched_question": faq_list[best_idx]["question"],
        "answer":           faq_list[best_idx]["answer"],
        "score":            best_score,
        "top_matches": [
            {
                "rank":     rank + 1,
                "question": faq_list[idx]["question"],
                "score":    round(score, 4)
            }
            for rank, (score, idx) in enumerate(results)
        ]
    }

# ════════════════════════════════════════════════════════════
#  DEMO — Test queries
# ════════════════════════════════════════════════════════════

TEST_QUERIES = [
    "How do I apply and register for admission?",
    "Is there a gym or football ground on campus?",
    "What books and journals are in the library?",
    "Are there any research labs and equipment?",
    "What scholarship options do students have?",
]

def run_demo(engine: TFIDF, faq_list: list):
    divider = "─" * 68
    print("=" * 68)
    print("   TF-IDF FAQ RETRIEVAL — DEMO QUERIES")
    print("=" * 68)

    for query in TEST_QUERIES:
        result = get_response(query, engine, faq_list)
        print(f"\n  Query   : {query}")
        print(f"  Matched : {result['matched_question']}")
        print(f"  Score   : {result['score']:.4f}")
        print(f"  Answer  : {result['answer']}")
        print(divider)

# ════════════════════════════════════════════════════════════
#  INTERACTIVE CHAT
# ════════════════════════════════════════════════════════════

def chat(engine: TFIDF, faq_list: list):
    divider = "─" * 68
    print("\n" + "=" * 68)
    print("   INTERACTIVE MODE  —  type 'bye' to exit")
    print("=" * 68)

    while True:
        try:
            user_input = input("\n  You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Exiting. Goodbye!]")
            break

        if not user_input:
            continue

        result = get_response(user_input, engine, faq_list)

        print(f"\n  Matched FAQ  : {result['matched_question']}")
        print(f"  Similarity   : {result['score']:.4f}")
        print(f"  Bot          : {result['answer']}")

        if result["top_matches"]:
            print(f"\n  Top 3 matches:")
            for m in result["top_matches"]:
                print(f"    #{m['rank']} [{m['score']:.4f}] {m['question']}")
        print(divider)

        if re.search(r"\b(bye|goodbye|exit|quit)\b", user_input.lower()):
            break

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 68)
    print("   SIT FAQ RETRIEVAL CHATBOT  —  TF-IDF Engine")
    print("=" * 68 + "\n")

    engine = TFIDF()
    engine.build(FAQ_DB)

    run_demo(engine, FAQ_DB)
    chat(engine, FAQ_DB)
