import json,zipfile, shutil, os, text_lib    
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

def initialize_rag_system(data_dir="./data", api_key=None):
    # Ορίζουμε τοπικά για τη διαδικασία, αν χρειαστεί, αλλά κυρίως το περνάμε στα αντικείμενα
    Settings.llm = OpenAI(
        model="gpt-4o", 
        temperature=0,
        api_key=api_key,  # <--- Εδώ δίνουμε ρητά το δικό σας κλειδί
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



