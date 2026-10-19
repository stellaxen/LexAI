import json,zipfile, shutil, os, text_lib    
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding


def initialize_rag_system(data_dir="./legal_docs", api_key=None):
    # 1. Ρύθμιση LLM με προσθήκη timeout=120.0
    Settings.llm = OpenAI(
        model="gpt-5.6-sol", 
        temperature=0,
        api_key=api_key,
        timeout=6000.0,  # <--- Timeout (σε δευτερόλεπτα)
        additional_kwargs={"response_format": {"type": "json_object"}}
    )
    
    # 2. Ρύθμιση Embedding Model (μπορείτε να προσθέσετε timeout και εδώ αν χρειαστεί)
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-large",
        api_key=api_key
    )
    
    # 3. Ορισμός SentenceSplitter για το Chunking
    parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    Settings.node_parser = parser
    
    print("[INFO] Loading legal documents...")
    documents = SimpleDirectoryReader(data_dir).load_data()
    
    print("[INFO] Parsing documents into chunks (nodes)...")
    nodes = parser.get_nodes_from_documents(documents)
    
    print(f"[INFO] Created {len(nodes)} chunks. Building vector index...")
    index = VectorStoreIndex(nodes)
    
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

# def make_answer(case_text, res):    
#     query_engine = res.as_query_engine(
#         similarity_top_k=10,
#         response_mode="compact"
#     )
    
#     response = query_engine.query(case_text)
#     print("\n--- Απάντηση RAG ---")
#     print(response)

#     response = str(response)
#     return beautify_answer(response)
#     # return response  # Επιστρέφουμε το raw string για περαιτέρω επεξεργασία




# def make_answer(user_input_text, index):
#     # Βήμα 1: Δημιουργούμε έναν retriever (μόνο για αναζήτηση)
#     retriever = index.as_retriever(similarity_top_k=3) # Παίρνουμε τα 3 πιο σχετικά κομμάτια
    
#     # Κάνουμε αναζήτηση χρησιμοποιώντας ΜΟΝΟ μια σύντομη περίληψη ή λέξεις-κλειδιά 
#     # (ώστε το embedding να μην ξεπεράσει τα 8192 tokens)
#     search_query = "κλοπή αυτοκινήτου νομική βάση άρθρα ποινικού κώδικα"
#     retrieved_nodes = retriever.retrieve(search_query)
    
#     # Ενώνουμε το κείμενο από τα RAG chunks που βρέθηκαν
#     rag_context = "\n\n".join([node.get_content() for node in retrieved_nodes])
    
#     # Βήμα 2: Συνθέτουμε το τελικό, μεγάλο prompt μας χειροκεντρικά
#     # (Εδώ μπορείτε να βάλετε όσες οδηγίες, κανόνες και JSON formats θέλετε, 
#     # καθώς ο gpt-5.6-sol έχει τεράστιο όριο context)
#     full_prompt = f"""
#     Είσαι ένας έμπειρος νομικός βοηθός...
#     [Εδώ βάζετε τις 30 οδηγίες λειτουργίας σας...]
    
#     === ΔΙΑΘΕΣΙΜΑ ΑΠΟΣΠΑΣΜΑΤΑ ΝΟΜΩΝ (RAG CONTEXT) ===
#     {rag_context}
    
#     === ΠΕΡΙΓΡΑΦΗ ΣΥΜΒΑΝΤΟΣ ΑΠΟ ΧΡΗΣΤΗ ===
#     {user_input_text}
    
#     Απάντησε αποκλειστικά σε μορφή JSON...
#     """
    
#     # Βήμα 3: Στέλνουμε το τελικό prompt απευθείας στον LLM
#     response = Settings.llm.complete(full_prompt)
    
#     return response.text



def make_answer(user_input_text, index):
    retriever = index.as_retriever(similarity_top_k=3)
    # search_query = "κλοπή αυτοκινήτου νομική βάση άρθρα ποινικού κώδικα"
    retrieved_nodes = retriever.retrieve(user_input_text)
    
    rag_context = "\n\n".join([node.get_content() for node in retrieved_nodes])
    
    full_prompt = f"""
    Είσαι ένας έμπειρος νομικός βοηθός...
    === ΔΙΑΘΕΣΙΜΑ ΑΠΟΣΠΑΣΜΑΤΑ ΝΟΜΩΝ (RAG CONTEXT) ===
    {rag_context}
    
    === ΠΕΡΙΓΡΑΦΗ ΣΥΜΒΑΝΤΟΣ ΑΠΟ ΧΡΗΣΤΗ ===
    {user_input_text}
    
    Απάντησε αποκλειστικά σε μορφή JSON...
    """

    print("\n\n\n[DEBUG] Full prompt sent to LLM:")
    print(full_prompt)
    print("[DEBUG] End of prompt \n\n\n\n")

    response = Settings.llm.complete(full_prompt)
    raw_text = response.text.strip()
    
    # Καθαρισμός από τυχόν markdown blocks (```json ... ```)
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    try:
        # Μετατροπή του JSON string σε Python dictionary
        data_dict = json.loads(raw_text.strip())
        return data_dict
    except json.JSONDecodeError:
        # Fallback σε περίπτωση που αποτύχει το JSON parsing
        return {
            "historic_summary": raw_text,
            "legal_substantiation": "Σφάλμα ανάλυσης JSON",
            "legal_base": "Δεν προκύπτει"
        }