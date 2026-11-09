from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

import os
import uuid
import logging

import func_lib
import file_handling
import prompts_lib
import ypagogi_flow

import uuid
import ypagogi_storage

ypagogi_storage.init_db()


load_dotenv()

app = Flask(__name__, template_folder="templates")

app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise ValueError("Δεν έχει οριστεί το FLASK_SECRET_KEY.")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

API_KEY = os.getenv("XENAKI_OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("Δεν βρέθηκε το OPENAI API KEY.")

os.makedirs(os.getenv("TEMP_FOLDER"), exist_ok=True)

rag_index = func_lib.initialize_rag_system(api_key=API_KEY)


@app.route('/', methods={'GET', 'POST'})
def index():
    return render_template('index.html')


@app.route("/ypagogi", methods=["GET", "POST"])
def ypagogi():
    session.pop("ypagogi_case_id", None)

    if request.method == "GET":
        session.pop("ypagogi_history", None)
        session.pop("ypagogi_data", None)
        session.pop("ypagogi_round", None)

        return render_template("ypagogi.html")

    case_text = (request.form.get("case_description") or "").strip()

    if len(case_text) < 20:
        flash("Παρακαλώ συμπληρώστε μια πιο αναλυτική περιγραφή.")
        return render_template("ypagogi.html"), 400

    history = [
        {
            "kind": "initial_case",
            "text": case_text
        }
    ]

    try:
        data = ypagogi_flow.ask_next_questions(
            history,
            rag_index,
            1
        )

        case_id = uuid.uuid4().hex

        ypagogi_storage.save_case(
            case_id,
            history,
            data,
            1
        )
        session["ypagogi_case_id"] = case_id


        if data["stage"] == "completed":
            return render_template(
                "ypagogi_result.html",
                report=data["report"]
            )

        return render_template(
            "ypagogi_dynamic.html",
            data=data,
            round_no=1
        )

    except Exception:
        app.logger.exception("Σφάλμα κατά την αρχική υπαγωγή")

        flash("Παρουσιάστηκε σφάλμα κατά την ανάλυση. Δοκιμάστε ξανά.")

        return render_template("ypagogi.html"), 500


@app.route("/ypagogi/questions", methods=["POST"])
def ypagogi_questions():
    case_id = session.get("ypagogi_case_id")
    case = ypagogi_storage.load_case(case_id)

    if not case:
        flash("Η υπόθεση δεν βρέθηκε. Ξεκινήστε νέα υπαγωγή.")
        return redirect(url_for("ypagogi"))

    history = case["history"]
    previous_data = case["data"]
    current_round = case["round_number"]

    if not history or not previous_data:
        return redirect(url_for("ypagogi"))

    if previous_data.get("stage") != "clarifications":
        return redirect(url_for("ypagogi"))

    try:
        answers = ypagogi_flow.validate_answers(
            previous_data["questions"],
            request.form
        )

        history.append({
            "kind": "answers",
            "round": current_round,
            "items": answers
        })

        next_round = current_round + 1

        data = ypagogi_flow.ask_next_questions(
            history,
            rag_index,
            next_round
        )

        # Περιορισμός των γύρων.
        # Μετά τον μέγιστο αριθμό ζητάμε ολοκλήρωση.
        if next_round >= ypagogi_flow.MAX_ROUNDS and data["stage"] == "clarifications":

            history.append({
                "kind": "system_note",
                "text": (
                    "Δεν επιτρέπονται άλλες ερωτήσεις. "
                    "Σύνταξε τώρα προκαταρκτική έκθεση με "
                    "ρητή αναφορά στα στοιχεία που λείπουν."
                )
            })

            data = ypagogi_flow.ask_next_questions(
                history,
                rag_index,
                next_round + 1
            )

        ypagogi_storage.save_case(
            case_id,
            history,
            data,
            next_round
        )

        if data["stage"] == "completed":
            return render_template(
                "ypagogi_result.html",
                report=data["report"]
            )

        return render_template(
            "ypagogi_dynamic.html",
            data=data,
            round_no=next_round
        )

    except ValueError as exc:
        flash(str(exc))

        return render_template(
            "ypagogi_dynamic.html",
            data=previous_data,
            round_no=current_round
        ), 400

    except Exception:
        app.logger.exception("Σφάλμα κατά τον γύρο διευκρινίσεων")

        return render_template(
            "ypagogi_error.html"
        ), 500

@app.route("/ypagogi/document", methods=["POST"])
def ypagogi_document():

    case_id = session.get("ypagogi_case_id")

    case = ypagogi_storage.load_case(case_id)

    if not case:
        app.logger.warning(
            "Δεν βρέθηκε υπόθεση για δημιουργία Word"
        )
        return (
            "Δεν βρέθηκαν τα δεδομένα της υπαγωγής. "
            "Παρακαλώ ξεκινήστε νέα υπόθεση.",
            404
        )

    data = case["data"]

    if data.get("stage") != "completed":
        return (
            "Η υπαγωγή δεν έχει ολοκληρωθεί.",
            400
        )

    report = data.get("report")

    if not isinstance(report, dict):
        return (
            "Δεν υπάρχει έγκυρη τελική έκθεση.",
            400
        )

    try:
        return file_handling.create_ypagogi(
            request,
            "ypagogi.docx",
            report
        )

    except Exception:
        app.logger.exception(
            "Αποτυχία δημιουργίας Word υπαγωγής"
        )

        return (
            "Παρουσιάστηκε σφάλμα κατά τη δημιουργία Word.",
            500
        )




@app.route('/exodiko', methods={'GET', 'POST'})
def exodiko():
    if request.method == 'GET':
        return render_template('exodiko.html')
    elif request.method == 'POST':
        case_text = request.form.get('case_description')  
        print("Received case description:", case_text)

        prompt = prompts_lib.exodiko_prompt(case_text)
        exodiko_data = func_lib.make_answer(
            case_text, prompt, rag_index
        )
        
        # Κλήση της κοινής συνάρτησης με το αντίστοιχο docx template
        return file_handling.create_exodiko(request, "exodiko.docx", exodiko_data)



# @app.route('/exodiko_misthosis', methods={'GET', 'POST'})
# def exodiko_misthosis():
#     if request.method == 'GET':
#         return render_template('exodiko_misthosis.html')
#     elif request.method == 'POST':
#         # Για δοκιμή ή πραγματική χρήση
#         # case_text = "DOKIMASTIKO KEIMENO GIA TESTING"
#         case_text = request.form.get('case_description')
#         print("Received case description:", case_text)  
        
#         # Κλήση της κοινής συνάρτησης με το αντίστοιχο docx template
#         return file_handling.handle_lease_agreement(request, "exodiko_misthotiriou.docx", case_text)



@app.route('/asfalistika', methods={'GET', 'POST'})
def asfalistika():
    if request.method == 'GET':
        return render_template('asfalistika.html')
    elif request.method == 'POST':        
        case_text = request.form.get('case_description')  
        print("Received case description:", case_text)  

        prompt = prompts_lib.asfalistika_prompt(case_text)
        asfalistika_data = func_lib.make_answer(
            case_text, prompt, rag_index
        )
        # Κλήση της κοινής συνάρτησης με το αντίστοιχο docx template
        return file_handling.create_asfalistika(request, "asfalistika.docx", asfalistika_data)




@app.route('/agogi', methods={'GET', 'POST'})
def agogi():
    if request.method == 'GET':
        return render_template('agogi.html')
    elif request.method == 'POST':        
        case_text = request.form.get('case_description')  
        print("Received case description:", case_text)  
        
        prompt = prompts_lib.agogi_prompt(case_text)
        agogi_data = func_lib.make_answer(
            case_text, prompt, rag_index
        )
        
        # Κλήση της κοινής συνάρτησης με το αντίστοιχο docx template
        return file_handling.create_agogi(request, "agogi.docx", agogi_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7654)