import re
import os
import csv
import glob
from nltk.util import ngrams
from utils import *
from words import *
from constants import *


OUTPUT_FILE = f'{OUTPUT_DIR}/comparison.csv'
CHUNK_SIZE = 500

def read_satoshi_text():
    with open(f'{DATA_DIR}/_satoshi/all-text.txt', 'r') as file:
        text = file.read()
        return text

satoshi_all_text = read_satoshi_text().lower()
satoshi_ngram1 = extract_ngrams_count(satoshi_all_text,1,False)
satoshi_ngram2 = extract_ngrams_count(satoshi_all_text,2,True)
satoshi_ngram3 = extract_ngrams_count(satoshi_all_text,3,True)

def analyze_text_file(directory, filename):
    exact_file_path = f'{DATA_DIR}/{directory}/{filename}'

    print(f'Analyzing file: {directory}/{filename}')

    try:
        text = read_and_parse_file(exact_file_path)
        chunks = chunk_text_by_regex(text, TOKEN_REGEX, CHUNK_SIZE)
    except (Exception) as err:
        print(f'Error reading file: {directory}/{filename}')
        print(err)

    if(len(chunks) == 1):
        print(f'Skipping file:  {directory}/{filename}, size: {len(chunks)}')
        return

    for idx, chunk in enumerate(chunks):
        words_case_insensitive = extract_words(chunk)
        sentiment = analyze_sentiment(chunk)

        # from here, all counting/comparison is lowercase
        chunk = chunk.lower()
        words = extract_words(chunk)
        words_nostop = extract_words(chunk, False)
        words_nostop_unique = sorted(set(words_nostop))
        words_length_freq = count_words_lengths(words)

        author_ngram1 = extract_ngrams_count(chunk,1,False)
        author_ngram2 = extract_ngrams_count(chunk,2,True)
        author_ngram3 = extract_ngrams_count(chunk,3,True)

        author_british = filter_words(words_nostop_unique,satoshi_words_british)
        author_slang = filter_words(words_nostop_unique,satoshi_words_slang)
        author_typo = filter_words(words_nostop_unique,satoshi_words_typo)
        author_hyphen_1 = filter_words(words_nostop_unique,satoshi_words_hyphen_1)
        author_hyphen_2 = filter_words(words_nostop_unique,satoshi_words_hyphen_2)
        author_less_frequent = filter_words(words_nostop_unique,satoshi_less_frequent_words)

        punctuation_single_space = count_single_spaces(chunk)
        punctuation_double_space = count_double_spaces(chunk)
        punctuation_space_ratio = punctuation_double_space / punctuation_single_space if punctuation_single_space else 0

        stats = {
            'source': directory,
            'filename': filename,
            'chunks': len(chunks),
            'chunk' : idx +1,
            'words': len(words),
            'characters': len(chunk),
            'satoshi_ngram1_matches': sum((Counter(satoshi_ngram1.keys()) & Counter(author_ngram1.keys())).values()),
            'satoshi_ngram2_matches': sum((Counter(satoshi_ngram2.keys()) & Counter(author_ngram2.keys())).values()),
            'satoshi_ngram3_matches': sum((Counter(satoshi_ngram3.keys()) & Counter(author_ngram3.keys())).values()),
            'satoshi_john_burrow_delta': round(john_burrow_delta(satoshi_all_text, chunk),5),
            'satoshi_jaccard_similarity' : round(jaccard_similarity(satoshi_ngram1, author_ngram1),5),
            'satoshi_words_british': ','.join(author_british),
            'satoshi_words_slang': ','.join(author_slang),
            'satoshi_words_typo': ','.join(author_typo),
            'satoshi_words_typo': ','.join(author_typo),
            'satoshi_words_hyphen_1': ','.join(author_hyphen_1),
            'satoshi_words_hyphen_2': ','.join(author_hyphen_2),
            'satoshi_words_less_frequent': ','.join(author_less_frequent),
            'words_unique': len(sorted(set(words))),
            'words_nostop_count': len(words_nostop),
            'words_nostop_unique': len(words_nostop_unique),
            'words_with_hyphen_1' : count_words_with_hyphen(words_nostop_unique,1,1),
            'words_with_hyphen_2' : count_words_with_hyphen(words_nostop_unique,2,10),
            'words_fully_capitalized': count_words_capitalized(words_case_insensitive),
            'words_verb_ing': len(filter_words_by_regex(words_nostop_unique,r"ing$")),
            'words_verb_ed': len(filter_words_by_regex(words_nostop_unique,r"ed$")),
            'words_verb_ly': len(filter_words_by_regex(words_nostop_unique,r"ly$")),
            'punctuation_single_space': count_single_spaces(chunk),
            'punctuation_double_space': count_double_spaces(chunk),
            'punctuation_space_ratio': round(punctuation_space_ratio,3),
            'punctuation_commas': chunk.count(', '),
            'punctuation_dots': chunk.count('. '),
            'punctuation_exclamation': chunk.count('! '),
            'punctuation_question': chunk.count('? '),
            'punctuation_colons': chunk.count(':'),
            'punctuation_semicolons': chunk.count(';'),
            'readability_flesch_reading_ease': textstat.flesch_reading_ease(chunk),
            'readability_smog_index': textstat.smog_index(chunk),
            'readability_flesch_kincaid_grade': textstat.flesch_kincaid_grade(chunk),
            'readability_coleman_liau_index': textstat.coleman_liau_index(chunk),
            'readability_automated_readability_index': textstat.automated_readability_index(chunk),
            'readability_dale_chall_readability_score': textstat.dale_chall_readability_score(chunk),
            'readability_linsear_write_formula': textstat.linsear_write_formula(chunk),
            'readability_gunning_fog': textstat.gunning_fog(chunk),
            'sentence_count': sentences_count(chunk),
            'sentence_word_count': round(sentence_word_counts(chunk),3),
            'sentence_word_median': sentence_word_median(chunk),
            'sentiment_subjectivity': round(sentiment['subjectivity'],3),
            'sentiment_polarity': round(sentiment['polarity'],3)
        }
        for pronoun, count in count_personal_pronouns(words).items():
            stats[f'personal_pronouns_{pronoun}'] = count

        for length in range(1, 16):
            stats[f'word_length_frequency_{length}'] = (words_length_freq[length] if length in words_length_freq  else 0)

        write_chunk_analysis_to_file(stats)


def write_chunk_analysis_to_file(result):
    file_exists_and_nonempty = os.path.isfile(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0

    with open(OUTPUT_FILE, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        if not file_exists_and_nonempty:
            writer.writerow(result.keys())
        writer.writerow(result.values())


def read_and_parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        text = re.sub(r"^-----\nSource: (.+?)\nName: (.+?)\nDate: (.+?)\n-----", '', text, flags=re.MULTILINE | re.IGNORECASE)

        # unique lines only
        text = set(text.splitlines())
        text = '\n'.join(text)
        # hacky way to keep the double spaces
        text = re.sub(r'(\.|\?|\!)  ([a-zA-Z0-9])', r'\1 @DOUBLE@ \2', text)
        text = ' '.join(text.split()).replace('@DOUBLE@','')
        return text

def chunk_text_by_regex(text, pattern, nr_matches):
    prev = 0
    chunks = []
    for i, match in enumerate(re.finditer(pattern, text), start=1):
        if i % nr_matches == 0:
            chunks.append(text[prev:match.start()].strip())
            prev = match.start()
    if prev < len(text):
        chunks.append(text[prev:].strip())
    return chunks

def start_analyzer():
   data_dir = f'{APP_DIR}/data/'
   pattern = os.path.join(data_dir, '**', '*.txt')

   for file_path in sorted(glob.glob(pattern, recursive=True)):
       folder_name = os.path.basename(os.path.dirname(file_path))
       file_name = os.path.basename(file_path)
       analyze_text_file(folder_name, file_name)


if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    start_analyzer()
