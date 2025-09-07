#!/usr/bin/env python3
"""
Tatoeba Corpus Processing Tool

Ce script télécharge les archives Tatoeba (phrases et liens), 
extrait les paires de phrases anglais–kabyle et les enregistre dans un fichier TSV,
puis crée deux fichiers texte (eng.txt et kab.txt) pour les phrases respectives.
Ensuite, il corrige le fichier kab.txt via le module fixer,
et enfin, il génère une liste de stopwords en kabyle à partir du fichier corrigé.
Tous les fichiers de sortie sont sauvegardés dans le répertoire "corpus" (défaut).

Tatoeba exports: https://tatoeba.org/en/downloads
"""

import os
import re
import unicodedata
import requests
import tarfile
import csv
import argparse
from yaspin import yaspin
import fixer  # Module de correction
import kab_stopwords  # Notre module pour créer la liste de stopwords
import nltk
from collections import Counter

# Téléchargement des ressources NLTK
nltk.download('punkt')

# URL pour les exports Tatoeba
SENTENCES_URL = "https://downloads.tatoeba.org/exports/sentences.tar.bz2"
LINKS_URL = "https://downloads.tatoeba.org/exports/links.tar.bz2"

# Noms de fichiers locaux pour les archives
SENTENCES_TAR = "sentences.tar.bz2"
LINKS_TAR = "links.tar.bz2"

### Fonctions de téléchargement ###
def get_remote_file_size(url):
    response = requests.head(url)
    response.raise_for_status()
    return int(response.headers.get('Content-Length', 0))

def download_file(url, filename):
    remote_size = get_remote_file_size(url)
    if os.path.exists(filename):
        local_size = os.path.getsize(filename)
        if local_size == remote_size:
            print(f"{filename} existe déjà (taille {local_size} octets), téléchargement ignoré.")
            return
        else:
            print(f"{filename} existe mais la taille diffère (local: {local_size}, remote: {remote_size}). Re-téléchargement.")
    else:
        print(f"Téléchargement de {filename} depuis {url} ...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Téléchargement terminé pour {filename}.")

### Fonctions génératrices pour parcourir les archives ###
def iter_sentences(tar_filename):
    with tarfile.open(tar_filename, "r:bz2") as tar:
        member = None
        for m in tar.getmembers():
            if os.path.basename(m.name).startswith("sentences"):
                member = m
                break
        if member is None:
            raise Exception("Fichier 'sentences' introuvable dans l'archive.")
        f = tar.extractfile(member)
        if f is None:
            raise Exception("Impossible d'extraire le fichier 'sentences'.")
        for line in f:
            parts = line.decode('utf-8').rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            yield parts[0], parts[1], parts[2]

def iter_links(tar_filename):
    with tarfile.open(tar_filename, "r:bz2") as tar:
        member = None
        for m in tar.getmembers():
            if os.path.basename(m.name).startswith("links"):
                member = m
                break
        if member is None:
            raise Exception("Fichier 'links' introuvable dans l'archive.")
        f = tar.extractfile(member)
        if f is None:
            raise Exception("Impossible d'extraire le fichier 'links'.")
        for line in f:
            parts = line.decode('utf-8').rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            yield parts[0], parts[1]

### Fonctions de traitement ###
def build_kab_sentence_dict():
    kab_sentences = {}
    for sid, lang, text in iter_sentences(SENTENCES_TAR):
        if lang == "kab":
            kab_sentences[sid] = text
    print(f"Trouvé {len(kab_sentences)} phrases en kabyle.")
    return kab_sentences

def build_eng_ids_needed(kab_sentences):
    eng_ids = set()
    for sid1, sid2 in iter_links(LINKS_TAR):
        if sid1 in kab_sentences and sid2 not in kab_sentences:
            eng_ids.add(sid2)
        elif sid2 in kab_sentences and sid1 not in kab_sentences:
            eng_ids.add(sid1)
    print(f"Identifié {len(eng_ids)} IDs de phrases anglaises associées au kabyle.")
    return eng_ids

def build_eng_sentence_dict(eng_ids):
    eng_sentences = {}
    for sid, lang, text in iter_sentences(SENTENCES_TAR):
        if lang == "eng" and sid in eng_ids:
            eng_sentences[sid] = text
    print(f"Chargé {len(eng_sentences)} phrases anglaises parmi les IDs candidats.")
    return eng_sentences

def write_sentence_pairs(eng_sentences, kab_sentences, output_filename):
    seen = set()
    with open(output_filename, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out, delimiter="\t")
        writer.writerow(["English", "Kabyle"])
        for sid1, sid2 in iter_links(LINKS_TAR):
            if sid1 in kab_sentences and sid2 in eng_sentences:
                key = tuple(sorted([sid1, sid2]))
                if key in seen:
                    continue
                seen.add(key)
                writer.writerow([eng_sentences[sid2], kab_sentences[sid1]])
            elif sid2 in kab_sentences and sid1 in eng_sentences:
                key = tuple(sorted([sid1, sid2]))
                if key in seen:
                    continue
                seen.add(key)
                writer.writerow([eng_sentences[sid1], kab_sentences[sid2]])
    print(f"Paires de phrases écrites dans {output_filename}.")

def split_tsv_to_text(tsv_filename, en_out, kab_out):
    with open(tsv_filename, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        with open(en_out, "w", encoding="utf-8") as en_file, \
             open(kab_out, "w", encoding="utf-8") as kab_file:
            for row in reader:
                english = row.get("English", "").strip()
                kabyle = row.get("Kabyle", "").strip()
                if english:
                    en_file.write(english + "\n")
                if kabyle:
                    kab_file.write(kabyle + "\n")
    print(f"Créé {en_out} et {kab_out} à partir de {tsv_filename}.")

### Fonction principale ###
def main():
    parser = argparse.ArgumentParser(description="Tatoeba Corpus Processing Tool")
    parser.add_argument("--source_lang", required=True, help="Code ISO pour la langue source (ex: eng)")
    parser.add_argument("--target_lang", required=True, help="Code ISO pour la langue cible (ex: kab)")
    parser.add_argument("--output_dir", default="corpus", help="Répertoire de sortie (défaut: corpus)")
    args = parser.parse_args()
    
    source_lang = args.source_lang
    target_lang = args.target_lang
    output_dir = args.output_dir
    
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    
    OUTPUT_TSV = os.path.join(output_dir, f"{source_lang}_{target_lang}_sentence_pairs.tsv")
    EN_OUTPUT = os.path.join(output_dir, f"{source_lang}.txt")
    KAB_OUTPUT = os.path.join(output_dir, f"{target_lang}.txt")
    KAB_FIXED = os.path.join(output_dir, f"{target_lang}_fixed.txt")
    STOPWORDS_OUTPUT = os.path.join(output_dir, "kab_stopwords.txt")
    
    with yaspin(text="Téléchargement de l'archive des phrases...", color="cyan") as spinner:
        download_file(SENTENCES_URL, SENTENCES_TAR)
        spinner.ok("✔")
    with yaspin(text="Téléchargement de l'archive des liens...", color="cyan") as spinner:
        download_file(LINKS_URL, LINKS_TAR)
        spinner.ok("✔")
    
    with yaspin(text="Construction du dictionnaire de phrases en kabyle...", color="cyan") as spinner:
        kab_sentences = build_kab_sentence_dict()
        spinner.ok("✔")
    
    with yaspin(text="Collecte des IDs anglais candidats...", color="cyan") as spinner:
        eng_ids_needed = build_eng_ids_needed(kab_sentences)
        spinner.ok("✔")
    
    with yaspin(text="Chargement des phrases anglaises...", color="cyan") as spinner:
        eng_sentences = build_eng_sentence_dict(eng_ids_needed)
        spinner.ok("✔")
    
    with yaspin(text="Écriture des paires de phrases dans le TSV...", color="cyan") as spinner:
        write_sentence_pairs(eng_sentences, kab_sentences, OUTPUT_TSV)
        spinner.ok("✔")
    
    with yaspin(text="Séparation du TSV en eng.txt et kab.txt...", color="cyan") as spinner:
        split_tsv_to_text(OUTPUT_TSV, EN_OUTPUT, KAB_OUTPUT)
        spinner.ok("✔")
    
    # Correction du fichier kab.txt à l'aide du module fixer
    with yaspin(text="Correction de kab.txt...", color="cyan") as spinner:
        fix_mapping = {
            'ţţ': 'tt',
            'țț': 'tt',
            'ε': 'ɛ',
            'ϵ': 'ɛ',
            'γ': 'ɣ',
            'Γ': 'Ɣ',
            'Σ': 'Ɛ',
            'Ԑ': 'Ɛ',
            'ğ': 'ǧ',
            'ş': 'ṣ'
        }
        num_fixed = fixer.fix_file(KAB_OUTPUT, KAB_FIXED, fix_mapping)
        spinner.ok("✔")
        print(f"{num_fixed} lignes corrigées dans {KAB_OUTPUT}. Fichier corrigé sauvegardé sous '{KAB_FIXED}'.")
    
    # Création de la liste de stopwords à partir du fichier corrigé kab_fixed.txt
    with yaspin(text="Création de la liste de stopwords en kabyle...", color="cyan") as spinner:
        stopwords = kab_stopwords.create_stopwords(
            KAB_FIXED,
            STOPWORDS_OUTPUT,
            rel_cutoff=0.005,   # 0.5% cutoff
            min_count=10,       # ignore words with < 10 occurrences
            max_words=500       # keep only the 500 most frequent stopwords
        )
        spinner.ok("✔")
        print(f"Liste de stopwords créée avec {len(stopwords)} mots et sauvegardée dans {STOPWORDS_OUTPUT}.")

    
    print("Toutes les étapes sont terminées.")

if __name__ == "__main__":
    main()
