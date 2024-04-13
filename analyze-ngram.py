import os
import glob
import csv
from collections import defaultdict, Counter
from utils import *
from constants import *
 
def read_satoshi_text():
    with open(f'{DATA_DIR}/_satoshi/all-text.txt', 'r') as file:
        text = file.read()
        return text

satoshi_all_text = read_satoshi_text().lower()
satoshi_ngram1 = extract_ngrams_count(satoshi_all_text,1,False)
satoshi_ngram2 = extract_ngrams_count(satoshi_all_text,2,True)

def process_file(file_path):

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read().lower()

    folder_name = os.path.basename(os.path.dirname(file_path))
    file_name = os.path.basename(file_path)


    author_ngram1 = extract_ngrams_count(content,1,False)
    author_ngram2 = extract_ngrams_count(content,2,True)

    return {
       'source': folder_name,
       'filename': file_name,
       'characters': len(content),
       'ngram1_matches': sum((Counter(satoshi_ngram1.keys()) & Counter(author_ngram1.keys())).values()),
       'ngram2_matches': sum((Counter(satoshi_ngram2.keys()) & Counter(author_ngram2.keys())).values()),
    }

# Write the header and processed data to a CSV file
with open(f'{OUTPUT_DIR}/comparison-totals.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['source', 'filename','characters', 'ngram1_matches','ngram2_matches'])

    for file_path in glob.glob(os.path.join(DATA_DIR, '**/*.txt'), recursive=True):
        file_data = process_file(file_path)
        csvwriter.writerow([file_data['source'], file_data['filename'], file_data['characters'],file_data['ngram1_matches'],file_data['ngram2_matches']])