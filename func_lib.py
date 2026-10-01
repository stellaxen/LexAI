import json,zipfile, shutil, os, text_lib    
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

def initialize_rag_system(data_dir="./legal_docs", api_key=None):
    # Ορίζουμε τοπικά για τη διαδικασία, αν χρειαστεί, αλλά κυρίως το περνάμε στα αντικείμενα
    Settings.llm = OpenAI(
        model="gpt-4o", 
        temperature=0,
        api_key=api_key,  
        additional_kwargs={"response_format": {"type": "json_object"}}
    )
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-large",
        api_key=api_key   # <--- Και εδώ το δικό σας κλειδί
    )
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
            # answer = ""
            # # Αν το JSON περιέχει πολλαπλά αντικείμενα ή ενιαίο λεξικό με τα ζητούμενα πεδία
            # # Υποθέτουμε ότι τα νέα keys βρίσκονται απευθείας στο data ή μέσα σε nested δομή. 
            # # Εδώ τα διαχειριζόμαστε απευθείας από το level του data:
            
            # historic_summary = data.get("historic_summary", "")
            # legal_substantiation = data.get("legal_substantiation", "")
            # legal_base = data.get("legal_base", "")
            # aitoumena_zitimata = data.get("aitoumena_zitimata", "")
            # prothesmia_symmorfosis = data.get("prothesmia_symmorfosis", "")

            # # Εκτύπωση στην κονσόλα για έλεγχο
            # print(f"Ιστορικό (Historic Summary): {historic_summary}")
            # print(f"Νομική Τεκμηρίωση: {legal_substantiation}")
            # print(f"Νομική Βάση: {legal_base}")
            # print(f"Αιτούμενα Ζητήματα: {aitoumena_zitimata}")
            # print(f"Προθεσμία Συμμόρφωσης: {prothesmia_symmorfosis}")
            # print("-" * 40)

            # # Δόμηση του τελικού κειμένου απάντησης
            # answer = (
            #     f"\n**Ιστορικό:**\n{historic_summary}\n\n"
            #     f"**Νομική Τεκμηρίωση:**\n{legal_substantiation}\n\n"
            #     f"**Νομική Βάση:**\n{legal_base}\n\n"
            #     f"**Αιτούμενα Ζητήματα:**\n{aitoumena_zitimata}\n\n"
            #     f"**Προθεσμία Συμμόρφωσης:**\n{prothesmia_symmorfosis}"
            # )

            return data
        else:
            answer = "Δε βρέθηκε υπαγωγή για την περίπτωσή σας."
            
    except json.JSONDecodeError:        
        answer = "Δε βρέθηκε υπαγωγή για την περίπτωσή σας."
    
    return answer


# def beautify_answer(raw_string):
#     cleaned = raw_string.strip()

#     if cleaned.startswith("```json"):
#         cleaned = cleaned[7:]
#     elif cleaned.startswith("```"):
#         cleaned = cleaned[3:]

#     if cleaned.endswith("```"):
#         cleaned = cleaned[:-3]

#     try:
#         data = json.loads(cleaned.strip())
#         if isinstance(data, dict):
#             answer = ""
#             for key, value in data.items():
#                 print(f"Άρθρο: {key}")
#                 print(f"Κείμενο: {value['κείμενο']}")
#                 print(f"Αρχείο: {value['αρχείο']}")
#                 print("-" * 40)
#                 # Χρησιμοποιούμε απλές αλλαγές γραμμής αντί για HTML tags                
#                 answer += f"\n\n{key}\n{value['κείμενο']}\nΑρχείο: {value['αρχείο']}\n" 
#         else:
#             answer = "Δε βρέθηκε υπαγωγή για την περίπτωση σας."
            
#     except json.JSONDecodeError:        
#         answer = "Δε βρέθηκε υπαγωγή για την περίπτωση σας."
    
#     return answer

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
    # return response  # Επιστρέφουμε το raw string για περαιτέρω επεξεργασία



