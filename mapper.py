#!/usr/bin/env python
"""mapper.py - This mapper script reads text input from standard input, in the format "document_id,text".
It processes each line to extract words and emits each word along with the document ID it appeared in. 
Each word is emitted only once per document to ensure uniqueness.
"""
import sys
import re

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            document_id, text = line.split(',', 1)
        except ValueError:
            continue
        
        unique_words = set()
        words = re.findall(r'\w+', text.lower())
        
        for word in words:
            if word not in unique_words:
                unique_words.add(word)
                print(f"{word}\t{document_id}")

if __name__ == "__main__":
    main()
