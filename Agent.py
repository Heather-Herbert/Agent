from __future__ import print_function
import datetime
import os.path
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents']


def get_credentials():
    """
    Obtains valid user credentials from storage. If nothing has been stored, or
    if the stored credentials are invalid, the OAuth2 flow is completed to obtain
    new credentials.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials are available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Make sure you have your credentials.json file from Google Cloud Console.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run.
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
        document_id (str): The ID of the created Google Doc.
    """
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)

    # Create a title using today's date.
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    title = f"activity for {today_str}"

    # Create the document with the specified title.
    document_body = {
        'title': title
    }
    doc = service.documents().create(body=document_body).execute()
    document_id = doc.get('documentId')
    print(f"Created document with title: '{title}', ID: {document_id}")

    # Insert the provided activity text at the beginning of the document.
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1,  # Index 1 because index 0 is reserved for the document start.
                },
                'text': activity_text
            }
        }
    ]
    service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
    print("Inserted text into the document.")

    return document_id


def summarise_for_telegram(text):
    """
    Placeholder for a function that summarises the provided text for Telegram.

    Args:
        text (str): The text to summarise.

    Returns:
        None
    """
    # TODO: Implement summarisation logic for Telegram.
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


if __name__ == '__main__':
    # Example incoming text that will be inserted into the new Google Doc.
    incoming_text = (
        "Today I worked on integrating the Google Docs API with our application.\n"
        "I fixed some bugs and planned out the next steps for the project."
    )

    # Create the Google Doc with the incoming text.
    create_google_doc(incoming_text)
