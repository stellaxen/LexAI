import datetime
import os
from dotenv import load_dotenv  # 1. Εισαγωγή της βιβλιοθήκης

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
                answer += f"\n\nΆρθρο: {key}\n{value['κείμενο']}\nΑρχείο: {value['αρχείο']}\n" 
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
        prompt_text = request.form.get('case_text') + rest_prompt
        case_text = make_answer(prompt_text, rag_index)
        
        try:
            # 1. Δημιουργία του αρχείου Word
            docx_path = generate_doc("ypagogi.docx", case_text)  
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


def generate_doc(filename, articles):
    template_path = os.path.join("templates_files", filename)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Το αρχείο πρότυπο δεν βρέθηκε στο: {template_path}")
        
    doc = DocxTemplate(template_path)
    
    context = {
        "caller_name": "Γιάννης",
        "caller_surname": "Παπαδόπουλος",
        "caller_fathers_name": "Κωνσταντίνος",
        "caller_tax_id": "123456789",
        "caller_address": "Οδός 123, Πόλη 12345",
        "calling_name": "Κώστας",
        "calling_surname": "Γεωργίου",
        "calling_fathers_name": "Ιωάννης",
        "calling_tax_id": "089654323",
        "calling_address": "Οδός Λιβανου 125,  Χίος 82131",
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