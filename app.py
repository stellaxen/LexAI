import datetime
import os
import unicodedata
from dotenv import load_dotenv  # 1. Εισαγωγή της βιβλιοθήκης

from models import Person  # 2. Εισαγωγή του μοντέλου Person από το αρχείο models.py

# Φόρτωση των μεταβλητών από το αρχείο .env
load_dotenv()

from flask import Flask, render_template, request, send_file
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import json

import subprocess 
from datetime import datetime

from docxtpl import DocxTemplate
import tempfile
import zipfile, shutil

def initialize_rag_system(data_dir="./data", api_key=None):
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    Settings.llm = OpenAI(
        model="gpt-4o", 
        temperature=0,
        additional_kwargs={"response_format": {"type": "json_object"}}
    )
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    
    print("[INFO] Loading legal documents...")
    documents = SimpleDirectoryReader(data_dir).load_data()
    
    print("[INFO] Building vector index...")
    index = VectorStoreIndex.from_documents(documents)
    
    return index

def beautify_answer(raw_string):
    cleaned = raw_string.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        data = json.loads(cleaned.strip())
        if isinstance(data, dict):
            answer = ""
            for key, value in data.items():
                print(f"Άρθρο: {key}")
                print(f"Κείμενο: {value['κείμενο']}")
                print(f"Αρχείο: {value['αρχείο']}")
                print("-" * 40)
                # Χρησιμοποιούμε απλές αλλαγές γραμμής αντί για HTML tags                
                answer += f"\n\n{key}\n{value['κείμενο']}\nΑρχείο: {value['αρχείο']}\n" 
        else:
            answer = "Δε βρέθηκε υπαγωγή για την περίπτωση σας."
            
    except json.JSONDecodeError:        
        answer = "Δε βρέθηκε υπαγωγή για την περίπτωση σας."
    
    return answer

def make_answer(case_text, res):    
    query_engine = res.as_query_engine(
        similarity_top_k=10,
        response_mode="compact"
    )
    
    response = query_engine.query(case_text)
    print("\n--- Απάντηση RAG ---")
    print(response)

    response = str(response)
    return beautify_answer(response)


app = Flask(__name__, template_folder='templates')

# 2. Φόρτωση του API key αποκλειστικά από τις μεταβλητές περιβάλλοντος
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("Δεν βρέθηκε το OPENAI_API_KEY. Βεβαιώσου ότι υπάρχει το αρχείο .env με τη σωστή μεταβλητή.")

rag_index = initialize_rag_system(data_dir="./legal_docs", api_key=API_KEY)

# Δημιουργία φακέλου temp αν δεν υπάρχει
TEMP_FOLDER = "temp"
os.makedirs(TEMP_FOLDER, exist_ok=True)


@app.route('/', methods={'GET', 'POST'})
def index():
    if request.method == 'GET':
        return render_template('index.html')
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
        case_text = make_answer(prompt_text, rag_index)
        
        try:
            # 1. Δημιουργία του αρχείου Word
            docx_path = generate_doc("ypagogi.docx", case_text, caller, calling)  
            output_dir = "output_pdfs"  
            os.makedirs(output_dir, exist_ok=True)

            # 2. Μετατροπή σε PDF μέσω LibreOffice
            with tempfile.TemporaryDirectory() as libreoffice_profile:
                profile_url = f"file://{libreoffice_profile}"
                cmd = [
                    'libreoffice', 
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

def remove_accents(input_str):
    """Αφαιρεί τους τόνους από μια ελληνική λέξη."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def guess_greek_gender(name):
    if not name:
        return "Του/Της"
        
    # 1. Μετατροπή σε πεζά
    name = name.strip().lower()
    
    # 2. Αντικατάσταση τυχόν κεφαλαίου 'Σ' ή μεσαίου 'σ' στο τέλος σε τελικό 'ς' 
    # (για να ταιριάζουν σωστά οι καταλήξεις)
    if name.endswith('σ') or name.endswith('Σ'):
        name = name[:-1] + 'ς'
        
    # 3. Αφαίρεση τόνων (π.χ. 'ά' -> 'α', 'ή' -> 'η')
    name_no_accent = remove_accents(name)
    
    # Συνήθεις γυναικείες καταλήξεις (χωρίς τόνους)
    female_endings = ('η', 'α', 'ου', 'ω')
    # Συνήθεις αντρικές καταλήξεις (χωρίς τόνους)
    male_endings = ('ης', 'ας', 'ος', 'ες')
    
    # Έλεγχος με βάση τις καταλήξεις χωρίς τόνους
    if name_no_accent.endswith(male_endings):
        return "Του"
    elif name_no_accent.endswith(female_endings):
        return "Της"
    else:
        return "Του/Της"

def to_genitive_first_name(name):
    name = name.strip()
    if not name:
        return ""
    
    last_char = name[-1].lower()
    last_two = name[-2:].lower() if len(name) >= 2 else ""
    
    # 1. Αρσενικά σε -ης (π.χ. Γιάννης -> Γιάννη)
    if last_two == "ης":
        return name[:-1] # Κόβει το 'ς' -> Γιάννη
        
    # 2. Αρσενικά σε -ος (π.χ. Γιώργος -> Γιώργου)
    elif last_two == "ος":
        return name[:-2] + "ου" # Γιώργου
        
    # 3. Αρσενικά σε -ας (π.χ. Κώστας -> Κώστα)
    elif last_two == "ας":
        return name[:-1] # Κώστα
        
    # 4. Γυναικεία σε -η (π.χ. Ελένη -> Ελένης)
    elif last_char == "η":
        return name + "ς" # Ελένης
        
    # 5. Γυναικεία σε -α (π.χ. Μαρία -> Μαρίας)
    elif last_char == "α":
        return name + "ς" # Μαρίας
        
    # 6. Γυναικεία σε -ου (π.χ. Αλεξοῦ -> Αλεξούς - σπάνιο, ή μένει ως έχει)
    return name.upper()  

def to_genitive_last_name(surname):
    surname = surname.strip()
    if not surname:
        return ""
    
    last_two = surname[-2:].lower() if len(surname) >= 2 else ""
    
    # Τα περισσότερα ελληνικά επώνυμα ακολουθούν κανόνες:
    # -όπουλος, -άκης, -ίδης κλπ. λήγουν σε -ος -> γίνονται -ου
    if last_two == "ος":
        return surname[:-2] + "ου"
    
    # Επώνυμα που λήγουν σε -ης (π.χ. Χατζής -> Χατζή)
    elif last_two == "ης":
        return surname[:-1]
        
    # Άκλιτα ή ξενικά επώνυμα
    return surname.upper()  



def generate_doc(filename, articles, caller: Person, calling: Person):
    template_path = os.path.join("templates_files", filename)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Το αρχείο πρότυπο δεν βρέθηκε στο: {template_path}")
        
    doc = DocxTemplate(template_path)    
    
    context = {
        "caller_gender": guess_greek_gender(caller.name),
        "caller_name": to_genitive_first_name(caller.name).upper(),
        "caller_surname": to_genitive_last_name(caller.surname).upper(),
        "caller_fathers_name": caller.fathers_name.upper(),
        "caller_tax_id": caller.tax_id,
        "caller_address": caller.address.upper(),
        "calling_gender": guess_greek_gender(calling.name),
        "calling_name": to_genitive_first_name(calling.name).upper(),
        "calling_surname": to_genitive_last_name(calling.surname).upper(),
        "calling_fathers_name": calling.fathers_name.upper(),
        "calling_tax_id": calling.tax_id,
        "calling_address": calling.address.upper(),
        "date": datetime.now().strftime("%d/%m/%Y"),
        "articles": str(articles) if articles else "Δε βρέθηκε υπαγωγή",
    }
    
    doc.render(context)
    
    output_path = os.path.join(TEMP_FOLDER, "1.docx")
    
    doc.save(output_path)
    
    temp_zip_path = output_path + ".tmp"
    
    with zipfile.ZipFile(output_path, 'r') as zin:
        with zipfile.ZipFile(temp_zip_path, 'w') as zout:
            for item in zin.infolist():
                if item.filename != 'docProps/core.xml':
                    zout.writestr(item, zin.read(item.filename))
                    
    shutil.move(temp_zip_path, output_path)
    
    return output_path


@app.route('/exodiko')
def exodiko():
    return '<h1>Exodiko Page!</h1>'


@app.route('/asfalistika')
def asfalistika():
    return '<h1>asfalistika metra!!</h1>'


@app.route('/ypagogi')
def ypagogi():
    return '<h1>ypagogi page!!</h1>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)