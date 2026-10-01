from docxtpl import DocxTemplate
from datetime import datetime

from models import Person
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


def generate_exodiko(filename, exodiko_data, caller: Person, calling: Person):
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

                
        "historic_summary": exodiko_data.get("historic_summary", "Δεν προκύπτει από το ιστορικό"),
        "legal_substantiation": exodiko_data.get("legal_substantiation", "Δεν προκύπτει από το ιστορικό"),
        "legal_base": exodiko_data.get("legal_base", "Δεν προκύπτει από το ιστορικό"),
        "aitoumena_zitimata": exodiko_data.get("aitoumena_zitimata", "Δεν προκύπτει από το ιστορικό"),
        "prothesmia_symmorfosis": exodiko_data.get("prothesmia_symmorfosis", "Δεν προκύπτει από το ιστορικό"),
    }

    return make_pdf(doc, context)

def generate_asfalistika(filename, asfalistika_data, caller: Person, calling: Person):
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

                
        "historic_summary": asfalistika_data.get("historic_summary", "Δεν προκύπτει από το ιστορικό"),
        "legal_substantiation": asfalistika_data.get("legal_substantiation", "Δεν προκύπτει από το ιστορικό"),
        "aitoumena_zitimata": asfalistika_data.get("aitoumena_zitimata", "Δεν προκύπτει από το ιστορικό"),
        "prothesmia_symmorfosis": asfalistika_data.get("prothesmia_symmorfosis", "Δεν προκύπτει από το ιστορικό"),
    }

    return make_pdf(doc, context)

def generate_ypagogi(filename, ypagogi_data):
    template_path = os.path.join("templates_files", filename)
    print(f"TTTTTTTTTTTTTTemplate Path: {template_path}")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Το αρχείο πρότυπο δεν βρέθηκε στο: {template_path}")
        
    doc = DocxTemplate(template_path)    
    
    context = {        
        "date": datetime.now().strftime("%d/%m/%Y"),

                
        "historic_summary": ypagogi_data.get("historic_summary", "Δεν προκύπτει από το ιστορικό"),
        "legal_substantiation": ypagogi_data.get("legal_substantiation", "Δεν προκύπτει από το ιστορικό"),
        "aitoumena_zitimata": ypagogi_data.get("aitoumena_zitimata", "Δεν προκύπτει από το ιστορικό"),
        "prothesmia_symmorfosis": ypagogi_data.get("prothesmia_symmorfosis", "Δεν προκύπτει από το ιστορικό"),
    }

    return make_pdf(doc, context)


def generate_agogi(filename, agogi_data, caller: Person, calling: Person):
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

                
        "historic_summary": agogi_data.get("historic_summary", "Δεν προκύπτει από το ιστορικό"),
        "legal_substantiation": agogi_data.get("legal_substantiation", "Δεν προκύπτει από το ιστορικό"),
        "aitoumena_zitimata": agogi_data.get("aitoumena_zitimata", "Δεν προκύπτει από το ιστορικό"),
        "prothesmia_symmorfosis": agogi_data.get("prothesmia_symmorfosis", "Δεν προκύπτει από το ιστορικό"),
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