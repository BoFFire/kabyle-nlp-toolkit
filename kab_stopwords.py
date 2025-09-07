#!/usr/bin/env python3
import re
import unicodedata
from collections import Counter

# Kabyle core alphabet (lowercase)
KABYLE_CORE = "abcčdḍeɛfgǧɣhḥijklmnpqrṛsṣtṭuwxyzẓ"
# Regex for Kabyle words (case-insensitive)
KABYLE_PATTERN = rf"[{KABYLE_CORE}{KABYLE_CORE.upper()}]+"

# Words to always exclude from stopwords
EXCLUDE = {"mary"}


def create_stopwords(input_filename, output_filename,
                     rel_cutoff=0.005, min_count=0, max_words=None, exclude=None):
    """
    Lit le fichier 'input_filename', normalise et tokenize le texte en utilisant
    uniquement l'alphabet kabyle CLDR, calcule la fréquence de chaque mot et écrit
    dans 'output_filename' la liste des mots apparaissant au moins 'rel_cutoff'
    (proportion du corpus) ou au moins 'min_count' fois, sauf ceux dans 'exclude'.
    Peut aussi limiter la liste aux 'max_words' les plus fréquents.

    Args:
        input_filename (str): Le fichier source (par ex. kab_fixed.txt).
        output_filename (str): Le fichier où sauvegarder la liste de stopwords.
        rel_cutoff (float): Seuil de fréquence relative (0 = désactivé).
        min_count (int): Seuil de fréquence absolue (0 = désactivé).
        max_words (int): Nombre maximum de stopwords à garder (défaut: None).
        exclude (set): Ensemble de mots à exclure (défaut: EXCLUDE global).
        
    Returns:
        list: La liste des candidats stopwords.
    """
    if exclude is None:
        exclude = EXCLUDE

    # Lire et normaliser en NFC
    with open(input_filename, "r", encoding="utf-8") as f:
        text = f.read()
    text = unicodedata.normalize('NFC', text)
    
    # Tokenisation basée sur l’alphabet Kabyle
    tokens = re.findall(KABYLE_PATTERN, text.lower())
    
    # Calcul des fréquences
    freq = Counter(tokens)
    total_tokens = sum(freq.values())
    
    # Sélectionner les mots selon les seuils
    candidate_stopwords = [
        word for word, count in freq.items()
        if (
            ((rel_cutoff == 0 or count / total_tokens >= rel_cutoff)
             or (min_count == 0 or count >= min_count))
            and word not in exclude
        )
    ]
    
    # Trier par fréquence décroissante
    candidate_stopwords = sorted(candidate_stopwords,
                                 key=lambda w: freq[w],
                                 reverse=True)

    # Limiter au top-N si demandé
    if max_words is not None:
        candidate_stopwords = candidate_stopwords[:max_words]
    
    # Sauvegarder
    with open(output_filename, "w", encoding="utf-8") as f_out:
        for word in candidate_stopwords:
            f_out.write(word + "\n")
    
    return candidate_stopwords


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Kabyle stopwords from corpus")
    parser.add_argument("input", help="Input text file (UTF-8)")
    parser.add_argument("output", help="Output stopwords file (UTF-8)")
    parser.add_argument("--rel_cutoff", type=float, default=0.005,
                        help="Relative frequency cutoff (default: 0.005 = 0.5%%, 0 = disabled)")
    parser.add_argument("--min_count", type=int, default=0,
                        help="Absolute frequency cutoff (default: 0 = disabled)")
    parser.add_argument("--max_words", type=int, default=None,
                        help="Maximum number of stopwords to keep (default: unlimited)")
    parser.add_argument("--top", type=int, default=20,
                        help="Show top-N stopwords with frequency (default: 20)")
    args = parser.parse_args()

    stopwords = create_stopwords(args.input, args.output,
                                 rel_cutoff=args.rel_cutoff,
                                 min_count=args.min_count,
                                 max_words=args.max_words)

    print(f"\n{len(stopwords)} stopwords saved to {args.output}\n")

    # Recompute frequencies for inspection
    with open(args.input, "r", encoding="utf-8") as f:
        text = unicodedata.normalize('NFC', f.read())
    tokens = re.findall(KABYLE_PATTERN, text.lower())
    freq = Counter(tokens)
    total_tokens = sum(freq.values())

    print(f"Top {args.top} stopword candidates:")
    for word in stopwords[:args.top]:
        rel_freq = freq[word] / total_tokens
        print(f"{word:15} {freq[word]:8d} ({rel_freq:.3%})")
