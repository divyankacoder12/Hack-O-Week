# ============================================================
#  Intent Classification for Student Queries
#  Symbiosis Institute of Technology, Nagpur
#
#  7 Intents:
#    1. admissions     2. exams        3. timetable
#    4. hostel         5. scholarships 6. fees
#    7. placements
#
#  Classifier: Multinomial Naive Bayes (built from scratch)
#  No sklearn / NLTK required — pure Python only
# ============================================================

import re
import math
from collections import defaultdict, Counter

# ════════════════════════════════════════════════════════════
#  TRAINING DATA
#  (query, intent) pairs — used to train the classifier
# ════════════════════════════════════════════════════════════

TRAINING_DATA = [

    # ── ADMISSIONS ──────────────────────────────────────────
    ("How do I apply for admission to SIT?",                     "admissions"),
    ("What is the admission process for BTech?",                 "admissions"),
    ("When does the enrollment process start?",                  "admissions"),
    ("What are the eligibility criteria for admission?",         "admissions"),
    ("How can I register for the entrance exam?",                "admissions"),
    ("What is the application deadline for SIT?",                "admissions"),
    ("Can I apply online for admissions?",                       "admissions"),
    ("What documents are needed for enrollment?",                "admissions"),
    ("Is there a merit list for admission selection?",           "admissions"),
    ("What is the SET exam for Symbiosis admissions?",           "admissions"),
    ("How many seats are available in computer science?",        "admissions"),
    ("What is the cutoff rank for admission?",                   "admissions"),
    ("Tell me about the admission procedure at SIT",             "admissions"),
    ("I want to join SIT how do I start the process?",          "admissions"),
    ("What is the last date to submit the admission form?",      "admissions"),

    # ── EXAMS ───────────────────────────────────────────────
    ("When are the semester exams scheduled?",                   "exams"),
    ("What is the exam pattern for BTech subjects?",             "exams"),
    ("How many papers are there in the final examination?",      "exams"),
    ("What is the passing marks for university exams?",          "exams"),
    ("Can I apply for revaluation of my answer sheet?",          "exams"),
    ("When will the exam results be declared?",                  "exams"),
    ("How is the internal assessment graded?",                   "exams"),
    ("What is the grading system for semester exams?",           "exams"),
    ("Are exams conducted online or offline?",                   "exams"),
    ("What happens if I fail in a subject?",                     "exams"),
    ("How do I get my mark sheet after exams?",                  "exams"),
    ("Is there a backlog exam for failed students?",             "exams"),
    ("When does the practical examination begin?",               "exams"),
    ("What is the minimum attendance required to appear for exam?","exams"),
    ("How do I check my exam results online?",                   "exams"),

    # ── TIMETABLE ───────────────────────────────────────────
    ("Where can I find the class timetable for this semester?",  "timetable"),
    ("What time do lectures start in the morning?",              "timetable"),
    ("Is the schedule for semester 3 available?",                "timetable"),
    ("Which day do we have no lectures?",                        "timetable"),
    ("What is the timetable for the lab sessions?",              "timetable"),
    ("How many hours of class are there per day?",               "timetable"),
    ("Can I get the weekly schedule for all subjects?",          "timetable"),
    ("When is the break time between classes?",                  "timetable"),
    ("Is Monday a holiday or is there a class?",                 "timetable"),
    ("What is the routine for first year BTech students?",       "timetable"),
    ("Tell me about the daily schedule at college",              "timetable"),
    ("At what time does the last lecture end?",                  "timetable"),
    ("Is there a revised timetable for this week?",              "timetable"),
    ("How many subjects are scheduled per week?",                "timetable"),
    ("What time does the college open in the morning?",          "timetable"),

    # ── HOSTEL ──────────────────────────────────────────────
    ("Is hostel accommodation available for students?",          "hostel"),
    ("What are the hostel facilities at SIT?",                   "hostel"),
    ("Is the hostel safe and secure for girls?",                 "hostel"),
    ("What is the monthly rent for the hostel room?",            "hostel"),
    ("Is food included in the hostel charges?",                  "hostel"),
    ("Are boys and girls hostels separate?",                     "hostel"),
    ("Can first year students get a hostel room?",               "hostel"),
    ("What is the hostel curfew timing?",                        "hostel"),
    ("Is Wi-Fi available in the hostel rooms?",                  "hostel"),
    ("How do I apply for hostel accommodation?",                 "hostel"),
    ("What is the process to get a hostel room allotted?",       "hostel"),
    ("Are there single or double occupancy hostel rooms?",       "hostel"),
    ("Is the hostel inside the campus?",                         "hostel"),
    ("What amenities are available in the student dormitory?",   "hostel"),
    ("Can I stay in the hostel during holidays?",                "hostel"),

    # ── SCHOLARSHIPS ────────────────────────────────────────
    ("Are there any scholarships available for BTech students?", "scholarships"),
    ("How do I apply for a merit scholarship?",                  "scholarships"),
    ("What is the eligibility for financial aid?",               "scholarships"),
    ("Is there a scholarship for economically weaker students?", "scholarships"),
    ("How much scholarship amount is given to toppers?",         "scholarships"),
    ("Does SIT offer any fee waiver programs?",                  "scholarships"),
    ("When is the last date to apply for scholarship?",          "scholarships"),
    ("What documents are required for scholarship application?", "scholarships"),
    ("Is there a government scholarship for engineering students?","scholarships"),
    ("Can I get a scholarship renewal every year?",              "scholarships"),
    ("What is the selection process for financial assistance?",  "scholarships"),
    ("Are there sports scholarships available at SIT?",          "scholarships"),
    ("How is the scholarship amount disbursed?",                 "scholarships"),
    ("Is there a need-based scholarship program?",               "scholarships"),
    ("Can I apply for multiple scholarships at the same time?",  "scholarships"),

    # ── FEES ────────────────────────────────────────────────
    ("What is the fee structure for BTech at SIT?",              "fees"),
    ("How much tuition do I need to pay per semester?",          "fees"),
    ("What are the total charges for four years of engineering?","fees"),
    ("Is the fee payment done online or offline?",               "fees"),
    ("What is the last date to pay the semester fees?",          "fees"),
    ("Are there any late payment penalties for fees?",           "fees"),
    ("Can I pay fees in installments?",                          "fees"),
    ("What is the hostel fee per year?",                         "fees"),
    ("Is there a separate exam fee I need to pay?",              "fees"),
    ("What payment methods are accepted for fee submission?",    "fees"),
    ("How much is the library and lab fee?",                     "fees"),
    ("Are there any hidden charges in the college fee?",         "fees"),
    ("What is the fee refund policy if I withdraw?",             "fees"),
    ("Do I need to pay registration fees every year?",           "fees"),
    ("How do I get a fee receipt after payment?",                "fees"),

    # ── PLACEMENTS ──────────────────────────────────────────
    ("What companies come to SIT for campus recruitment?",       "placements"),
    ("What is the average salary package offered to students?",  "placements"),
    ("How does the placement process work at SIT?",              "placements"),
    ("When does the campus placement season start?",             "placements"),
    ("Are there off-campus placement opportunities too?",        "placements"),
    ("How many students got placed last year?",                  "placements"),
    ("Which IT companies visit SIT for hiring?",                 "placements"),
    ("Is there a dedicated training and placement cell?",        "placements"),
    ("How do I register for campus placement drives?",           "placements"),
    ("What skills are companies looking for in hiring?",         "placements"),
    ("Are internships offered through the placement cell?",      "placements"),
    ("What is the highest package offered at SIT?",              "placements"),
    ("Does SIT have tie-ups with any MNCs for recruitment?",     "placements"),
    ("How should I prepare for campus placement interviews?",    "placements"),
    ("Can final year students appear for multiple companies?",   "placements"),
]

# ════════════════════════════════════════════════════════════
#  INTENT RESPONSES
# ════════════════════════════════════════════════════════════

INTENT_RESPONSES = {
    "admissions": (
        "For admissions at SIT, candidates must qualify the SET (Symbiosis "
        "Entrance Test) and clear a personal interaction round. Applications "
        "open online at symbiosis.ac.in. Check eligibility criteria and "
        "deadlines on the official portal."
    ),
    "exams": (
        "SIT follows Symbiosis International University's examination system "
        "with internal assessments, mid-semester, and end-semester exams. "
        "Results are declared on the SIU portal. Minimum attendance of 75% "
        "is required to sit for exams."
    ),
    "timetable": (
        "Class timetables are published on the SIT student portal at the "
        "start of each semester. Lectures run from 9:00 AM to 5:00 PM, "
        "Monday to Friday. Lab sessions and electives may have separate "
        "time slots — check with your department."
    ),
    "hostel": (
        "SIT provides separate hostel facilities for male and female students "
        "with amenities including Wi-Fi, mess, and security. Rooms are "
        "available on a first-come-first-served basis. Apply through the "
        "admissions portal after confirmation of your seat."
    ),
    "scholarships": (
        "SIT and Symbiosis International University offer merit-based and "
        "need-based scholarships. Government scholarships for SC/ST/OBC "
        "students are also applicable. Applications open during admissions — "
        "visit symbiosis.ac.in for eligibility and required documents."
    ),
    "fees": (
        "The fee structure at SIT varies by program and category. Fees can "
        "be paid online via the student portal. Installment options may be "
        "available — contact the accounts office. Visit symbiosis.ac.in for "
        "the complete and updated fee structure."
    ),
    "placements": (
        "SIT's Training and Placement Cell facilitates campus drives by "
        "top IT and engineering companies. Students can register on the "
        "T&P portal. The placement season typically begins in the final year. "
        "Average packages and company lists are available on the SIT website."
    ),
}

# ════════════════════════════════════════════════════════════
#  PREPROCESSING
# ════════════════════════════════════════════════════════════

STOPWORDS = {
    "a","an","the","is","it","in","on","at","to","for","of","and","or",
    "but","not","are","was","were","be","been","have","has","do","does",
    "did","will","would","could","should","can","i","me","my","we","our",
    "you","your","he","she","they","them","this","that","these","those",
    "what","which","who","how","when","where","with","from","by","about",
    "into","so","if","just","get","want","need","tell","let","know","hi",
    "hello","hey","please","some","any","more","very","much","also","than",
    "then","up","out","its","their","there","here","being","having","am",
    "us","all","no","yes","one","two","three","each","every","many","few"
}

def tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split()
              if t not in STOPWORDS and len(t) > 1]
    return tokens

# ════════════════════════════════════════════════════════════
#  NAIVE BAYES CLASSIFIER (built from scratch)
#  Model: P(intent|query) ∝ P(intent) × ∏ P(word|intent)
# ════════════════════════════════════════════════════════════

class NaiveBayesClassifier:

    def __init__(self, smoothing: float = 1.0):
        self.smoothing       = smoothing   # Laplace smoothing alpha
        self.class_priors    = {}          # log P(intent)
        self.word_log_probs  = {}          # log P(word | intent)
        self.vocab           = set()
        self.classes         = []

    # ── Training ─────────────────────────────────────────────
    def train(self, data: list):
        """
        data: list of (text, label) tuples
        Computes log-prior and log-likelihood for each intent.
        """
        # Group documents by class
        class_docs = defaultdict(list)
        for text, label in data:
            tokens = tokenize(text)
            class_docs[label].extend(tokens)
            self.vocab.update(tokens)

        self.classes  = list(class_docs.keys())
        total_docs    = len(data)
        label_counts  = Counter(label for _, label in data)
        vocab_size    = len(self.vocab)

        for cls in self.classes:
            # Log prior: log( count(cls) / total )
            self.class_priors[cls] = math.log(label_counts[cls] / total_docs)

            # Word counts in this class
            word_counts = Counter(class_docs[cls])
            total_words = sum(word_counts.values())

            # Log likelihood with Laplace smoothing:
            # log P(w|c) = log( (count(w,c) + α) / (total_words_c + α×|V|) )
            self.word_log_probs[cls] = {}
            denom = total_words + self.smoothing * vocab_size

            for word in self.vocab:
                count = word_counts.get(word, 0)
                self.word_log_probs[cls][word] = math.log(
                    (count + self.smoothing) / denom
                )

        print(f"  [NB] Trained on {total_docs} samples")
        print(f"  [NB] {len(self.classes)} intents: {', '.join(sorted(self.classes))}")
        print(f"  [NB] Vocabulary size: {vocab_size} unique terms\n")

    # ── Prediction ───────────────────────────────────────────
    def predict(self, text: str) -> list:
        """
        Returns sorted list of (intent, score) — highest score = best match.
        Score is the log-posterior (not normalized probability).
        """
        tokens = tokenize(text)
        scores = {}

        for cls in self.classes:
            # Start with log prior
            score = self.class_priors[cls]
            # Add log likelihoods for each token
            for token in tokens:
                if token in self.word_log_probs[cls]:
                    score += self.word_log_probs[cls][token]
                # Unknown words: use smoothed unseen probability
                else:
                    vocab_size  = len(self.vocab)
                    total_words = sum(
                        1 for _ in self.word_log_probs[cls]
                    )
                    score += math.log(
                        self.smoothing / (total_words + self.smoothing * vocab_size)
                    )
            scores[cls] = score

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

    # ── Softmax confidence ───────────────────────────────────
    def confidence(self, ranked: list) -> list:
        """Convert log-scores to percentage confidence via softmax."""
        scores  = [s for _, s in ranked]
        # Shift for numerical stability
        shifted = [s - max(scores) for s in scores]
        exps    = [math.exp(s) for s in shifted]
        total   = sum(exps)
        return [(cls, round(e / total * 100, 2))
                for (cls, _), e in zip(ranked, exps)]

    # ── Evaluation ───────────────────────────────────────────
    def evaluate(self, test_data: list) -> dict:
        """Run accuracy evaluation on a test set."""
        correct = 0
        errors  = []
        for text, true_label in test_data:
            ranked = self.predict(text)
            pred   = ranked[0][0]
            if pred == true_label:
                correct += 1
            else:
                errors.append((text, true_label, pred))
        accuracy = correct / len(test_data) * 100
        return {"accuracy": accuracy, "errors": errors,
                "total": len(test_data), "correct": correct}

# ════════════════════════════════════════════════════════════
#  CHATBOT RESPONSE ENGINE
# ════════════════════════════════════════════════════════════

def get_response(query: str, clf: NaiveBayesClassifier) -> dict:
    text = query.lower().strip()

    # Special intents
    if re.search(r"\b(hi|hello|hey|namaste|good morning)\b", text):
        return {"intent": "greeting", "confidence": 100.0,
                "answer": "Hello! I'm the SIT Intent Bot. Ask me about "
                          "admissions, exams, timetable, hostel, scholarships, "
                          "fees, or placements!", "all_scores": []}

    if re.search(r"\b(bye|goodbye|exit|quit)\b", text):
        return {"intent": "goodbye", "confidence": 100.0,
                "answer": "Goodbye! Best of luck at SIT!", "all_scores": []}

    if re.search(r"\b(thank|thanks|thx|thank you)\b", text):
        return {"intent": "thanks", "confidence": 100.0,
                "answer": "You're welcome! Ask me anything else.",
                "all_scores": []}

    # Classify
    ranked     = clf.predict(query)
    confidence = clf.confidence(ranked)
    top_intent, top_conf = confidence[0]

    answer = INTENT_RESPONSES.get(top_intent,
        "Sorry, I couldn't classify that query. Please try rephrasing.")

    return {
        "intent":     top_intent,
        "confidence": top_conf,
        "answer":     answer,
        "all_scores": confidence
    }

# ════════════════════════════════════════════════════════════
#  DEMO TEST QUERIES
# ════════════════════════════════════════════════════════════

TEST_QUERIES = [
    ("How do I apply for BTech admission at SIT?",        "admissions"),
    ("What is the exam schedule for semester 5?",          "exams"),
    ("Can you share the class timetable for this week?",   "timetable"),
    ("Is there a girls hostel available on campus?",       "hostel"),
    ("Am I eligible for a merit scholarship?",             "scholarships"),
    ("What is the tuition fee for first year BTech?",      "fees"),
    ("Which companies hire from SIT campus?",              "placements"),
    ("When is the last date to submit the admission form?","admissions"),
    ("What happens if I fail in an exam?",                 "exams"),
    ("How much is the monthly hostel rent?",               "hostel"),
    ("Is there a fee waiver for toppers?",                 "scholarships"),
    ("Can I pay fees in monthly installments?",            "fees"),
    ("What is the average salary in campus placements?",   "placements"),
]

def run_demo(clf: NaiveBayesClassifier):
    divider = "─" * 70
    print("=" * 70)
    print("   INTENT CLASSIFICATION — DEMO TEST QUERIES")
    print("=" * 70)
    print(f"\n  {'#':<3} {'QUERY':<46} {'PREDICTED':<14} {'CONF%':<8} {'OK?'}")
    print(divider)

    correct = 0
    for i, (query, expected) in enumerate(TEST_QUERIES, 1):
        result = get_response(query, clf)
        pred   = result["intent"]
        conf   = result["confidence"]
        mark   = "✓" if pred == expected else "✗"
        if pred == expected:
            correct += 1
        q_short = query[:44] + ".." if len(query) > 44 else query
        print(f"  {i:<3} {q_short:<46} {pred:<14} {conf:<8} {mark}")

    print(divider)
    acc = correct / len(TEST_QUERIES) * 100
    print(f"\n  Accuracy on demo queries: {correct}/{len(TEST_QUERIES)} = {acc:.1f}%\n")

# ════════════════════════════════════════════════════════════
#  FULL TRAINING EVALUATION (leave-one-out style)
# ════════════════════════════════════════════════════════════

def run_evaluation(clf: NaiveBayesClassifier):
    result = clf.evaluate(TRAINING_DATA)
    print(f"  Training-set accuracy : {result['correct']}/{result['total']}"
          f" = {result['accuracy']:.1f}%")
    if result["errors"]:
        print(f"\n  Misclassified queries ({len(result['errors'])}):")
        for text, true, pred in result["errors"]:
            print(f"    ✗ [{true}→{pred}] {text}")
    print()

# ════════════════════════════════════════════════════════════
#  INTERACTIVE CHAT
# ════════════════════════════════════════════════════════════

def chat(clf: NaiveBayesClassifier):
    divider = "─" * 70
    print("=" * 70)
    print("   INTERACTIVE MODE  —  type 'bye' to exit")
    print("=" * 70)

    while True:
        try:
            user_input = input("\n  You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Exiting.]")
            break

        if not user_input:
            continue

        result = get_response(user_input, clf)

        print(f"\n  Intent     : {result['intent'].upper()}"
              f"  ({result['confidence']}% confidence)")

        if result["all_scores"]:
            scores_str = "  │  ".join(
                f"{cls}: {conf}%" for cls, conf in result["all_scores"]
            )
            print(f"  All scores : {scores_str}")

        print(f"  Bot        : {result['answer']}")
        print(divider)

        if result["intent"] == "goodbye":
            break

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("   STUDENT QUERY INTENT CLASSIFIER")
    print("   Algorithm: Multinomial Naive Bayes (from scratch)")
    print("   Intents  : admissions | exams | timetable | hostel")
    print("              scholarships | fees | placements")
    print("=" * 70 + "\n")

    clf = NaiveBayesClassifier(smoothing=1.0)
    clf.train(TRAINING_DATA)

    run_evaluation(clf)
    run_demo(clf)
    chat(clf)