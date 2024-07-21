#!/usr/bin/env python
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
        
        words = re.findall(r'\w+', text.lower())
        
        for word in words:
            print(f"{document_id}\t{word}\t1")

if __name__ == "__main__":
    main()
