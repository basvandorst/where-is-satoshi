#####
# Additional script for the `import-reddit-db.py`, for some reason i reached some query limits.
# Workaround: run query (import-reddit-db.py) --> save the results temporary table --> store as CSV in a bucket.
# The downloaded CSV files could be used for this script.
#####
import re
import csv
import sys
from utils import clean_filename

from constants import APP_DIR
csv.field_size_limit(100000000)

# Query export to CSV
for i in range(0, 10):
    filepath = f'd:/reddit-csv/00000000000{i}.csv'
    with open(filepath, 'r', encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file, delimiter=';', fieldnames=['author', 'comments'])
        for row in reader:
            author = row['author'] if row['author'] else "unknown"
            filename = f'{APP_DIR}/data/reddit/{clean_filename(author)}.txt'
            print(f'Writing file: {filename}')

            comments = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', '', row['comments'])
            comments = re.sub(r'#([^\s]+)', '', comments)
            comments = re.sub(r'@(?!\_)[^\s]+','',comments, flags=re.MULTILINE | re.IGNORECASE)
            comments = re.sub('\/(u|r)\/(\S+\s+)', '', comments, flags=re.MULTILINE | re.IGNORECASE)
            comments = re.sub(r'^[^\s]*$\n', '', comments, flags=re.MULTILINE | re.IGNORECASE)
            comments = re.sub(r'^&gt;.*$', '\n', comments, flags=re.MULTILINE)
            comments = re.sub(r'\\n', '\n', comments, flags=re.MULTILINE)

            with open(filename, 'w', encoding="utf-8") as output_file:
                output_file.write(f"@_author: {row['author']}\n") # once the name which is not stripped
                output_file.write(comments)