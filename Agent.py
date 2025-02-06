from __future__ import print_function
import datetime
import os
import pickle
import re
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not NEWSAPI_KEY or not OPENAI_API_KEY:
    raise ValueError("Please set the NEWSAPI_KEY and OPENAI_API_KEY in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)
from dotenv import load_dotenv

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request



# -------------------------
# Define Scopes for all required APIs
# -------------------------
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]


# -------------------------
# Google Docs API Functions
# -------------------------
def get_credentials():
    """
    Obtains valid user credentials from storage. If nothing has been stored,
    or if the stored credentials are invalid, the OAuth2 flow is completed to
    obtain new credentials.
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

def markdown_to_requests(markdown_text):
    """
    Converts simple Markdown (only headers and plain text) into Google Docs API requests.
    This is a simple example – you can extend it for additional Markdown features.
    """
    requests_body = []
    current_index = 1  # start after document start

    for line in markdown_text.splitlines():
        # Determine the style based on header markers.
        if line.startswith("### "):
            # Small header (e.g., Heading 3)
            text = line.replace("### ", "")
            text_style = {"bold": True, "fontSize": {"magnitude": 12, "unit": "PT"}}
        elif line.startswith("## "):
            # Medium header (e.g., Heading 2)
            text = line.replace("## ", "")
            text_style = {"bold": True, "fontSize": {"magnitude": 14, "unit": "PT"}}
        elif line.startswith("# "):
            # Large header (e.g., Heading 1)
            text = line.replace("# ", "")
            text_style = {"bold": True, "fontSize": {"magnitude": 16, "unit": "PT"}}
        else:
            text = line
            text_style = {}  # no extra formatting

        # Insert the text.
        requests_body.append({
            'insertText': {
                'location': {'index': current_index},
                'text': text + "\n"  # add newline after each line
            }
        })

        # If there is any style, add a request to update the text style.
        if text_style:
            requests_body.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(text)
                    },
                    'textStyle': text_style,
                    'fields': 'bold,fontSize'
                }
            })

        current_index += len(text) + 1  # update index (plus newline)

    return requests_body

def create_google_doc(activity_text):
    """
    Creates a new Google Doc titled "activity for <today's date>" and inserts
    the provided activity_text into the document, applying basic Markdown formatting.
    """
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    title = f"activity for {today_str}"

    document_body = {'title': title}
    doc = service.documents().create(body=document_body).execute()
    document_id = doc.get('documentId')
    print(f"Created document with title: '{title}', ID: {document_id}")

    # Convert Markdown to API requests.
    requests_body = markdown_to_requests(activity_text)
    service.documents().batchUpdate(documentId=document_id, body={'requests': requests_body}).execute()
    print("Inserted formatted text into the document.")

    document_url = f"https://docs.google.com/document/d/{document_id}/edit"
    return document_url


# -------------------------
# News, Email, and Calendar Functions
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
            paragraphs = soup.find_all('p')  # Find all paragraph elements

            all_text = ""
            for p in paragraphs:
                text = p.get_text(strip=True)
                all_text += text + " "  # Add each paragraph's text with a space

            return all_text.strip() # Remove any trailing space.
        else:
            print(f"Request to {url} returned status code: {response.status_code}") # More informative error output
    except requests.exceptions.RequestException as e:  # Catch specific requests exceptions
        print(f"Error fetching snippet from {url}: {e}")
    except Exception as e: # Catch any other unexpected exceptions
        print(f"An unexpected error occurred while processing {url}: {e}")
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
        "language": "en",
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


def extract_email_address(from_header):
    """
    Extracts an email address from a 'From' header string.

    Args:
        from_header (str): The full from header.

    Returns:
        email (str): The extracted email address.
    """
    match = re.search(r'<(.+?)>', from_header)
    if match:
        return match.group(1).lower()
    return from_header.strip().lower()


def compile_emails_section(creds, alert_senders):
    """
    Retrieves Gmail messages from the last 24 hours, compiles them into a text block,
    and flags any emails coming from addresses in the alert_senders list.

    Args:
        creds: Google API credentials.
        alert_senders (list): List of email addresses to alert on.

    Returns:
        emails_text (str): A text block with email details.
    """
    gmail_service = build('gmail', 'v1', credentials=creds)
    query = "newer_than:1d"
    results = gmail_service.users().messages().list(userId='me', q=query).execute()
    messages = results.get("messages", [])

    emails_text = "### Emails Received in the Last 24 Hours\n\n"

    if not messages:
        emails_text += "No emails received in the last 24 hours.\n\n"
        return emails_text

    for msg in messages:
        msg_id = msg.get("id")
        msg_detail = gmail_service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = msg_detail.get("payload", {}).get("headers", [])

        subject = "No Subject"
        from_field = "Unknown"
        date = "Unknown Date"
        for header in headers:
            name = header.get("name", "").lower()
            if name == "subject":
                subject = header.get("value")
            elif name == "from":
                from_field = header.get("value")
            elif name == "date":
                date = header.get("value")

        # Extract email address from the From header.
        sender_email = extract_email_address(from_field)
        alert = " [ALERT]" if sender_email in [x.lower() for x in alert_senders] else ""

        snippet = msg_detail.get("snippet", "")
        emails_text += f"**Subject:** {subject}{alert}\n"
        emails_text += f"**From:** {from_field}\n"
        emails_text += f"**Date:** {date}\n"
        emails_text += f"Snippet: {snippet}\n\n"
    return emails_text


def compile_calendar_section(creds):
    """
    Retrieves calendar events happening in the next 24 hours and compiles them into a text block.

    Args:
        creds: Google API credentials.

    Returns:
        calendar_text (str): A text block with upcoming event details.
    """
    calendar_service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=1)).isoformat() + 'Z'

    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    calendar_text = "### Calendar Events in the Next 24 Hours\n\n"
    if not events:
        calendar_text += "No upcoming events in the next 24 hours.\n\n"
    else:
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
            summary = event.get('summary', 'No Title')
            calendar_text += f"**{summary}** at {start}\n\n"
    return calendar_text


def summarize_text(prompt_text, summary_prompt):
    """
    Uses OpenAI's API to summarize the given text.

    Args:
        prompt_text (str): The text to summarize.
        summary_prompt (str): Instructions to the AI for how to summarize.

    Returns:
        summary (str): The summary generated by OpenAI.
    """

    url = "https://api.openai.com/v1/chat/completions"  # Correct URL for chat completions
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,  # Set the User-Agent header
    }

    full_prompt = f"{summary_prompt}\n\n{prompt_text}\n\nSummary:"

    data = {
        "model": "o3-mini-2025-01-31",  # or gpt-3.5-turbo if that is what you intended
        "messages": [
            {"role": "system", "content": "You are a helpful AI Agent."},
            {"role": "user", "content": full_prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        json_response = response.json()
        return json_response["choices"][0]["message"]["content"].strip()  # Access the content correctly

    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAI (requests): {e}")
        if response.status_code != 200:
            try:
                error_message = response.json()
                print(f"OpenAI API Error details: {error_message}")
            except:
                print(f"OpenAI API Error details: Status Code: {response.status_code}")
        return ""
    except (KeyError, IndexError) as e:  # Handle potential JSON parsing errors
        print(f"Error parsing OpenAI response: {e}")
        print(f"Raw response: {response.text}")  # print the raw response to help with debugging
        return ""
    except Exception as e:  # Catch any other exceptions
        print(f"An unexpected error occurred: {e}")
        return ""


# -------------------------
# Telegram Integration Function
# -------------------------
def summarise_for_telegram(text, google_doc_url):
    """
    Uses OpenAI to summarize the provided text, appends a link for more details,
    and posts the final message to a Telegram bot.

    Args:
        text (str): The text to summarize.
        google_doc_url (str): The URL of the Google Doc to be shared.
    """
    # Create a summary using OpenAI.
    telegram_summary_prompt = "Summarize the following content for a quick Telegram update:"
    full_prompt = f"{telegram_summary_prompt}\n\n{text}\n\nSummary:"

    url = "https://api.openai.com/v1/chat/completions"  # Correct URL for chat completions
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,  # Set the User-Agent header
    }

    data = {
        "model": "o3-mini-2025-01-31",  # or gpt-3.5-turbo if that is what you intended
        "messages": [
            {"role": "system", "content": "You are a helpful AI Agent."},
            {"role": "user", "content": full_prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        json_response = response.json()
        summary = json_response["choices"][0]["message"]["content"].strip()  # Access the content correctly

    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAI (requests): {e}")
        if response.status_code != 200:
            try:
                error_message = response.json()
                print(f"OpenAI API Error details: {error_message}")
            except:
                print(f"OpenAI API Error details: Status Code: {response.status_code}")
        return ""
    except (KeyError, IndexError) as e:  # Handle potential JSON parsing errors
        print(f"Error parsing OpenAI response: {e}")
        print(f"Raw response: {response.text}")  # print the raw response to help with debugging
        return ""
    except Exception as e:  # Catch any other exceptions
        print(f"An unexpected error occurred: {e}")
        return ""


    # Append the link to the Google Doc.

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        r = requests.get(telegram_url)
        if r.status_code == 200:
            updates = r.json()
            if updates['ok']:
                # Find the latest message from the user
                for update in reversed(updates['result']):  # Reverse to get the latest first
                    if 'message' in update and 'chat' in update['message']:
                        chat_id = update['message']['chat']['id']
                        print(f"Chat ID: {chat_id}")
                        break  # Found it, no need to continue
            else:
                print("Error getting updates:", updates['description'])
        else:
            print("Error getting updates. Status code:", r.status_code)
    except requests.exceptions.RequestException as e:
        print("Error getting updates:", e)

    message = f"{summary}\n\nFor more details see {google_doc_url}"

    # Get Telegram Bot token and chat id from environment variables.
    TELEGRAM_CHAT_ID = chat_id
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set in .env.")
        return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        r = requests.post(telegram_url, data=payload)
        if r.status_code == 200:
            print("Message posted to Telegram successfully.")
        else:
            print("Failed to post message to Telegram. Response:", r.text)
    except Exception as e:
        print("Error posting to Telegram:", e)


# -------------------------
# Todoist Integration Function
# -------------------------
def create_todo_list(text):
    """
    Uses OpenAI to generate actionable todo tasks from the provided text and then
    creates them in Todoist via their API with the due date set to today.

    Args:
        text (str): The text from which to generate todo tasks.
    """
    # Create a prompt to extract tasks.
    full_prompt = (
        "Extract actionable todo tasks from the following text. "
        "List each task on a new line. Only include tasks that can be completed today.\n\n"
        f"{text}\n\nTasks:"
    )
    url = "https://api.openai.com/v1/chat/completions"  # Correct URL for chat completions
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,  # Set the User-Agent header
    }


    data = {
        "model": "o3-mini-2025-01-31",  # or gpt-3.5-turbo if that is what you intended
        "messages": [
            {"role": "system", "content": "You are a helpful AI Agent."},
            {"role": "user", "content": full_prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        json_response = response.json()
        lines = json_response["choices"][0]["message"]["content"].strip()  # Access the content correctly

    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAI (requests): {e}")
        if response.status_code != 200:
            try:
                error_message = response.json()
                print(f"OpenAI API Error details: {error_message}")
            except:
                print(f"OpenAI API Error details: Status Code: {response.status_code}")
        return ""
    except (KeyError, IndexError) as e:  # Handle potential JSON parsing errors
        print(f"Error parsing OpenAI response: {e}")
        print(f"Raw response: {response.text}")  # print the raw response to help with debugging
        return ""
    except Exception as e:  # Catch any other exceptions
        print(f"An unexpected error occurred: {e}")
        return ""

    # Parse tasks by splitting on newlines.
    tasks = [line.strip("- ").strip() for line in lines.splitlines() if line.strip()]
    if not tasks:
        print("No valid tasks found.")
        return

    # Get Todoist API key from environment.
    TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
    if not TODOIST_API_KEY:
        print("TODOIST_API_KEY not set in .env.")
        return

    todoist_url = "https://api.todoist.com/rest/v2/tasks"
    headers = {
        "Authorization": f"Bearer {TODOIST_API_KEY}",
        "Content-Type": "application/json"
    }

    today_str = datetime.date.today().isoformat()  # e.g. "2025-02-05"

    for task in tasks:
        data = {
            "content": task,
            "due_string": "today",
            "due_date": today_str
        }
        try:
            r = requests.post(todoist_url, headers=headers, json=data)
            if r.status_code in [200, 204]:
                print(f"Task created: {task}")
            else:
                print(f"Failed to create task '{task}': {r.text}")
        except Exception as e:
            print(f"Error creating task '{task}': {e}")


# -------------------------
# Main Functionality
# -------------------------
if __name__ == '__main__':
    # Get Google API credentials (for Docs, Gmail, and Calendar).
    creds = get_credentials()

    # 1. News Section
    top_articles = get_news(NEWSAPI_KEY, limit=20)
    top_section = compile_news_section(top_articles, "Top Stories")
    print("Fetched top stories.")

    trans_articles = get_news(NEWSAPI_KEY, query="transgender", limit=20)
    trans_section = compile_news_section(trans_articles, "Transgender News")
    print("Fetched transgender news.")

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

    # 2. Email Section (Last 24 Hours)
    # Define alert senders. My email is the first one.
    alert_senders_str = os.getenv("ALERT_SENDERS", "")
    alert_senders = [email.strip() for email in alert_senders_str.split(",") if email.strip()]
    emails_section = compile_emails_section(creds, alert_senders)
    emails_summary_prompt = (
        "Summarize the following email headlines and snippets, highlighting any alerts. "
        "Focus on key subjects and senders."
    )
    emails_summary = summarize_text(emails_section, emails_summary_prompt)

    # 3. Calendar Events Section (Next 24 Hours)
    calendar_section = compile_calendar_section(creds)

    # Construct the incoming text for the Google Doc.
    incoming_text = (
        "## Email Summaries (Last 24 Hours)\n\n"
        "### Emails Summary\n\n"
        f"{emails_summary}\n\n"
        "## Calendar Events (Next 24 Hours)\n\n"
        f"{calendar_section}\n"
        "## News Summaries\n\n"
        "### Top Stories Summary\n\n"
        f"{top_summary}\n\n"
        "Detailed Top Stories:\n\n"
        f"{top_section}\n\n"
        "### Transgender News Summary\n\n"
        f"{trans_summary}\n\n"
        "Detailed Transgender News:\n\n"
        f"{trans_section}\n\n"
    )

    # Create a Google Doc with the incoming text.
    google_doc_url = create_google_doc(incoming_text)
    print("Google Doc created at:", google_doc_url)

    # Post the summary to Telegram, including the Google Doc link.
    summarise_for_telegram(incoming_text, google_doc_url)

    # Create todo tasks in Todoist from the incoming text.
    create_todo_list(incoming_text)
