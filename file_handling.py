import os
import subprocess
import tempfile
from flask import Flask, request, send_file  # Make sure send_file is included

from datetime import datetime
from models import Person

import func_lib, docs_lib


# ΝΑ ΧΡΗΣΙΜΟΠΟΙΗΘΕΙ ΣΑΝ TEMPLATE ΚΑΙ ΜΕΤΑ ΝΑ ΤΟ ΣΒΗΣΩ
# def handle_document_generation(request, template_docx, case_text):
#     """
#     Κοινή λογική για τη δημιουργία της φόρμας, μετατροπή σε docx, 
#     μετατροπή σε pdf μέσω LibreOffice και αποστολή στον browser.
#     """
#     try:
#         # 1. Δημιουργία αντικειμένων Person από τα δεδομένα της φόρμας
#         caller = Person(
#             name=request.form.get('caller_name'),
#             surname=request.form.get('caller_surname'),
#             fathers_name=request.form.get('caller_fathers_name'),
#             address=request.form.get('caller_address'),
#             tax_id=request.form.get('caller_tax_id')
#         )
#         calling = Person(
#             name=request.form.get('calling_name'),
#             surname=request.form.get('calling_surname'),
#             fathers_name=request.form.get('calling_fathers_name'),
#             address=request.form.get('calling_address'),
#             tax_id=request.form.get('calling_tax_id')
#         )

#         # 2. Δημιουργία του αρχείου Word
#         docx_path = docs_lib.generate_doc(template_docx, case_text, caller, calling)
#         return convert_docx_to_pdf(docx_path)

#     except Exception as e:
#         print(f"⚠️ PDF Conversion Exception: {e}")
#         return f"Error: {e}", 500



def create_exodiko(request, template_docx, exodiko_data):
    """
    Κοινή λογική για τη δημιουργία της φόρμας, παραγωγή του docx 
    και αποστολή του αρχείου Word απευθείας στον browser.
    """
    try:
        # 1. Δημιουργία αντικειμένων Person από τα δεδομένα της φόρμας
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

        # 2. Δημιουργία του αρχείου Word
        docx_path = docs_lib.generate_exodiko(template_docx, exodiko_data, caller, calling)
        
        # 3. Αποστολή του docx στον χρήστη
        return send_docx_file(docx_path)

    except Exception as e:
        print(f"⚠️ DOCX Generation Exception: {e}")
        return f"Error: {e}", 500


def create_asfalistika(request, template_docx, asfalistika_data):
    """
    Κοινή λογική για τη δημιουργία της φόρμας, παραγωγή του docx 
    και αποστολή του αρχείου Word απευθείας στον browser.
    """
    try:
        # 1. Δημιουργία αντικειμένων Person από τα δεδομένα της φόρμας
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

        # 2. Δημιουργία του αρχείου Word
        docx_path = docs_lib.generate_asfalistika(template_docx, asfalistika_data, caller, calling)
        
        # 3. Αποστολή του docx στον χρήστη
        return send_docx_file(docx_path)

    except Exception as e:
        print(f"⚠️ DOCX Generation Exception: {e}")
        return f"Error: {e}", 500



def send_docx_file(docx_path):
    output_dir = "output_docs"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    new_docx_name = f"{timestamp}"
    final_docx_path = os.path.join(output_dir, new_docx_name)

    # Αν το αρχείο δημιουργείται προσωρινά αλλού, το μεταφέρουμε στο φάκελο εξόδου με νέο όνομα
    if os.path.exists(docx_path):
        # Αν θες να το μετακινήσεις/μετονομάσεις:
        os.rename(docx_path, final_docx_path)
        # Ή αν το `generate_exodiko` το αποθηκεύει ήδη εκεί, απλά κάνε το send_file(docx_path)
        
        print(f"✅ DOCX Created and Ready: {final_docx_path}")
        
        return send_file(
            final_docx_path, 
            as_attachment=True, 
            download_name=f"{new_docx_name}.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        print("❌ DOCX creation failed (file not found).")
        return "DOCX creation failed.", 500