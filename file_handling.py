import os
import subprocess
import tempfile
from flask import Flask, render_template, request, send_file  # Make sure send_file is included

from datetime import datetime
from models import Person, RentalRestData

import func_lib, docs_lib


# ΝΑ ΧΡΗΣΙΜΟΠΟΙΗΘΕΙ ΣΑΝ TEMPLATE ΚΑΙ ΜΕΤΑ ΝΑ ΤΟ ΣΒΗΣΩ
def handle_document_generation(request, template_docx, case_text):
    """
    Κοινή λογική για τη δημιουργία της φόρμας, μετατροπή σε docx, 
    μετατροπή σε pdf μέσω LibreOffice και αποστολή στον browser.
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
        docx_path = docs_lib.generate_doc(template_docx, case_text, caller, calling)
        return convert_docx_to_pdf(docx_path)

    except Exception as e:
        print(f"⚠️ PDF Conversion Exception: {e}")
        return f"Error: {e}", 500



def handle_lease_agreement(request, template_docx, case_text):
    """
    Κοινή λογική για τη δημιουργία της φόρμας, μετατροπή σε docx, 
    μετατροπή σε pdf μέσω LibreOffice και αποστολή στον browser.
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

        rental_rest_data = RentalRestData(
            property_kind=request.form.get('property_kind'),
            property_address=request.form.get('property_address'),
            agreement_date = request.form.get('agreement_date'),
            monthly_rent=request.form.get('monthly_rent'),
            dept_months=request.form.get('dept_months'),
            total_dept=request.form.get('total_dept'),
            other_bills=request.form.get('other_bills'),
            caller_demand=request.form.get('caller_demand'),
            compliance_deadline=request.form.get('compliance_deadline'),
            comments=request.form.get('comments')
        )

        # 2. Δημιουργία του αρχείου Word
        docx_path = docs_lib.generate_lease_agreement(template_docx, case_text, caller, calling, rental_rest_data)
        return convert_docx_to_pdf(docx_path)

    except Exception as e:
        print(f"⚠️ PDF Conversion Exception: {e}")
        return f"Error: {e}", 500



    
def convert_docx_to_pdf(docx_path):
    output_dir = "output_pdfs"
    os.makedirs(output_dir, exist_ok=True)

    # 3. Μετατροπή σε PDF μέσω LibreOffice
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
        
        return send_file(
            final_pdf_path, 
            as_attachment=True, 
            download_name="document.pdf"
        )
    else:
        print("❌ PDF creation failed (file not found in output_dir).")
        return f"PDF creation failed. LibreOffice stderr: {result.stderr}", 500
        
