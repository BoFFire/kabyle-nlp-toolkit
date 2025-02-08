#!/usr/bin/env python3
"""
Fixer Module

This module provides functions to fix a text file by replacing disallowed characters
with their allowed equivalents according to a mapping.

Usage as a command‐line tool:
    python3 fixer.py --input_file <input.txt> --output_file <output.txt>
"""

import unicodedata
import argparse

def fix_sentence(sentence, fix_mapping):
    """
    Normalize the sentence to NFC form and replace occurrences of disallowed characters
    using the provided mapping. The mapping is applied in order of decreasing key length
    (so that multi-character sequences are processed first).
    """
    fixed = unicodedata.normalize('NFC', sentence)
    # Process keys in order of decreasing length (longer keys first)
    for key in sorted(fix_mapping, key=lambda k: -len(k)):
        fixed = fixed.replace(key, fix_mapping[key])
    return fixed

def fix_file(input_file, output_file, fix_mapping):
    """
    Reads input_file line by line, applies fix_sentence to each line, and writes the result to output_file.
    Returns the number of lines that were changed.
    """
    fixed_count = 0
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:
        for line in infile:
            fixed_line = fix_sentence(line, fix_mapping)
            if fixed_line != line:
                fixed_count += 1
            outfile.write(fixed_line)
    return fixed_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix a text file using fix mappings.")
    parser.add_argument("--input_file", required=True, help="Input text file")
    parser.add_argument("--output_file", required=True, help="Output text file")
    args = parser.parse_args()

    # Define the fix mapping.
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

    count = fix_file(args.input_file, args.output_file, fix_mapping)
    print(f"Fixed {count} lines. Corrected file saved as '{args.output_file}'.")
