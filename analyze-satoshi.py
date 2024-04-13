import os
import collections
import csv
from constants import *
from utils import *
from nltk.tokenize import sent_tokenize

def write_to_file(words, output_filename):
    with open(output_filename, 'w') as txtfile:
        for word in words:
            txtfile.write(word + '\n')

def write_counts_to_file(words_count, output_filename):
    with open(output_filename, 'w') as txtfile:
        for word, count in words_count.most_common():
            txtfile.write(f"{count} - {word}\n")

if __name__ == "__main__":
    with open(DATA_DIR + '/_satoshi/all-text.txt', 'r') as file:
        text = file.read().lower()

    tokens = extract_words(text, True)
    write_counts_to_file(filter_words_with_hyphen_count(tokens,1,1), OUTPUT_DIR + '/hyphen/1.txt')
    write_counts_to_file(filter_words_with_hyphen_count(tokens,2,10), OUTPUT_DIR + '/hyphen/2+.txt')

    write_counts_to_file(count_words(filter_words_by_regex(tokens,r"ing$")), OUTPUT_DIR + '/verb-suffix/ing.txt')
    write_counts_to_file(count_words(filter_words_by_regex(tokens,r"ly$")), OUTPUT_DIR + '/verb-suffix/ly.txt')
    write_counts_to_file(count_words(filter_words_by_regex(tokens,r"ed$")), OUTPUT_DIR + '/verb-suffix/ed.txt')

    write_to_file(extract_sentences(text), OUTPUT_DIR + '/sentences.txt')

    for ngram in range(1, 6):
        write_counts_to_file(extract_ngrams_count(text,ngram, True), OUTPUT_DIR + f"/n-gram/{ngram}.txt")
        write_counts_to_file(extract_ngrams_count(text,ngram, False), OUTPUT_DIR + f"/n-gram/{ngram}-no-stopwords.txt")

    write_counts_to_file(extract_ngrams_count(text,ngram, True), OUTPUT_DIR + f"/n-gram/{ngram}.txt")
    write_counts_to_file(extract_ngrams_count(text,ngram, False), OUTPUT_DIR + f"/n-gram/{ngram}-no-stopwords.txt")

    write_to_file(spell_check(extract_words(text), "en_US"), OUTPUT_DIR + '/spellcheck/US.txt')
    write_to_file(spell_check(extract_words(text), "en_GB"), OUTPUT_DIR + '/spellcheck/GB.txt')
