# pairing.py
from extractor import iter_sentences, iter_links

def build_sentence_dict(tar_filename, lang):
    """
    Iterates over the sentences file and builds a dictionary of sentences for a given language.
    Returns a dict mapping sentence_id -> text.
    """
    sentences = {}
    for sid, sentence_lang, text in iter_sentences(tar_filename):
        if sentence_lang == lang:
            sentences[sid] = text
    print(f"Found {len(sentences)} sentences in '{lang}'.")
    return sentences

def build_candidate_ids(links_tar_filename, ref_dict, other_lang):
    """
    Iterates over the links file and collects a set of sentence IDs that are paired with a sentence in ref_dict.
    The other sentence is assumed to be in other_lang.
    Returns a set of candidate sentence IDs.
    """
    candidate_ids = set()
    for sid1, sid2 in iter_links(links_tar_filename):
        if sid1 in ref_dict and sid2 not in ref_dict:
            candidate_ids.add(sid2)
        elif sid2 in ref_dict and sid1 not in ref_dict:
            candidate_ids.add(sid1)
    print(f"Identified {len(candidate_ids)} candidate sentence IDs for language '{other_lang}'.")
    return candidate_ids

def build_sentence_dict_from_ids(tar_filename, lang, id_set):
    """
    Iterates over the sentences file and builds a dictionary for sentences in a given language
    whose IDs are in id_set. Returns a dict mapping sentence_id -> text.
    """
    sentences = {}
    for sid, sentence_lang, text in iter_sentences(tar_filename):
        if sentence_lang == lang and sid in id_set:
            sentences[sid] = text
    print(f"Loaded {len(sentences)} sentences in '{lang}' from candidate IDs.")
    return sentences

def write_sentence_pairs(links_tar_filename, dict_a, dict_b, output_filename, a_first=True):
    """
    Iterates over the links file (streaming) and writes to output_filename
    the sentence pairs when one sentence is in dict_a and the other in dict_b.
    If a_first is True, output (dict_a[sid], dict_b[other]); otherwise, reverse.
    Duplicate pairs are skipped.
    """
    seen = set()  # Use sorted tuple of IDs to avoid duplicates.
    import csv
    with open(output_filename, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out, delimiter="\t")
        writer.writerow(["LangA", "LangB"])
        for sid1, sid2 in iter_links(links_tar_filename):
            if sid1 in dict_a and sid2 in dict_b:
                key = tuple(sorted([sid1, sid2]))
                if key in seen:
                    continue
                seen.add(key)
                if a_first:
                    writer.writerow([dict_a[sid1], dict_b[sid2]])
                else:
                    writer.writerow([dict_a[sid2], dict_b[sid1]])
            elif sid2 in dict_a and sid1 in dict_b:
                key = tuple(sorted([sid1, sid2]))
                if key in seen:
                    continue
                seen.add(key)
                if a_first:
                    writer.writerow([dict_a[sid2], dict_b[sid1]])
                else:
                    writer.writerow([dict_a[sid1], dict_b[sid2]])
    print(f"Wrote sentence pairs to {output_filename}.")
