
import json
import re

import func_lib


MAX_ROUNDS = 8

ALLOWED_TYPES = {
    "text",
    "textarea",
    "date",
    "number",
    "select",
    "radio",
}

REPORT_FIELDS = [
    "historic_summary",
    "legal_substantiation",
    "legal_base",
    "aitoumena_zitimata",
    "prothesmia_symmorfosis",
]


def build_prompt(history, round_number):
    history_json = json.dumps(history, ensure_ascii=False, indent=2)

    return f"""
Είσαι εξειδικευμένος νομικός βοηθός για την προκαταρκτική
νομική υπαγωγή πραγματικών περιστατικών στο ελληνικό δίκαιο.

Σκοπός σου είναι:
1. Να κατανοήσεις τα πραγματικά περιστατικά.
2. Να εντοπίσεις τις πιθανές νομικές βάσεις.
3. Να εντοπίσεις ποια κρίσιμα στοιχεία λείπουν.
4. Να υποβάλεις στοχευμένες ερωτήσεις.
5. Να ολοκληρώσεις την προκαταρκτική έκθεση όταν υπάρχουν
   επαρκή στοιχεία.

ΧΡΗΣΙΜΟΠΟΙΗΣΕ ΤΑ ΠΑΡΕΧΟΜΕΝΑ ΑΠΟΣΠΑΣΜΑΤΑ RAG.
Μην επινοείς άρθρα, νόμους, αποφάσεις ή πραγματικά περιστατικά.
Αν δεν μπορείς να επιβεβαιώσεις μία διάταξη από το RAG,
δήλωσε ρητά ότι χρειάζεται περαιτέρω έλεγχος.

ΙΣΤΟΡΙΚΟ ΣΥΝΕΝΤΕΥΞΗΣ:

{history_json}

Τρέχων γύρος: {round_number}

Απάντησε ΑΠΟΚΛΕΙΣΤΙΚΑ με έγκυρο JSON.

Η δομή πρέπει να είναι:

{{
  "stage": "clarifications",
  "summary": "Σύντομη περιγραφή όσων έχουν γίνει κατανοητά",
  "questions": [
    {{
      "id": "event_date",
      "type": "date",
      "label": "Πότε συνέβη το περιστατικό;",
      "required": true,
      "help": "Αναφέρετε την ακριβή ημερομηνία, αν είναι γνωστή."
    }},
    {{
      "id": "evidence",
      "type": "textarea",
      "label": "Υπάρχουν αποδεικτικά στοιχεία;",
      "required": false,
      "help": "Για παράδειγμα, έγγραφα, μηνύματα ή φωτογραφίες."
    }},
    {{
      "id": "relationship",
      "type": "select",
      "label": "Ποια είναι η σχέση σας με το άλλο μέρος;",
      "required": true,
      "options": [
        "Συμβατική σχέση",
        "Εργασιακή σχέση",
        "Ιδιοκτησιακή σχέση",
        "Άλλη σχέση"
      ]
    }}
  ],
  "report": null
}}

ΚΑΝΟΝΕΣ:

- Αν λείπουν κρίσιμα στοιχεία, χρησιμοποίησε:
  "stage": "clarifications".

- Στην περίπτωση αυτή επέστρεψε 1 έως 5 συγκεκριμένες ερωτήσεις.

- Μην επαναλαμβάνεις ερωτήσεις που έχουν ήδη απαντηθεί.

- Οι ερωτήσεις πρέπει να σχετίζονται με πραγματικές
  προϋποθέσεις νομικής υπαγωγής.

- Για select και radio είναι υποχρεωτικό το πεδίο options.

- Οι επιτρεπόμενοι τύποι είναι:
  text, textarea, date, number, select, radio.

- Όταν τα στοιχεία είναι επαρκή, χρησιμοποίησε:
  "stage": "completed",
  "questions": [].

- Στην ολοκλήρωση συμπλήρωσε το report με τα παρακάτω πεδία:

{{
  "historic_summary": "Αναλυτικό και ουδέτερο ιστορικό",
  "legal_substantiation": "Νομική τεκμηρίωση και ανάλυση",
  "legal_base": "Νομικές διατάξεις και άρθρα",
  "aitoumena_zitimata": "Αξιώσεις και επιδιωκόμενα αποτελέσματα",
  "prothesmia_symmorfosis": "Προθεσμίες και κρίσιμα χρονικά στοιχεία"
}}

Η έκθεση πρέπει να διαχωρίζει:
- πραγματικά περιστατικά,
- ισχυρισμούς,
- αποδεικτικά στοιχεία,
- παραδοχές,
- άγνωστα στοιχεία,
- νομικές εκτιμήσεις.

Μην παρουσιάζεις την ανάλυση ως βέβαιη δικαστική έκβαση.
Αν λείπουν στοιχεία, δήλωσε τις επιφυλάξεις.
"""


def validate_llm_response(data):
    if not isinstance(data, dict):
        raise ValueError("Η απάντηση του μοντέλου δεν είναι JSON αντικείμενο.")

    stage = data.get("stage")

    if stage not in ("clarifications", "completed"):
        raise ValueError("Μη έγκυρη κατάσταση υπαγωγής.")

    questions = data.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError("Το questions πρέπει να είναι λίστα.")

    seen_ids = set()

    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("Μη έγκυρη ερώτηση.")

        question_id = question.get("id")
        label = question.get("label")
        question_type = question.get("type", "text")

        if not question_id or not label:
            raise ValueError("Κάθε ερώτηση πρέπει να έχει id και label.")

        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,49}", question_id):
            raise ValueError("Μη έγκυρο αναγνωριστικό ερώτησης.")

        if question_id in seen_ids:
            raise ValueError("Υπάρχουν διπλά αναγνωριστικά ερωτήσεων.")

        seen_ids.add(question_id)

        if question_type not in ALLOWED_TYPES:
            raise ValueError("Μη υποστηριζόμενος τύπος ερώτησης.")

        if question_type in ("select", "radio"):
            options = question.get("options")

            if not isinstance(options, list) or not options:
                raise ValueError(
                    "Οι ερωτήσεις επιλογής πρέπει να έχουν options."
                )

            if not all(isinstance(option, str) for option in options):
                raise ValueError("Μη έγκυρες επιλογές.")

    if stage == "clarifications" and not questions:
        raise ValueError(
            "Το μοντέλο ζήτησε διευκρινίσεις χωρίς να δώσει ερωτήσεις."
        )

    if stage == "completed":
        report = data.get("report")

        if not isinstance(report, dict):
            raise ValueError("Δεν επιστράφηκε τελική έκθεση.")

        for field in REPORT_FIELDS:
            report.setdefault(
                field,
                "Δεν προκύπτει από τα διαθέσιμα στοιχεία."
            )

    return data


def ask_next_questions(history, rag_index, round_number):
    prompt = build_prompt(history, round_number)

    # Χρησιμοποιούμε το υπάρχον RAG της εφαρμογής.
    case_text = json.dumps(history, ensure_ascii=False)

    response = func_lib.make_answer(
        case_text,
        prompt,
        rag_index
    )

    return validate_llm_response(response)


def validate_answers(questions, form):
    answers = []

    for question in questions:
        question_id = question["id"]
        label = question["label"]
        question_type = question.get("type", "text")
        required = question.get("required", False)

        value = (form.get(question_id) or "").strip()

        if required and not value:
            raise ValueError(
                f"Απαιτείται απάντηση στην ερώτηση: {label}"
            )

        if question_type in ("select", "radio") and value:
            if value not in question.get("options", []):
                raise ValueError(
                    f"Μη επιτρεπόμενη επιλογή στην ερώτηση: {label}"
                )

        answers.append({
            "question_id": question_id,
            "question": label,
            "answer": value if value else "Δεν γνωρίζω / Δεν προκύπτει"
        })

    return answers
