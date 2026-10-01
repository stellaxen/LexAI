from dotenv import load_dotenv
from flask import Flask, render_template, request
import os, func_lib

import file_handling, prompts_lib

load_dotenv()

app = Flask(__name__, template_folder='templates')

API_KEY = os.getenv("XENAKI_OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Δεν βρέθηκε το OPENAI_API_KEY...")

os.makedirs(os.getenv("TEMP_FOLDER"), exist_ok=True)


rag_index = func_lib.initialize_rag_system(api_key=API_KEY)

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
        case_text = func_lib.make_answer(prompt_text, rag_index) 
        
        # Κλήση της κοινής συνάρτησης
        return file_handling.handle_document_generation(request, "ypagogi.docx", case_text)


@app.route('/exodiko', methods={'GET', 'POST'})
def exodiko():
    if request.method == 'GET':
        return render_template('exodiko.html')
    elif request.method == 'POST':
        # Για δοκιμή ή πραγματική χρήση
        # case_text = "DOKIMASTIKO KEIMENO GIA TESTING"
        case_text = request.form.get('case_description')  
        print("Received case description:", case_text)  

        prompt = prompts_lib.exodiko_prompt(case_text)
        print(prompt)  # Εκτύπωση του prompt για έλεγχο

        exodiko_data = func_lib.make_answer(prompt, rag_index)
        print(exodiko_data)
        
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
        print(prompt)  # Εκτύπωση του prompt για έλεγχο
        

        asfalistika_data = func_lib.make_answer(prompt, rag_index)
        print(asfalistika_data)
        
        # Κλήση της κοινής συνάρτησης με το αντίστοιχο docx template
        return file_handling.create_asfalistika(request, "asfalistika.docx", asfalistika_data)



@app.route('/agogi')
def agogi():
    return render_template('agogi.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7654)