import os
import collections
import csv
import nltk
import re
import textstat
import json
import statistics
import language_tool_python
import enchant
import numpy as np
from constants import *
from email.utils import parsedate_to_datetime
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize,sent_tokenize,RegexpTokenizer
from nltk.util import ngrams
from collections import defaultdict
from textblob import TextBlob
from collections import Counter
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
from nltk.probability import FreqDist

wnl = WordNetLemmatizer()
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('cmudict')
stop_words = set(stopwords.words('english'))

def extract_email_address(header):
    match = re.search(r'[\w\.-]+@[\w\.-]+', header)
    return match.group(0) if match else 'unknown_email'
    return "unknown_email"

def extract_name(header):
    match = re.search(r'\((.*?)\)', header)
    return match.group(1) if match else 'unknown_name'

def extract_subject(email_content):
    header_pattern = re.compile(r"Subject: (.+?)$", re.MULTILINE)
    match_sender = header_pattern.search(email_content)
    if match_sender:
        return match_sender.group(1)
    return "unknown_subject"

def extract_date(email_content):
    date_header_pattern = re.compile(r"Date: (.+)$", re.MULTILINE)
    match_date = date_header_pattern.search(email_content)
    if match_date:
        try:
            date_str = match_date.group(1)
            return parsedate_to_datetime(date_str).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "unknown_date"
    return "unknown_date"

def extract_sentences(text):
    text = re.sub(r'\n', ' ', text, flags=re.MULTILINE)
    sentences = sent_tokenize(text)

    return  sorted(set(sentences))

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = {
        'polarity': blob.sentiment.polarity,
        'subjectivity': blob.sentiment.subjectivity
    }
    return sentiment

def sentences_count(text):
    sentences = sent_tokenize(text)
    return len(sentences)

def sentence_word_counts(text):
    sentences = sent_tokenize(text)
    word_counts = [len(word_tokenize(sentence)) for sentence in sentences]
    return sum(word_counts) / len(sentences) if sentences else 0

def sentence_word_median(text):
    sentences = sent_tokenize(text)
    word_counts = [len(word_tokenize(sentence)) for sentence in sentences]
    return statistics.median(word_counts) if sentences else 0

def penn_to_morphy(penntag):
    """ https://stackoverflow.com/questions/49354691/nltk-how-to-lemmatize-taking-surrounding-words-into-context """
    morphy_tag = {'NN':'n', 'JJ':'a', 'VB':'v', 'RB':'r'}
    return morphy_tag.get(penntag[:2], 'n')

def lemmatize_words(words):
    text = ' '.join(words)
    tokenized_and_tagged = pos_tag(word_tokenize(text))
    lemmatized = [wnl.lemmatize(word.lower(), pos=penn_to_morphy(tag)) for word, tag in tokenized_and_tagged]
    return lemmatized

def count_personal_pronouns(words):
    """Counts personal pronouns in a list of words, considering lemmatization."""
    pronouns = {
        "i": 0, "you": 0, "he": 0, "she": 0, "it": 0,
        "we": 0, "they": 0, "me": 0, "him": 0, "her": 0,
        "us": 0, "them": 0, "myself": 0, "yourself": 0
    }
    lemmatized_words = lemmatize_words(words)
    for word in lemmatized_words:
        if word in pronouns:
            pronouns[word] += 1
    return pronouns

def filter_words(words, filter):
    return [word for word in words if word in filter]

def filter_words_by_regex(words, regex):
    return [word for word in words if re.search(regex, word)]

def count_words(words):
    return collections.Counter(words)

def exclude_stopwords(words):
    return [word for word in words if word not in stop_words]

def extract_words(text, stopwords=True):
    tokenizer = RegexpTokenizer(TOKEN_REGEX)
    words = tokenizer.tokenize(text)
    if not stopwords:
        words = exclude_stopwords(words)

    return words

def count_words_lengths(words, max_length=15):
    word_lengths = [len(word) if len(word) <= max_length else max_length for word in words]
    freq_dist = FreqDist(word_lengths)
    total_words = len(words)
    percentage_dist = {length: round(((count / total_words) * 100),2) for length, count in freq_dist.items()}
    return percentage_dist

def filter_words_with_hyphen_count(words, min, max):
    words = [word for word in words if min <= word.count('-') <= max]
    return collections.Counter(words)
    # merge

def count_words_with_hyphen(words, min, max):
    return sum(1 for word in words if word.count('-') >= min and word.count('-') <=max)

def count_words_capitalized(words):
    return sum(word.isupper() for word in words)

def count_single_spaces(text):
    matches = re.findall(r'(\.|\?|\!) [a-zA-Z0-9]', text)
    return len(matches)

def count_double_spaces(text):
    matches = re.findall(r'(\.|\?|\!)  [a-zA-Z0-9]', text)
    return len(matches)

def extract_ngrams_count(text, n=2, stopwords=False):
    text = re.sub(r'\n', ' ', text, flags=re.MULTILINE)
    tokenizer = RegexpTokenizer(TOKEN_REGEX)
    words = tokenizer.tokenize(text)
    if not stopwords:
        words = exclude_stopwords(words)

    n_grams = ngrams(words, n)
    n_grams_as_strings = (' '.join(n_gram) for n_gram in n_grams)
    n_grams_counts = collections.Counter(n_grams_as_strings)

    return n_grams_counts

def jaccard_similarity(ngram1, ngram2):
    set1 = set(ngram1.keys())
    set2 = set(ngram2.keys())

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    jaccard_similarity = intersection / union
    return jaccard_similarity

def john_burrow_delta(original, chunk):
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform([original, chunk])
    features = vectorizer.get_feature_names_out()

    frequencies = X.toarray()

    author_freq = frequencies[0]
    chunk_freq = frequencies[1]

    mean_author_freq = np.mean(author_freq)
    std_author_freq = np.std(author_freq)

    delta = np.mean(np.abs(chunk_freq - author_freq) / std_author_freq) if std_author_freq > 0 else 0
    return delta

def spell_check(words, locale):
    checker = enchant.Dict(locale)

    results = []
    for word in words:
        if not checker.check(word):
            suggestions = checker.suggest(word)

            if len(suggestions) > 0 and word.lower() not in [s.lower() for s in suggestions]:
                formatted_suggestions = ', '.join(suggestions[:3])
                results.append(f"{word} - {formatted_suggestions}")

    return results

def clean_filename(name):
    name = re.sub(r'[^\w\d\.-@]', '', name)
    name = name.strip(" '\"")
    name = re.sub(r'\W+', '_', name).lower()
    return name


def extract_last_reply(text):
    try:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text()
    except Exception:
        pass

    text = re.sub(r"^(Subject:(.*))\n(.*)$", '\n', text, flags=re.MULTILINE)
    text = re.sub(r"^(Date:|From|From:|To:|Cc:|In-Reply-To:|Message-ID:|MIME-Version:|Content-Type:)(.*)$", '\n', text, flags=re.MULTILINE)
    text = re.sub(r"(?s)^-------------- next part --------------(\r\n|\r|\n)(.*)", '\n', text, flags=re.MULTILINE)
    text = re.sub(r'^>(.*)$', '\n', text, flags=re.MULTILINE)
    text = re.sub(r'^\|(.*)$', '\n', text, flags=re.MULTILINE)
    text = re.sub(r'^\/(.*)$', '\n', text, flags=re.MULTILINE)
    text = re.sub(r'^\|(.*)$', '\n', text, flags=re.MULTILINE)
    text = re.sub(r'(^\s*[\r\n|\r|\n]+|^\t.*?$|^>.*?$)', '', text, flags=re.MULTILINE)
    text = re.sub(r"(?s)^-------------- next part --------------(.*)", '', text, flags=re.MULTILINE)
    text = re.sub(r"(?s)^---------------------------------------------------------------------(.*)", '', text, flags=re.MULTILINE)
    text = re.sub(r"^-----begin pgp signed message-----", '', text)


    text = re.sub(r"^-----BEGIN PGP SIGNED MESSAGE-----", '', text)
    text = re.sub(r"(-----BEGIN PGP SIGNATURE-----\n)([\s\S]*?)(\n-----END PGP SIGNATURE-----)", '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"(-----.*?message.*?-----\n)([\s\S]*?)(\n-----.*?message.*?-----)", '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"(--------------.*?\n)([\s\S]*?)(\n--------------.*?)", '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^----- end forwarded message -----", '', text, flags=re.MULTILINE | re.IGNORECASE)

    text = re.sub(r"(?s)^-- (.*)", '', text, flags=re.MULTILINE)
    text = re.sub(r"(?s)^- --(.*)", '', text, flags=re.MULTILINE)
    text = re.sub(r"^--(.*)", '', text) # sigs

    text = re.sub(r"(?s)^Content-Transfer-Encoding(.*)", '', text, flags=re.MULTILINE | re.IGNORECASE)


    text = re.sub(r"^d{4}-\d{2}-\d{2}(.*)$", '', text)
    text = re.sub(r"^(.*)(wrote|writing|writes):", '', text, flags=re.MULTILINE)
    text = re.sub(r"^(.*)(wrote|writing|writes)(.+)(AM|PM):", '', text)
    text = re.sub(r"^On\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun|\d{2})(.*)", '', text)

    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','',text)
    text = re.sub(r'#([^\s]+)', '', text)
    text = re.sub('@[^\s]+','',text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^[^\s]*$\n','',text, flags=re.MULTILINE | re.IGNORECASE)

    text = re.sub(r'(\r\n|\r|\n)(\r\n|\r|\n)',' \n',text)
    text = re.sub(r'(\r\n|\r|\n)(\r\n|\r|\n)',' \n',text)
    text = re.sub(r' (\r\n|\r|\n)',' ',text)

    text = text.strip()

    return text