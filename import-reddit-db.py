#####
# This script will excecute a query (all Reddit comments, BigQuery) and stores it in /data/reddit
# Change the location of the key- and projectfile and make sure your service account has access to run queries.
# Note: query cost you a few bucks: "This query will process 1.21 TB when run"
#####

import re

from utils import clean_filename
from constants import *
from google.cloud import bigquery
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file('key.json')
project_id = 'xxxx'

client = bigquery.Client(credentials=credentials, project=project_id)

query = """
SELECT
  LOWER(author) as author,
  STRING_AGG(
    CONCAT(
      '@_date: ', FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', TIMESTAMP_SECONDS(created_utc)),
      '\n',
      body
    ),
    '\n\n'
  ) as comments,
FROM `fh-bigquery.reddit_comments.20*`
WHERE subreddit = 'Bitcoin'
GROUP BY LOWER(author)
HAVING LENGTH(comments) > 1500
ORDER BY LOWER(author)
"""

query_job = client.query(query)
results = query_job.result()

for row in results:
    author = row.author if row.author else "unknown"
    filename = f'{APP_DIR}/data/reddit/{clean_filename(author)}.txt'

    comments = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','',row.comments)
    comments = re.sub(r'#([^\s]+)', '', comments)
    comments = re.sub(r'@(?!\_)[^\s]+','',comments, flags=re.MULTILINE | re.IGNORECASE)
    comments = re.sub('\/(u|r)\/(\S+\s+)', '', comments, flags=re.MULTILINE | re.IGNORECASE)
    comments = re.sub(r'^[^\s]*$\n','',comments, flags=re.MULTILINE | re.IGNORECASE)
    comments = re.sub(r'^&gt;.*$', '\n', comments, flags=re.MULTILINE)

    with open(filename, 'w', encoding="utf-8") as file:
        output_file.write(f"@_author: {row.author}\n") # once the name which is not stripped
        output_file.write(comments)