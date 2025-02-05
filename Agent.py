from __future__ import print_function
import datetime
import os
import pickle
import requests
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Load environment variables from .env file.
load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not NEWSAPI_KEY or not OPENAI_API_KEY:
    raise ValueError("Please set the NEWSAPI_KEY and OPENAI_API_KEY in your .env file.")

openai.api_key = OPENAI_API_KEY

# -------------------------
# Google Docs API Functions
# -------------------------
SCOPES = ['https://www.googleapis.com/auth/documents']


def get_credentials():
    """
    Obtains valid user credentials from storage. If nothing has been stored, or
    if the stored credentials are invalid, the OAuth2 flow is completed to obtain
    new credentials.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def create_google_doc(activity_text):
    """
    Creates a new Google Doc titled "activity for <today's date>" and inserts
    the provided activity_text into the document.

    Args:
        activity_text (str): The text content to insert into the document.

    Returns:
        document_url (str): The URL of the created Google Doc.
    """
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    title = f"activity for {today_str}"

    document_body = {'title': title}
    doc = service.documents().create(body=document_body).execute()
    document_id = doc.get('documentId')
    print(f"Created document with title: '{title}', ID: {document_id}")

    # Insert the text at index 1 (after document start).
    requests_body = [
        {
            'insertText': {
                'location': {'index': 1},
                'text': activity_text
            }
        }
    ]
    service.documents().batchUpdate(documentId=document_id, body={'requests': requests_body}).execute()
    print("Inserted text into the document.")

    # Construct the document URL.
    document_url = f"https://docs.google.com/document/d/{document_id}/edit"
    return document_url


# -------------------------
# News and Summarization Functions
# -------------------------
USER_AGENT = "Agent (https://github.com/Heather-Herbert/Agent)"


def fetch_article_snippet(url):
    """
    Uses BeautifulSoup to fetch the first paragraph of an article.

    Args:
        url (str): The URL of the article.

    Returns:
        snippet (str): The first paragraph text, or an empty string if not found.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            p = soup.find('p')
            if p:
                return p.get_text(strip=True)
    except Exception as e:
        print(f"Error fetching snippet from {url}: {e}")
    return ""


def get_news(api_key, query=None, limit=3):
    """
    Retrieves news articles from NewsAPI.

    Args:
        api_key (str): Your NewsAPI key.
        query (str): Optional query parameter (e.g. "transgender") for filtering news.
        limit (int): Maximum number of articles to return.

    Returns:
        articles (list): List of articles from NewsAPI.
    """
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": api_key,
        "country": "us",
        "pageSize": limit
    }
    if query:
        params["q"] = query
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if data.get("status") != "ok":
        print("Error fetching news:", data.get("message"))
        return []
    return data.get("articles", [])


def compile_news_section(articles, section_title):
    """
    Compiles a section of news into a text block.

    Args:
        articles (list): List of articles (each article is a dict).
        section_title (str): Title for this section.

    Returns:
        section_text (str): A text block with headlines, snippets, and links.
    """
    section_text = f"### {section_title}\n\n"
    for article in articles:
        title = article.get("title", "No Title")
        url = article.get("url", "")
        snippet = fetch_article_snippet(url)
        section_text += f"**{title}**\n\n"
        if snippet:
            section_text += f"Snippet: {snippet}\n\n"
        section_text += f"Link: {url}\n\n"
    return section_text


def summarize_text(prompt_text, summary_prompt):
    """
    Uses OpenAI's API to summarize the given text.

    Args:
        prompt_text (str): The text to summarize.
        summary_prompt (str): Instructions to the AI for how to summarize.

    Returns:
        summary (str): The summary generated by OpenAI.
    """
    full_prompt = f"{summary_prompt}\n\n{prompt_text}\n\nSummary:"
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print("Error calling OpenAI:", e)
        return ""


# -------------------------
# Placeholder Functions
# -------------------------
def summarise_for_telegram(text, google_doc_url):
    """
    Placeholder for a function that summarises the provided text for Telegram.

    Args:
        text (str): The text to summarise.
        google_doc_url (str): The URL of the Google Doc to be shared.

    Returns:
        None
    """
    # TODO: Implement summarisation logic for Telegram.
    # You can send the google_doc_url along with your summary message.
    print("Telegram summary placeholder:")
    print(f"Google Doc URL: {google_doc_url}")
    print(f"Text: {text[:100]}...")  # Print first 100 characters as a sample.
    pass


def create_todo_list(text):
    """
    Placeholder for a function that creates a todo list based on the provided text.

    Args:
        text (str): The text from which to create a todo list.

    Returns:
        None
    """
    # TODO: Implement logic to extract or generate todo items.
    pass


# -------------------------
# Main Functionality
# -------------------------
if __name__ == '__main__':
    # Fetch top stories (limit to 3 for brevity)
    top_articles = get_news(NEWSAPI_KEY, limit=3)
    top_section = compile_news_section(top_articles, "Top Stories")
    print("Fetched top stories.")

    # Fetch transgender-related news (limit to 3)
    trans_articles = get_news(NEWSAPI_KEY, query="transgender", limit=3)
    trans_section = compile_news_section(trans_articles, "Transgender News")
    print("Fetched transgender news.")

    # Make two OpenAI calls to summarise each section.
    top_summary_prompt = (
        "Summarize the following top news headlines, including key points and context. "
        "Include the links provided as references."
    )
    top_summary = summarize_text(top_section, top_summary_prompt)

    trans_summary_prompt = (
        "Summarize the following transgender-related news headlines, highlighting the main themes and events. "
        "Include the links provided as references."
    )
    trans_summary = summarize_text(trans_section, trans_summary_prompt)

    # Construct the incoming text for the Google Doc.
    incoming_text = (
        "## News Summaries\n\n"
        "### Top Stories Summary\n\n"
        f"{top_summary}\n\n"
        "Detailed Top Stories:\n\n"
        f"{top_section}\n\n"
        "### Transgender News Summary\n\n"
        f"{trans_summary}\n\n"
        "Detailed Transgender News:\n\n"
        f"{trans_section}\n"
    )

    # Create a Google Doc with the incoming text.
    google_doc_url = create_google_doc(incoming_text)
    print("Google Doc created at:", google_doc_url)

    # Pass the google_doc_url to the Telegram summarisation function.
    summarise_for_telegram(incoming_text, google_doc_url)

    # Optionally, you can also call the placeholder function for creating a todo list:
    # create_todo_list(incoming_text)
