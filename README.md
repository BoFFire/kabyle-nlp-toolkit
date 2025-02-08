# Kabyle NLP Toolkit

This repository provides a lightweight, modular toolkit for processing the Tatoeba corpus specifically for Kabyle and English, including downloading, extracting, and generating a bilingual corpus; splitting the corpus into separate language files; and automatically fixing non‑standard characters in Kabyle text to conform to a standardized character set.

### Create and activate a virtual environment
```bash
python3 -m venv env
```
#### On Linux/Mac:

```bash
source env/bin/activate
```

### Getting Started

Clone the repository using:

```bash
git clone https://github.com/BoFFire/kabyle-nlp-toolkit.git
```

Go to :

```bash
cd kabyle-nlp-toolkit
```

### Install dependencies from requirements.txt
  
```bash
pip install -r requirements.txt
```

### Run the main corpus processing script for English-Kabyle:

```bash
python3 get_tatoeba_corpus.py --source_lang eng --target_lang kab
```

#### All output files are saved in the "corpus" directory by default.
Expected files:

```
corpus/
├── eng_kab_sentence_pairs.tsv
├── en.txt
├── kab.txt
└── kab_fixed.txt
```
- `corpus/eng_kab_sentence_pairs.tsv` : TSV file containing bilingual sentence pairs
- `corpus/en.txt`   : File with English sentences only
- `corpus/kab.txt`  : File with original Kabyle sentences
- `corpus/kab_fixed.txt` : File with fixed Kabyle sentences (non-standard characters replaced)
