"""This is the logic for ingesting MediaWiki Site into LangChain."""
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pdfminer.high_level import extract_text
import faiss, pickle, docx2txt, urllib.request, requests
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
from requests.auth import HTTPBasicAuth
from urllib.error import URLError

load_dotenv()
OPENAI_API_TOKEN = os.getenv('OPENAI_API_TOKEN')
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
MEDIAWIKI_BASE_URL = os.getenv('MEDIAWIKI_BASE_URL')
MEDIAWIKI_LOGIN_URL = os.getenv('MEDIAWIKI_LOGIN_URL')
MEDIAWIKI_ALLPAGES_URL = os.getenv('MEDIAWIKI_ALLPAGES_URL')
username = os.getenv('MEDIAWIKI_USERNAME')  # login username
password = os.getenv('MEDIAWIKI_PASSWORD')  # login password

n = 0

LOGIN_URL = MEDIAWIKI_LOGIN_URL

def get_authenticity_token(html):
    soup = BeautifulSoup(html, "html.parser")
    token = soup.find('input', attrs={'name': 'wpLoginToken'})
    if not token:
        print('could not find `wpLoginToken` on login form')
    return token.get('value').strip()

def get_login_authAction(html):
    soup = BeautifulSoup(html, "html.parser")
    authAction = soup.find('input', attrs={'name': 'authAction'})
    if not authAction:
        print('could not find `authAction` on login form')
    return authAction.get('value').strip()

payload = {
    'wpName': username,
    'wpPassword': password
}

session = requests.Session()
session.headers = {'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')}
response = session.get(LOGIN_URL)

token = get_authenticity_token(response.text)
authAction = get_login_authAction(response.text)
payload.update({
    'wpLoginToken': token,
    'authAction': authAction
})

p = session.post(LOGIN_URL, data=payload)  # perform login

url = MEDIAWIKI_ALLPAGES_URL
html = session.get(url)
htmlParse = BeautifulSoup(html.text, 'html.parser')
links = htmlParse.select('a')

for link in links:
    n += 1
    if link.get('href') != None:
      if 'javascript' not in link.get('href'):
        if 'http' in link.get('href'):
          url3 = (link.get('href'))
          url2 = urllib.request.Request(link.get('href'))
          try: html2 = urllib.request.urlopen(url2)
          except urllib.error.URLError as e:
              print(e.reason)
          else:
              html2 = session.get(link.get('href')).text
              htmlParse2 = BeautifulSoup(html2, 'html.parser')
              with open(("wiki/wiki_" + url3.replace("/", "") + ".txt"), 'w') as f:
                for para in htmlParse2.find_all(["p","li"]):
                    f.write(para.get_text())
              page = session.get(url3).text
              soup = BeautifulSoup(page, 'html.parser')
              tables = [soup.find('table', class_="wikitable sortable")]
              print(tables)
              for i, table in enumerate(tables):
                try: df = pd.read_html(str(table))
                except:
                    print("no tables")
                else:
                    df = pd.concat(df)
                    df.style.set_caption(url3)
                    column_headers = list(df.columns.values)
                    for h, header in enumerate(column_headers):
                        df_copy = df.copy()
                        df_copy.insert(loc = h + h, column = "Column Header" + str(h), value = column_headers[h])                 
                        df = df_copy.copy()
                    df.to_csv(("wiki/table_" + url3.replace("/", "") + ".txt"), sep=" ", mode='w', index=False)

        else:
          url3 = (MEDIAWIKI_BASE_URL + link.get('href'))
          url2 = urllib.request.Request(MEDIAWIKI_BASE_URL + link.get('href'))
          try: html2 = urllib.request.urlopen(url2)
          except urllib.error.URLError as e:
              print(e.reason)
          else:
              html2 = session.get(MEDIAWIKI_BASE_URL + link.get('href')).text
              htmlParse2 = BeautifulSoup(html2, 'html.parser')
              with open(("wiki/wiki_" + url3.replace("/", "") + ".txt"), 'w') as f:
                for para in htmlParse2.find_all(["p","li"]):
                    f.write(para.get_text())
              page = session.get(url3).text
              soup = BeautifulSoup(page, 'html.parser')
              tables = [soup.find('table', class_="wikitable sortable")]
              for i, table in enumerate(tables):
                try: df = pd.read_html(str(table))
                except:
                    print("no tables")
                else:
                    df = pd.concat(df)
                    print(len(df))
                    df.style.set_caption(url3)
                    column_headers = list(df.columns.values)
                    j = 0
                    for h, header in enumerate(column_headers):
                        df_copy = df.copy()
                        df_copy.insert(loc = h + h, column = "Column Header" + str(h), value = column_headers[h])
                        df = df_copy.copy()
                    df.to_csv(("wiki/table_" + url3.replace("/", "") + ".txt"), sep=" ", mode='w', index=False)

# Here we convert pdf files to text
files = list(Path("wiki/").glob("**/*.pdf"))
for file in files:
    filename = str(file) + ".txt"
    text = extract_text(file)
    with open(filename, 'w') as f:
        f.write(text)

# Here we convert docx files to text
files = list(Path("wiki/").glob("**/*.docx"))
for file in files:
    filename = str(file) + ".txt"
    text = docx2txt.process(file)
    with open(filename, 'w') as f:
        f.write(text)

# Here we load in the data in the format that Notion exports it in.
ps = list(Path("wiki/").glob("**/*.txt"))

data = []
sources = []
for p in ps:
    with open(p) as f:
        data.append(f.read())
    sources.append(p)

# Here we split the documents, as needed, into smaller chunks.
# We do this due to the context limits of the LLMs.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=500, length_function=len)

docs = []
metadatas = []

for i, d in enumerate(data):
    splits = text_splitter.split_text(d)
    docs.extend(splits)
    metadatas.extend([{"source": sources[i]}] * len(splits))


# Here we create a vector store from the documents and save it to disk.
store = FAISS.from_texts(docs, OpenAIEmbeddings(), metadatas=metadatas)
faiss.write_index(store.index, "wiki_docs.index")
store.index = None
with open("wiki_faiss_store.pkl", "wb") as f:
    pickle.dump(store, f)
