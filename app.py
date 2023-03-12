import os
import json
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain import OpenAI, ConversationChain, LLMChain 
from langchain.chains.conversation.memory import ConversationalBufferWindowMemory
from langchain.chains import LLMChain, VectorDBQAWithSourcesChain
import faiss
import pickle

load_dotenv()

SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
OPENAI_API_TOKEN = os.getenv('OPENAI_API_TOKEN')
DOCUMENTS_FOLDER = os.getenv('DOCUMENTS_FOLDER')
MEDIAWIKI_BASE_URL = os.getenv('MEDIAWIKI_BASE_URL')

# Load the LangChain.
index = faiss.read_index("wiki_docs.index")

with open("wiki_faiss_store.pkl", "rb") as f:
    store = pickle.load(f)

store.index = index

# Initializes your app with your bot token and socket mode handler
app = App(token=SLACK_BOT_TOKEN)

chatgpt_chain = VectorDBQAWithSourcesChain.from_chain_type(OpenAI(temperature=0.2, max_tokens=300), chain_type="stuff", vectorstore=store)

#Message handler for Slack
@app.message(".*")
def message_handler(message, say, logger):
    json_dict = chatgpt_chain({"question": message['text']}, return_only_outputs=False)
    json_str = json.dumps(json_dict)
    data = json.loads(json_str)
    sources=[]
    if "," in data['sources']:
       sources = data['sources'].split(", ",2)
       source = sources[0]
       source2 = sources[1]
    else:
       source = data['sources']
       source2 = ""
    if "I don't know" in data['answer']:
       source = ""
       source2 = ""

    if "title=" in source:
       source = source.replace("title=","*")
       source = source.replace(".txt","*")
       re=source.split("*")
       res=re[1]
       source = "Source: " + MEDIAWIKI_BASE_URL + "/index.php?title=" + res
    else:
       source = source.replace("wiki/","*")
       source = source.replace(".txt","*")
       re=source.split("*")
       try: res=re[1]
       except: res=""
       if res=="":
          source = ""
       else:
          source = "Source: " + DOCUMENTS_FOLDER + res

    if "title=" in source2:
       source2 = source2.replace("title=","*")
       source2 = source2.replace(".txt","*")
       re=source2.split("*")
       res=re[1]
       source2 = "Source2: " + MEDIAWIKI_BASE_URL + "/index.php?title=" + res
    else:
       source2 = source2.replace("wiki/","*")
       source2 = source2.replace(".txt","*")
       re=source2.split("*")
       try: res=re[1]
       except: res=""
       if res=="":
          source2 = ""
       else:
          source2 = "Source2: " + DOCUMENTS_FOLDER + res

    say("Answer: " + data['answer'] + "\n" + source + "\n" + source2)


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
