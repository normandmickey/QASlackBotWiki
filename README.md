 QA Slack Bot Wiki

## Introduction
This application is a Slack Bot that uses Langchain and OpenAI's GPT3 language model to provide domain specific answers. You provide the knowledge base using a MediaWiki website and supporting documents in PDF or DOCX. 

## Features
- GPT based Slack Bot using your own knowledge base (MediaWiki website required). 
- Knowledge base can be supplemented with Word Docs (DOCX) or PDF files.  
- Uses local FAISS vector database.  

## Usage
To use the QA Slack Bot Wiki, the following environment variables need to be set in your .env file:
- SLACK_BOT_TOKEN: Token for the Slack Bot.
- SLACK_APP_TOKEN: Token for the Slack app.
- OPENAI_API_TOKEN: Token for OpenAi
- MEDIAWIKI_BASE_URL: Base URL for MediaWiki site (ie. https://wiki.yoursite.com). 
- MEDIAWIKI_LOGIN_URL: Login page for your MediaWiki site. 
- MEDIAWIKI_ALLPAGES_URL: 
- MEDIAWIKI_USERNAME:
- MEDIAWIKI_PASSWORD:
- DOCUMENTS_FOLDER: 

## Installation
Requires Python3.10 or higher

Clone this repo and run the following commands 

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
```

1. Set your OPENAI_API_TOKEN in the .env file. 

2. Create new Slack App - https://api.slack.com

3. Click on "Basic Information"
   - Click on "Generate Token and Scopes"
     - Token Name = "App Token"
     - App Scope = "connections:write"

   - Copy "App Token" and paste it into your .env file as "SLACK_APP_TOKEN". 

4. Click on "Socket Mode"
   - Click on "Enable"

5. Click on "OAuth & Permissions" and add the following permissions. 
   - app_mentions:read
   - chat:write
   - chat:write.public
   - im:history

   - Copy "Bot User OAuth Token" and paste it into your .env file as "SLACK_BOT_TOKEN". 

6. Click on "App Home" and make sure "Messages Tab" is enabled and check the box for "Allow users to send Slash commands and messages from the messages tab". 

7. Click on "Event Subscriptions" then "Subscribe to Bot Events" and add the following events. 
    - app_mention
    - message.im

8. Install App into your Slack. 

9. Create a directory called "wiki". 
```
mkdir wiki
```

10. Upload or copy your .pdf or .docx files to the "wiki" folder. 

11. Run the following commands.
 
   ```
   python ingest.py
   python app.py
   ```

12. Visit your Slack and send direct message to your bot. 

13. Your vector database needs to be re-indexed each time you add or remove documents from your docs folder. To do this simply run 
```python ingest.py```. 
