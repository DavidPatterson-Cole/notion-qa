from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import email
import base64
import json
from langchain.text_splitter import CharacterTextSplitter
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle
from bs4 import BeautifulSoup
import re


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

skipped_mimetypes = ['text/calendar', 'image/png', 'image/jpeg', 'application/ics', 'application/pdf', 'image/gif', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

# EXAMPLE: Part 1 - "Hi", Part 2 - "Hi", Part 3 - [Part 1 - "Hello", Part 2 - "Hello"]
# def nested_parts(item, full_body):
#   # partial_body = ''
#   for i, part in enumerate(item['payload']['parts']):
#     print(f'\nPART{i}\n')
#     if 'multipart/alternative' in part['mimeType']:
#       result = nested_parts(part, full_body)
#       full_body.append(result)
#     else:
#       body = part['body']['data']
#       body = base64.urlsafe_b64decode(body.encode('UTF-8'))
#       body = body.decode('utf-8')
#       if part['mimeType'] == 'text/plain':
#         print('part[\'mimeType\']', part['mimeType'])
#         print(f'Plain: {body=}')
#         # partial_body += body
#         full_body.append(body)
#       elif part['mimeType'] == 'text/html':
#         print(f'HTML: {body=}')
#         print('part[\'mimeType\']', part['mimeType'])
#         soup = BeautifulSoup(body, 'html.parser')
#         soup_text = soup.get_text()
#         full_body.append(body)
#         # partial_body += soup_text
#       else:
#         print('MISSED - part[\'mimeType\']', part['mimeType'])
#   return full_body



def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
      creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
          flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
          creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        email_address = service.users().getProfile(userId='me').execute()['emailAddress']
        print(f'{email_address=}')
        num_requested_emails = 3000
        email_count = 500
        email_list_response = service.users().messages().list(userId='me', maxResults=500, q="after:2022/02/01 before:2022/02/04").execute()
        email_list = email_list_response['messages']
        # print(f'{email_list=}')
        nextPageToken = None
        try:
          nextPageToken = email_list_response['nextPageToken']
        except:
          nextPageToken = None
          print('No next page token')
          pass
        while email_count < num_requested_emails and nextPageToken:
            email_list_response = service.users().messages().list(userId='me', maxResults=500, q="after:2022/02/01 before:2022/02/04", pageToken=nextPageToken).execute()
            # print(email_list_response['messages'])
            email_list.extend(email_list_response['messages'])
            try: 
              nextPageToken = email_list_response['nextPageToken']
            except:
              nextPageToken = None
              print('No next page token')
            email_count += 500
        results = []
        # print(f'{email_list}')
        for email in email_list:
          if email['id']:
            results.append(service.users().messages().get(userId='me', id=email['id']).execute())
        print(f'{len(results)=}')
        # snippets = []
        # for result in results:
        #   try:
        #     snippets.append(result['snippet'])
        #   except:
        #     print(f'{result=}')
        # print(f'{snippets=}')
        metadatas = []
        docs = []
        skipped_emails = 0
        missed_parts = 0
        long_split_list = []
        for item in results:
          for header in item['payload']['headers']:
            if header['name'] == 'Subject':
              subject = header['value']
            if header['name'] == 'From':
              email_from = header['value']
            if header['name'] == 'Received':
              received_date = header['value']
            if header['name'] == 'Date':
              date = header['value']
            # replace this section with the directly accesible mimetype 
            if header['name'] == 'Content-Type':
              part_mimetype = header['value']
              # print(f'{part_mimetype=}')
          if 'multipart' in part_mimetype:
            # full_body = nested_parts(item, [])
            # parts = item['payload']['parts']
            full_body = []
            parts_list = [item['payload']]
            while True:
              new_parts = []
              # print(f'{len(parts_list)=}')
              for parts_element in parts_list:
                # print(f'{parts_element=}')
                parts = parts_element['parts'] # removed payload
                parent_mimetype = parts_element['mimeType'] # removed payload
                # print(f'{parent_mimetype=}')
                for i, part in enumerate(parts):
                  # print(f'\nPART{i}\n')
                  # print(f'{part=}')
                  if 'multipart' in part['mimeType']:
                    # print('Nested multipart')
                    new_parts.append(part)
                  else:
                    if part['mimeType'] in skipped_mimetypes:
                      # print(f'{subject=}')
                      # print(f'{part=}')
                      continue
                      # print('SKIPPED - part[\'mimeType\']', part['mimeType'])
                    elif parent_mimetype == 'multipart/alternative':
                      try:
                        body = part['body']['data']
                        body = base64.urlsafe_b64decode(body.encode('UTF-8'))
                        body = body.decode('utf-8')
                      except KeyError as e:
                          print(f"KeyError: {e}")
                          print(f'{subject=}')
                          print(part)
                      if 'text/html' in part['mimeType']:
                        # print(f'HTML: {body=}')
                        # print('part[\'mimeType\']', part['mimeType'])
                        soup = BeautifulSoup(body, features='lxml')
                        soup_text = soup.get_text()
                        # print(f'{soup_text=}')
                        full_body.append(soup_text)
                        # partial_body += soup_text
                      else:
                        continue
                        # print('SKIPPED multipart/alternative - part[\'mimeType\']', part['mimeType'])
                    else: 
                      # print(f'{subject=}')
                      # print(f'{part=}')
                      try:
                          body = part['body']['data']
                          body = base64.urlsafe_b64decode(body.encode('UTF-8'))
                          body = body.decode('utf-8')
                      except KeyError as e:
                          print(f"KeyError: {e}")
                          print(f'{subject=}')
                          print(part)
                      if 'text/plain' in part['mimeType']:
                        # print('part[\'mimeType\']', part['mimeType'])
                        # print(f'Plain: {body=}')
                        # partial_body += body
                        full_body.append(body)
                      elif 'text/html' in part['mimeType']:
                        # print(f'HTML: {body=}')
                        # print('part[\'mimeType\']', part['mimeType'])
                        soup = BeautifulSoup(body, features='lxml')
                        soup_text = soup.get_text()
                        full_body.append(soup_text)
                        # partial_body += soup_text
                      else:
                        missed_parts += 1
                        # print(f'{subject=}')
                        continue
                        # print('MISSED - part[\'mimeType\']', part['mimeType'])
              parts_list = new_parts
              if len(parts_list) == 0:
                break
            # print(f'{subject=}')
            full_body = ''.join(full_body)
            # print(f'Multipart-{full_body=}')
          else:
            full_body = item['payload']['body']['data']
            full_body = base64.urlsafe_b64decode(full_body.encode('UTF-8'))
            full_body = full_body.decode('utf-8')
            # print(f'{full_body=}')
            if 'text/plain' in part_mimetype:
              continue
            elif 'text/html' in part_mimetype:
              soup = BeautifulSoup(full_body, 'lxml')
              soup_text = soup.get_text()
              full_body = soup_text
            else:
              print(f'{subject=}')
              print(f'{part_mimetype=}')
              missed_parts += 1
              continue
              # print('MISSED - part[\'mimeType\']', part['mimeType'])
            # print(f'{subject=}')
            full_body = ''.join(full_body)
            # print(f'Singlepart-{full_body=}')
          # Need to change this code now that full body is an array
          if not full_body or len(full_body) <20:
            skipped_emails +=1
          if len(full_body) > 20:
            # print('--------SPLIT--------')
            splits = text_splitter(full_body, long_split_list)
            # longest_element = max(splits, key=len)
            # print(f'{len(longest_element)=}')
            new_splits = []
            sources = []
            for i, split in enumerate(splits):
              # print(f'{split=}')
              # new_splits.append('SUBJECT: ', subject + '|' + 'EMAIL_FROM: ', email_from + '|' + 'RECEIVED DATE: ', json.dumps(received_date) + '|' + 'CONTENT: ', split)
              # print(f'{subject=}')
              # print(f'{split=}')
              concat_split = 'SUBJECT: ' + subject + '|' + 'EMAIL_FROM: ' + email_from + '|' + 'RECEIVED DATE: ' + date + '|' + 'CONTENT: ' + split
              if len(concat_split) > 5000:
                print(concat_split[0:250])
              new_splits.append(concat_split)
              email_id = item['id']
              sources.append({"source": subject+str(i), "url": f'https://mail.google.com/mail?authuser={email_address}#all/{email_id}'})
            docs.extend(new_splits)
            metadatas.extend(sources)

        print(f'{missed_parts=}')
        print(f'{skipped_emails=}')
        print(f'{len(long_split_list)=}')
        if len(long_split_list):
          print(f'{max(long_split_list)=}')
        print(f'{len(docs)=}')
        print(docs[0:3])
        print(metadatas[0:3])
        for doc in docs:
          if len(doc) > 5000:
            # print(len(doc))
            # print(doc[0:150])
            continue

        store = FAISS.from_texts(docs, OpenAIEmbeddings(), metadatas=metadatas)
        # This creates an index out of the store data structure
        if os.path.exists('faiss'):
          existing_index = FAISS.load_local('faiss', OpenAIEmbeddings())
          existing_index.add_texts(texts=docs, metadatas=metadatas)

          # Should probably stick to using FAISS (langchain) vs intermingling with faiss
          print(f'{os.getcwd()=}')
          existing_index.save_local('faiss')
        else:
          store.save_local('faiss')
        store.index = None

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


def text_splitter(text, long_split_list):
    # print(text)
    chunks = []
    chunk = ""
    # naive_split = text.split(". | , | \n | ; | :")
    text = re.sub(r'[\r,\xa0,\u200c,\t]', ' ', text)
    # naive_split = re.split(r"[,.;:\n](?=[^\s])", text)
    naive_split = re.split(r"([,.?;:\n])", text)

    # print(naive_split)
    # print(len(naive_split))
    for split in naive_split:
      # print(split)
      
      if len(split) >= 4000:
        # print(split)
        long_split_list.append(len(split))
        # print(split)
      if len(chunk + split) < 4000:
        # print('here')
        chunk += split
        # print(chunk)
      else:
        # print(chunk)
        chunks.append(chunk)
        chunks.append(split) # this is risky because it could be over 400
        chunk = ""
    chunks.append(chunk)
    # print(chunks)
    return chunks

if __name__ == '__main__':
    main()




          # This currently doesn't work because each part can have multipart/alernative so it can be infinitely nested
          # while true: 
            # for loop over parts and check if any of them are multipart/alternative
              # if so call the function with that part


          # if 'multipart/alternative' in part_mimetype:
          #   full_body = ''
          #   for i, part in enumerate(item['payload']['parts']):
          #     print(f'\nPART{i}\n')
          #     body = part['body']['data']
          #     body = base64.urlsafe_b64decode(body.encode('UTF-8'))
          #     body = body.decode('utf-8')
          #     if part['mimeType'] == 'text/plain':
          #       print('part[\'mimeType\']', part['mimeType'])
          #       print(f'Plain: {body=}')
          #       full_body += body
          #     elif part['mimeType'] == 'text/html':
          #       print(f'HTML: {body=}')
          #       print('part[\'mimeType\']', part['mimeType'])
          #       soup = BeautifulSoup(body, 'html.parser')
          #       soup_text = soup.get_text()
          #       full_body += soup_text
          #     else:
          #       print('part[\'mimeType\']', part['mimeType'])
          # else:
          #   full_body = item['payload']['body']['data']
          #   full_body = base64.urlsafe_b64decode(body.encode('UTF-8'))
          #   full_body = body.decode('utf-8')
          #   if part['mimeType'] == 'text/plain':
          #     full_body = body
          #   elif part['mimeType'] == 'text/html':
          #     soup = BeautifulSoup(full_body, 'html.parser')
          #     soup_text = soup.get_text()
          #     full_body = soup_text
          #   else:
          #     print('part[\'mimeType\']', part['mimeType'])