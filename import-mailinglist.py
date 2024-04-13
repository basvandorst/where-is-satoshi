#####
# Extract all messages from mailing list archives and appends each post to the corresponding file of the author.
# Make sure each post is divided by the separator configured in `start_of_email_pattern`
#
# Input:
# D:\source-mailinglist\
#   - listA
#       - 2001.txt
#       - 2002.txt
#   - listB
#       - 2001.txt
#####

import os
import glob
import re
from constants import *
from utils import *

#start_of_email_pattern = re.compile(r"============================== START ==============================")
start_of_email_pattern = re.compile(r"^(From (.*))\n$")

def read_file(location):
    try:
        with open(location, 'r', encoding='utf-8') as file:
            return file.readlines()
    except UnicodeDecodeError:
        try:
            with open(location, 'r', encoding='latin-1') as file:
               return file.readlines()
        except UnicodeDecodeError as e:
            print(f"Couldn't read {file_path}. Error: {e}")
            return
    except (Exception) as err:
        print(err)

def save_email(directory, email_content):
    mail_address = clean_filename(extract_email_address(email_content))
    author = extract_name(email_content)
    date = extract_date(email_content)
    subject = extract_subject(email_content)
    print(f'File: {directory}/{mail_address}.txt')

    try:
        os.makedirs(f'{APP_DIR}/data/{directory}', exist_ok=True)
        filename = f'{APP_DIR}/data/{directory}/{mail_address}.txt'
        with open(filename, 'a', encoding='utf-8') as file:
            last_reply = extract_last_reply(email_content)
            # ~10 words
            if len(last_reply) < 50:
                return
            file.write(f"\n@_date: {date}\n")
            file.write(f"@_author: {author} \n")
            file.write(f"@_subject: {subject} \n")
            file.write(last_reply + '\n')

    except (Exception) as err:
        print(err)

def extract_and_save_emails(directory, content):
    current_email = []
    if content == None:
        return

    for line in content:
        if start_of_email_pattern.match(line) and current_email:
            save_email(directory, ''.join(current_email[1:]))
            current_email = []
        current_email.append(line)
    if current_email:
        save_email(directory, ''.join(current_email))

def start_import(path):
   pattern = os.path.join(path, '**', '*.txt')

   for file_path in sorted(glob.glob(pattern, recursive=True)):
       directory = os.path.basename(os.path.dirname(file_path))
       content = read_file(file_path)
       extract_and_save_emails(directory, content)


if __name__ == "__main__":
    start_import('D:\source-testlist')
