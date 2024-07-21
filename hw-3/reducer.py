#!/usr/bin/env python
"""reducer.py - Processes key-value pairs received from the mapper, where each key is a word 
and each value is a document ID where the word appeared. This script aggregates the document IDs 
for each word and outputs the word alongside the set of unique document IDs where the word was found.
The reducer reads lines of input from standard input, where each line has a format of 'word,document_id'.
The input lines are expected to be sorted by the word. The reducer uses this sorted order to efficiently
aggregate document IDs by using a set data structure, transitioning between different words as it processes
the input lines one-by-one.
"""

import sys

def main():
    current_word = None
    current_doc_ids = set()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            word, doc_id = line.split('\t', 1)
        except ValueError:
            continue

        if current_word == word:
            current_doc_ids.add(doc_id)
        else:
            if current_word is not None:
                print(f"{current_word}\t{','.join(current_doc_ids)}")
            
            current_word = word
            current_doc_ids = set([doc_id])

    if current_word is not None:
        print(f"{current_word}\t{','.join(current_doc_ids)}")

if __name__ == "__main__":
    main()
