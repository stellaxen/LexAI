from dotenv import load_dotenv
from flask import Flask, render_template, request
import os

import file_handling  # Περιέχει πλέον και τη νέα συνάρτηση handle_document_generation

load_dotenv()

app = Flask(__name__, template_folder='templates')

API_KEY = os.getenv("XENAKI_OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Δεν βρέθηκε το OPENAI_API_KEY...")

os.makedirs(os.getenv("TEMP_FOLDER"), exist_ok=True)

@app.route('/', methods={'GET', 'POST'})
def index():
    return render_template('index.html')


@app.route('/ypagogi', methods={'GET', 'POST'})
def ypagogi():
    if request.method == 'GET':
        return render_template('ypagogi.html')
    elif request.method == 'POST':
        rest_prompt = """ΑΠΑΝΤΗΣΕ ΑΠΟΚΛΕΙΣΤΙΚΑ ΚΑΙ ΜΟΝΟ ΜΕ ΕΝΑ ΕΓΚΥΡΟ JSON..."""
        prompt_text = request.form.get('case_text') + rest_prompt
        
        # Υποθέτουμε ότι το rag_index είναι διαθέσιμο (ή το περνάς ανάλογα)
        case_text = file_handling.make_answer(prompt_text, rag_index) 
        
        # Κλήση της κοινής συνάρτησης
        return file_handling.handle_document_generation(request, "ypagogi.docx", case_text)


@app.route('/exodiko_misthosis', methods={'GET', 'POST'})
def exodiko_misthosis():
    if request.method == 'GET':
        return render_template('exodiko_misthosis.html')
    elif request.method == 'POST':
        # Για δοκιμή ή πραγματική χρήση
        case_text = "DOKIMASTIKO KEIMENO GIA TESTING"
        
        # Κλήση της κοινής συνάρτησης με το αντίστοιχο docx template
        return file_handling.handle_lease_agreement(request, "exodiko_misthotiriou.docx", case_text)


@app.route('/asfalistika')
def asfalistika():
    return render_template('asfalistika.html')

@app.route('/agogi')
def agogi():
    return render_template('agogi.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7654)