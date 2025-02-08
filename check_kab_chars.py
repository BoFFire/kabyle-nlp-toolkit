#!/usr/bin/env python3
"""
Check Kabyle Sentences for Non-Standard Characters and Optionally Fix Them

This tool reads a text file containing Kabyle sentences (one per line) and
checks each sentence for any alphabetical characters that are not in the
allowed standardized set. Numbers, punctuation, and whitespace are ignored.

Allowed characters (case-insensitive):
['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t',
 'u','v','w','x','y','z','č','ḍ','ǧ','ḥ','ɣ','ṛ','ṣ','ṭ','ɛ','ẓ']

If the --fix flag is provided, the tool will automatically replace known disallowed characters
according to the following mapping (applied in order of decreasing key length):
  - "ţţ" → "tt"      (two consecutive ţ's → "tt")
  - "țț" → "tt"      (two consecutive ț's → "tt")
  - ϵ    → ɛ        (Greek lunate epsilon to Latin small open e)
  - ε    → ɛ        (Greek small epsilon to Latin small open e)
  - γ    → ɣ        (Greek small gamma to Latin small gamma)
  - Γ    → Ɣ        (Greek capital Gamma to Latin capital Ɣ)
  - Σ    → Ɛ        (Greek capital Sigma to Latin capital Ɛ)
  - Ԑ    → Ɛ        (Cyrillic letter Ԑ to Latin capital Ɛ)
  - ğ    → ǧ        (Latin letter ğ to Latin letter ǧ)
  - ş    → ṣ        (Latin letter ş to Latin letter ṣ)

Usage examples:
    Check sentences without fixing:
        python3 check_kab_chars.py --input_file kab.txt

    Check and fix (writes corrected sentences to kab_fixed.txt by default):
        python3 check_kab_chars.py --input_file kab.txt --fix

    Or specify a custom output file:
        python3 check_kab_chars.py --input_file kab.txt --fix --fixed_output my_kab.txt
"""

import argparse
import unicodedata

def find_disallowed(sentence, allowed_set):
    """
    For each character in the sentence that is alphabetic, check if its lowercase 
    version is in allowed_set. Return a set of all characters (in their original form)
    that are not allowed.
    """
    disallowed = set()
    for char in sentence:
        if char.isalpha() and (char.lower() not in allowed_set):
            disallowed.add(char)
    return disallowed

def fix_sentence(sentence, fix_mapping):
    """
    Normalize the sentence to NFC form and replace occurrences of disallowed characters
    using the provided mapping. The mapping is applied in order of decreasing key length
    so that multi-character sequences are processed first.
    """
    fixed = unicodedata.normalize('NFC', sentence)
    # Process keys in order of decreasing length (longer keys first)
    for key in sorted(fix_mapping, key=lambda k: -len(k)):
        fixed = fixed.replace(key, fix_mapping[key])
    return fixed

def main():
    parser = argparse.ArgumentParser(
        description="Check Kabyle sentences for non-standard characters and optionally fix them."
    )
    parser.add_argument("--input_file", default="kab.txt",
                        help="Input text file with one Kabyle sentence per line (default: kab.txt)")
    parser.add_argument("--fix", action="store_true",
                        help="Automatically fix known disallowed characters and output a corrected file.")
    parser.add_argument("--fixed_output", default=None,
                        help="Output file for fixed sentences (default: input filename with '_fixed' appended)")
    args = parser.parse_args()

    # Allowed characters (lowercase) as provided.
    allowed_chars = [
        'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t',
        'u','v','w','x','y','z','č','ḍ','ǧ','ḥ','ɣ','ṛ','ṣ','ṭ','ɛ','ẓ'
    ]
    allowed_set = set(allowed_chars)
    
    problematic_sentences = 0
    total_sentences = 0
    
    with open(args.input_file, "r", encoding="utf-8") as infile:
        for i, line in enumerate(infile, start=1):
            sentence = line.strip()
            if not sentence:
                continue
            total_sentences += 1
            disallowed = find_disallowed(sentence, allowed_set)
            if disallowed:
                problematic_sentences += 1
                sorted_disallowed = sorted(disallowed)
                print(f"Line {i}: {sentence}")
                print(f"  Disallowed characters: {', '.join(sorted_disallowed)}\n")
    
    print(f"Checked {total_sentences} sentences. Found {problematic_sentences} sentence(s) with disallowed characters.")
    
    if args.fix:
        # Mapping for fixes. Multi-character keys come first.
        fix_mapping = {
            'ţţ': 'tt',   # Two consecutive ţ's → "tt"
            'țț': 'tt',   # Two consecutive ț's → "tt"
            'ϵ': 'ɛ',     # Greek lunate epsilon → Latin small open e
            'ε': 'ɛ',     # Greek small epsilon → Latin small open e
            'γ': 'ɣ',     # Greek small gamma → Latin small gamma
            'Γ': 'Ɣ',     # Greek capital Gamma → Latin capital Ɣ
            'Σ': 'Ɛ',     # Greek capital Sigma → Latin capital Ɛ
            'Ԑ': 'Ɛ',     # Cyrillic letter Ԑ → Latin capital Ɛ
            'ğ': 'ǧ',     # Latin letter ğ → Latin letter ǧ
            'ş': 'ṣ'      # Latin letter ş → Latin letter ṣ
        }
        # Determine output filename.
        if args.fixed_output:
            output_file = args.fixed_output
        else:
            if '.' in args.input_file:
                base, ext = args.input_file.rsplit('.', 1)
                output_file = f"{base}_fixed.{ext}"
            else:
                output_file = f"{args.input_file}_fixed.txt"
        
        fixed_count = 0
        with open(args.input_file, "r", encoding="utf-8") as infile, \
             open(output_file, "w", encoding="utf-8") as outfile:
            for line in infile:
                fixed_line = fix_sentence(line, fix_mapping)
                if fixed_line != line:
                    fixed_count += 1
                outfile.write(fixed_line)
        print(f"Fixed {fixed_count} lines. Corrected file saved as '{output_file}'.")

if __name__ == "__main__":
    main()

