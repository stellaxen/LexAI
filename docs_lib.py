from docxtpl import DocxTemplate
from datetime import datetime

from models import Person, RentalRestData
import os, zipfile, shutil, text_lib

# ΝΑ ΧΡΗΣΙΜΟΠΟΙΗΘΕΙ ΣΑΝ TEMPLATE ΚΑΙ ΜΕΤΑ ΝΑ ΤΟ ΣΒΗΣΩ
def generate_doc(filename, articles, caller: Person, calling: Person):
    template_path = os.path.join("templates_files", filename)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Το αρχείο πρότυπο δεν βρέθηκε στο: {template_path}")
        
    doc = DocxTemplate(template_path)    
    
    context = {
        "caller_gender": text_lib.guess_greek_gender(caller.name),
        "caller_name": text_lib.to_genitive_first_name(caller.name).upper(),
        "caller_surname": text_lib.to_genitive_last_name(caller.surname).upper(),
        "caller_fathers_name": caller.fathers_name.upper(),
        "caller_tax_id": caller.tax_id,
        "caller_address": caller.address.upper(),
        "calling_gender": text_lib.guess_greek_gender(calling.name),
        "calling_name": text_lib.to_genitive_first_name(calling.name).upper(),
        "calling_surname": text_lib.to_genitive_last_name(calling.surname).upper(),
        "calling_fathers_name": calling.fathers_name.upper(),
        "calling_tax_id": calling.tax_id,
        "calling_address": calling.address.upper(),
        "date": datetime.now().strftime("%d/%m/%Y"),
        "articles": str(articles) if articles else "Δε βρέθηκε υπαγωγή",
    }

    return make_pdf(doc, context)


def generate_lease_agreement(filename, articles, caller: Person, calling: Person, rental_rest_data: RentalRestData):
    template_path = os.path.join("templates_files", filename)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Το αρχείο πρότυπο δεν βρέθηκε στο: {template_path}")
        
    doc = DocxTemplate(template_path)    
    
    context = {
        "caller_gender": text_lib.guess_greek_gender(caller.name),
        "caller_name": text_lib.to_genitive_first_name(caller.name).upper(),
        "caller_surname": text_lib.to_genitive_last_name(caller.surname).upper(),
        "caller_fathers_name": caller.fathers_name.upper(),
        "caller_tax_id": caller.tax_id,
        "caller_address": caller.address.upper(),
        "calling_gender": text_lib.guess_greek_gender(calling.name),
        "calling_name": text_lib.to_genitive_first_name(calling.name).upper(),
        "calling_surname": text_lib.to_genitive_last_name(calling.surname).upper(),
        "calling_fathers_name": calling.fathers_name.upper(),
        "calling_tax_id": calling.tax_id,
        "calling_address": calling.address.upper(),
        "date": datetime.now().strftime("%d/%m/%Y"),

        "property_kind": rental_rest_data.property_kind,
        "property_address": rental_rest_data.property_address,
        "agreement_date": rental_rest_data.agreement_date,
        "monthly_rent": rental_rest_data.monthly_rent,
        "dept_months": rental_rest_data.dept_months,
        "total_dept": rental_rest_data.total_dept,
        "other_bills": rental_rest_data.other_bills,
        "caller_demand": rental_rest_data.caller_demand,
        "compliance_deadline": rental_rest_data.compliance_deadline,
        "comments": rental_rest_data.comments,

        "articles": str(articles) if articles else "Δε βρέθηκε υπαγωγή",
    }

    return make_pdf(doc, context)

def make_pdf(doc, context):
    doc.render(context)    
    output_path = os.path.join( os.getenv("TEMP_FOLDER"), "temp.docx")    
    doc.save(output_path)    
    temp_zip_path = output_path + ".tmp"
    
    with zipfile.ZipFile(output_path, 'r') as zin:
        with zipfile.ZipFile(temp_zip_path, 'w') as zout:
            for item in zin.infolist():
                if item.filename != 'docProps/core.xml':
                    zout.writestr(item, zin.read(item.filename))
                    
    shutil.move(temp_zip_path, output_path)
    
    return output_path