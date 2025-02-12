import re
import unicodedata
from collections import Counter

def create_stopwords(input_filename, output_filename, threshold=100):
    """
    Lit le fichier 'input_filename', normalise et tokenize le texte,
    calcule la fréquence de chaque mot et écrit dans 'output_filename'
    la liste des mots apparaissant au moins 'threshold' fois.
    
    Args:
        input_filename (str): Le fichier source (par exemple, kab_fixed.txt).
        output_filename (str): Le fichier où sauvegarder la liste de stopwords.
        threshold (int): Le seuil de fréquence pour considérer un mot comme stopword (défaut 1000).
        
    Returns:
        list: La liste des candidats stopwords.
    """
    # Lire le contenu du fichier et normaliser Unicode (form NFC)
    with open(input_filename, "r", encoding="utf-8") as f:
        text = f.read()
    text = unicodedata.normalize('NFC', text)
    
    # Tokenisation : extraire les mots en convertissant en minuscules
    tokens = re.findall(r'\w+', text.lower())
    
    # Calculer la distribution de fréquence
    freq = Counter(tokens)
    
    # Sélectionner les mots qui apparaissent au moins 'threshold' fois
    candidate_stopwords = [word for word, count in freq.items() if count >= threshold]
    
    # Sauvegarder la liste dans output_filename
    with open(output_filename, "w", encoding="utf-8") as f_out:
        for word in candidate_stopwords:
            f_out.write(word + "\n")
    
    return candidate_stopwords
