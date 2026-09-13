from dotenv import load_dotenv  # Εισαγωγή της βιβλιοθήκης για τη φόρτωση των μεταβλητών περιβάλλοντος από το αρχείο .env
from flask import Flask, render_template, request, send_file
import subprocess, tempfile
from datetime import datetime
import os

import func_lib  # Εισαγωγή της βιλιοθήκης my_lib.py που περιέχει δικες μου βοηθητικές συναρτήσεις
from models import Person  # Εισαγωγή του μοντέλου Person από το αρχείο models.py


# Φόρτωση των μεταβλητών περιβάλλοντος από το αρχείο .env
load_dotenv()


app = Flask(__name__, template_folder='templates')

# 2. Φόρτωση του API key αποκλειστικά από τις μεταβλητές περιβάλλοντος
API_KEY = os.getenv("XENAKI_OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("Δεν βρέθηκε το OPENAI_API_KEY. Βεβαιώσου ότι υπάρχει το αρχείο .env με τη σωστή μεταβλητή.")

rag_index = func_lib.initialize_rag_system(data_dir="./legal_docs", api_key=API_KEY)

# Δημιουργία φακέλου temp αν δεν υπάρχει
os.makedirs( os.getenv("TEMP_FOLDER"), exist_ok=True)


@app.route('/', methods={'GET', 'POST'})
def index():
    return render_template('index.html')


@app.route('/ypagogi', methods={'GET', 'POST'})
def ypagogi():
    if request.method == 'GET':
        return render_template('ypagogi.html')
    elif request.method == 'POST':
        rest_prompt = """ΑΠΑΝΤΗΣΕ ΑΠΟΚΛΕΙΣΤΙΚΑ ΚΑΙ ΜΟΝΟ ΜΕ ΕΝΑ ΕΓΚΥΡΟ JSON. Μην γράψεις καμία άλλη λέξη, πρόταση, εισαγωγή ή επεξήγηση πριν ή μετά το JSON. Μη χρησιμοποιήσεις markdown blocks (όπως ```json). 
        Η δομή του JSON πρέπει να είναι ακριβώς η εξής:
        {
        "Αριθμός_Άρθρου": {
            "κείμενο": "ολόκληρο το κείμενο του άρθρου",
            "αρχείο": "όνομα_αρχείου.txt"
        }
        }
        """

        caller = Person(
            name=request.form.get('caller_name'),
            surname=request.form.get('caller_surname'),
            fathers_name=request.form.get('caller_fathers_name'),
            address=request.form.get('caller_address'),
            tax_id=request.form.get('caller_tax_id')
        )
        calling = Person(
            name=request.form.get('calling_name'),
            surname=request.form.get('calling_surname'),
            fathers_name=request.form.get('calling_fathers_name'),
            address=request.form.get('calling_address'),
            tax_id=request.form.get('calling_tax_id')
        )

        prompt_text = request.form.get('case_text') + rest_prompt
        case_text = func_lib.make_answer(prompt_text, rag_index)
        
        try:
            # 1. Δημιουργία του αρχείου Word
            docx_path = func_lib.generate_doc("ypagogi.docx", case_text, caller, calling)  
            output_dir = "output_pdfs"  
            os.makedirs(output_dir, exist_ok=True)

            # 2. Μετατροπή σε PDF μέσω LibreOffice
            with tempfile.TemporaryDirectory() as libreoffice_profile:
                profile_url = f"file://{libreoffice_profile}"
                cmd = [
                    '/usr/bin/libreoffice', 
                    f'-env:UserInstallation={profile_url}',
                    '--headless', 
                    '--convert-to', 'pdf',
                    '--outdir', output_dir,
                    docx_path
                ]
                
                print(f"🔄 Converting to PDF via LibreOffice: {docx_path}")
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

            # Εκτύπωση των logs του LibreOffice για debugging
            print(f"LibreOffice STDOUT: {result.stdout}")
            print(f"LibreOffice STDERR: {result.stderr}")

            base_name = os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
            generated_pdf_path = os.path.join(output_dir, base_name)

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_pdf_name = f"{timestamp}.pdf"
            final_pdf_path = os.path.join(output_dir, new_pdf_name)

            if os.path.exists(generated_pdf_path):
                os.rename(generated_pdf_path, final_pdf_path)
                print(f"✅ PDF Created and Renamed: {final_pdf_path}")
                
                # 3. Απευθείας αποστολή του PDF για λήψη στον browser
                return send_file(
                    final_pdf_path, 
                    as_attachment=True, 
                    download_name="document.pdf"
                )
            else:
                print("❌ PDF creation failed (file not found in output_dir).")
                return f"PDF creation failed. LibreOffice stderr: {result.stderr}", 500
                
        except Exception as e:
            print(f"⚠️ PDF Conversion Exception: {e}")
            return f"Error: {e}", 500


@app.route('/exodiko')
def exodiko():
    return render_template('exodiko.html')


@app.route('/asfalistika')
def asfalistika():
    return render_template('asfalistika.html')


@app.route('/agogi')
def agogi():
    return render_template('agogi.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7654)
