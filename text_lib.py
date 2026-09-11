import unicodedata

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
