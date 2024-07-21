#!/usr/bin/env python
import sys
from collections import defaultdict, Counter

K = 3

def main():
    current_document_id = None
    word_counts = defaultdict(int)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            document_id, word, count = line.split('\t')
            count = int(count)
        except ValueError:
            continue

        if current_document_id == document_id:
            word_counts[word] += count
        else:
            if current_document_id is not None:
                top_k_words = Counter(word_counts).most_common(K)
                for word, count in top_k_words:
                    print(f"{current_document_id}\t{word}\t{count}")

            current_document_id = document_id
            word_counts = defaultdict(int)
            word_counts[word] = count

    if current_document_id is not None:
        top_k_words = Counter(word_counts).most_common(K)
        for word, count in top_k_words:
            print(f"{current_document_id}\t{word}\t{count}")

if __name__ == "__main__":
    main()
