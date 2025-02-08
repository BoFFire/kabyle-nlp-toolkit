#!/usr/bin/env python3
"""
Tatoeba Corpus Processing Tool

This tool downloads the Tatoeba sentences and links archives (if needed),
extracts and processes them in a memory-efficient, streaming manner to build a TSV file
of English (eng)–Kabyle (kab) sentence pairs, and then splits that TSV file into:
  - en.txt (only English sentences)
  - kab.txt (only Kabyle sentences)

In a final step, it fixes the generated kab.txt file using the fixer module.
All output files are saved in an output directory (default: "corpus").

A spinner (from yaspin) is displayed during each major operation.

Tatoeba exports: https://tatoeba.org/en/downloads
"""

import os
import requests
import tarfile
import csv
import argparse
from yaspin import yaspin
import fixer  # Import the fixer module

# URLs for Tatoeba exports
SENTENCES_URL = "https://downloads.tatoeba.org/exports/sentences.tar.bz2"
LINKS_URL = "https://downloads.tatoeba.org/exports/links.tar.bz2"

# Filenames for the downloaded archives
SENTENCES_TAR = "sentences.tar.bz2"
LINKS_TAR = "links.tar.bz2"

### Download functions with size check ###
def get_remote_file_size(url):
    """Return the remote file size (in bytes) using a HEAD request."""
    response = requests.head(url)
    response.raise_for_status()
    return int(response.headers.get('Content-Length', 0))

def download_file(url, filename):
    """Download file from URL if local file is missing or size does not match remote."""
    remote_size = get_remote_file_size(url)
    if os.path.exists(filename):
        local_size = os.path.getsize(filename)
        if local_size == remote_size:
            print(f"{filename} already exists with matching size ({local_size} bytes), skipping download.")
            return
        else:
            print(f"{filename} exists but size differs (local: {local_size}, remote: {remote_size}). Re-downloading.")
    else:
        print(f"Downloading {filename} from {url} ...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {filename}.")

### Generator functions for streaming through tar archive files ###
def iter_sentences(tar_filename):
    """
    Generator that yields (sentence_id, lang, text) for each line in the sentences file.
    Opens the tar archive, finds the file whose basename starts with "sentences", and streams its lines.
    """
    with tarfile.open(tar_filename, "r:bz2") as tar:
        member = None
        for m in tar.getmembers():
            if os.path.basename(m.name).startswith("sentences"):
                member = m
                break
        if member is None:
            raise Exception("Could not find the sentences file in the archive.")
        f = tar.extractfile(member)
        if f is None:
            raise Exception("Could not extract the sentences file.")
        for line in f:
            parts = line.decode('utf-8').rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            yield parts[0], parts[1], parts[2]

def iter_links(tar_filename):
    """
    Generator that yields (sentence_id, translation_id) for each line in the links file.
    Opens the tar archive, finds the file whose basename starts with "links", and streams its lines.
    """
    with tarfile.open(tar_filename, "r:bz2") as tar:
        member = None
        for m in tar.getmembers():
            if os.path.basename(m.name).startswith("links"):
                member = m
                break
        if member is None:
            raise Exception("Could not find the links file in the archive.")
        f = tar.extractfile(member)
        if f is None:
            raise Exception("Could not extract the links file.")
        for line in f:
            parts = line.decode('utf-8').rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            yield parts[0], parts[1]

### Processing functions ###
def build_kab_sentence_dict():
    """
    Iterates over the sentences file and builds a dictionary of Kabyle sentences.
    Returns a dict mapping sentence_id -> text for sentences where lang == "kab".
    """
    kab_sentences = {}
    for sid, lang, text in iter_sentences(SENTENCES_TAR):
        if lang == "kab":
            kab_sentences[sid] = text
    print(f"Found {len(kab_sentences)} Kabyle sentences.")
    return kab_sentences

def build_eng_ids_needed(kab_sentences):
    """
    Iterates over the links file and collects a set of sentence IDs paired with a Kabyle sentence.
    If one side is Kabyle, the other is treated as a candidate English sentence.
    Returns a set of candidate English sentence IDs.
    """
    eng_ids = set()
    for sid1, sid2 in iter_links(LINKS_TAR):
        if sid1 in kab_sentences and sid2 not in kab_sentences:
            eng_ids.add(sid2)
        elif sid2 in kab_sentences and sid1 not in kab_sentences:
            eng_ids.add(sid1)
    print(f"Identified {len(eng_ids)} candidate English sentence IDs paired with Kabyle.")
    return eng_ids

def build_eng_sentence_dict(eng_ids):
    """
    Iterates over the sentences file and builds a dictionary for English sentences
    whose IDs are in eng_ids. Returns a dict mapping sentence_id -> text.
    """
    eng_sentences = {}
    for sid, lang, text in iter_sentences(SENTENCES_TAR):
        if lang == "eng" and sid in eng_ids:
            eng_sentences[sid] = text
    print(f"Loaded {len(eng_sentences)} English sentences from candidate IDs.")
    return eng_sentences

def write_sentence_pairs(eng_sentences, kab_sentences, output_filename):
    """
    Iterates over the links file (streaming) and writes to output_filename
    the English–Kabyle pairs (with English sentence first) when one sentence is in eng_sentences
    and the other is in kab_sentences. Duplicate pairs are skipped.
    """
    seen = set()  # To avoid duplicate pairs (using sorted tuple of IDs as key)
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
    print(f"Wrote sentence pairs to {output_filename}.")

def split_tsv_to_text(tsv_filename, en_out, kab_out):
    """
    Reads the TSV file and splits it into two text files:
      - en_out: one English sentence per line.
      - kab_out: one Kabyle sentence per line.
    """
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
    print(f"Created {en_out} and {kab_out} from {tsv_filename}.")

### Main function ###
def main():
    parser = argparse.ArgumentParser(description="Tatoeba Corpus Processing Tool")
    parser.add_argument("--source_lang", required=True, help="ISO code for source language (e.g., eng)")
    parser.add_argument("--target_lang", required=True, help="ISO code for target language (e.g., kab)")
    parser.add_argument("--output_dir", default="corpus", help="Output directory for all files (default: corpus)")
    args = parser.parse_args()
    
    source_lang = args.source_lang
    target_lang = args.target_lang
    output_dir = args.output_dir
    
    # Ensure output directory exists.
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    
    # Define output file paths.
    OUTPUT_TSV = os.path.join(output_dir, f"{source_lang}_{target_lang}_sentence_pairs.tsv")
    EN_OUTPUT = os.path.join(output_dir, f"{source_lang}.txt")
    KAB_OUTPUT = os.path.join(output_dir, f"{target_lang}.txt")
    KAB_FIXED = os.path.join(output_dir, f"{target_lang}_fixed.txt")
    
    from yaspin import yaspin

    with yaspin(text="Downloading sentences archive...", color="cyan") as spinner:
        download_file(SENTENCES_URL, SENTENCES_TAR)
        spinner.ok("✔")
    with yaspin(text="Downloading links archive...", color="cyan") as spinner:
        download_file(LINKS_URL, LINKS_TAR)
        spinner.ok("✔")
    
    with yaspin(text="Building Kabyle sentence dictionary...", color="cyan") as spinner:
        kab_sentences = build_kab_sentence_dict()
        spinner.ok("✔")
    
    with yaspin(text="Collecting candidate English sentence IDs...", color="cyan") as spinner:
        eng_ids_needed = build_eng_ids_needed(kab_sentences)
        spinner.ok("✔")
    
    with yaspin(text="Loading English sentences...", color="cyan") as spinner:
        eng_sentences = build_eng_sentence_dict(eng_ids_needed)
        spinner.ok("✔")
    
    with yaspin(text="Writing English–Kabyle sentence pairs to TSV...", color="cyan") as spinner:
        write_sentence_pairs(eng_sentences, kab_sentences, OUTPUT_TSV)
        spinner.ok("✔")
    
    with yaspin(text="Splitting TSV into en.txt and kab.txt...", color="cyan") as spinner:
        split_tsv_to_text(OUTPUT_TSV, EN_OUTPUT, KAB_OUTPUT)
        spinner.ok("✔")
    
    # Final step: fix the generated kab.txt file.
    with yaspin(text="Fixing kab.txt...", color="cyan") as spinner:
        fix_mapping = {
            'ţţ': 'tt',   # Two consecutive ţ's → "tt"
            'țț': 'tt',   # Two consecutive ț's → "tt"
            'ε': 'ɛ',     # Greek small epsilon → Latin small open e
            'ϵ': 'ɛ',     # Greek lunate epsilon → Latin small open e
            'γ': 'ɣ',     # Greek small gamma → Latin small gamma
            'Γ': 'Ɣ',     # Greek capital Gamma → Latin capital Ɣ
            'Σ': 'Ɛ',     # Greek capital Sigma → Latin capital Ɛ
            'Ԑ': 'Ɛ',     # Cyrillic letter Ԑ → Latin capital Ɛ
            'ğ': 'ǧ',     # Latin letter ğ → Latin letter ǧ
            'ş': 'ṣ'      # Latin letter ş → Latin letter ṣ
        }
        num_fixed = fixer.fix_file(KAB_OUTPUT, KAB_FIXED, fix_mapping)
        spinner.ok("✔")
        print(f"Fixed {num_fixed} lines in {KAB_OUTPUT}. Corrected file saved as '{KAB_FIXED}'.")
    
    print("All steps completed.")

if __name__ == "__main__":
    main()

