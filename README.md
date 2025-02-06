# Automated Daily Summary Generator

## Overview
This Python application automates the process of fetching news articles, summarizing key points, extracting email details, and retrieving calendar events. The summarized information is compiled into a Google Document, with an option to share updates via Telegram and generate actionable tasks in Todoist.

## Features
- **News Retrieval:** Fetches top headlines and category-specific articles using the NewsAPI.
- **Email Summaries:** Extracts subject lines and snippets from Gmail messages.
- **Calendar Events:** Retrieves upcoming events from Google Calendar.
- **Google Docs Integration:** Creates a Google Document with structured summaries.
- **AI Summarization:** Uses OpenAI's API to generate concise summaries.
- **Telegram Integration:** Posts updates to a Telegram chat.
- **Todoist Task Creation:** Converts relevant information into actionable tasks.

## Prerequisites
Ensure you have the following dependencies installed and API keys set up:

### API Keys & Authentication
- **NewsAPI Key**: `NEWSAPI_KEY`
- **OpenAI API Key**: `OPENAI_API_KEY`
- **Google API Credentials**: `credentials.json`
- **Telegram Bot Token**: `TELEGRAM_BOT_TOKEN`
- **Todoist API Key**: `TODOIST_API_KEY`

Set these environment variables in a `.env` file.

```
NEWSAPI_KEY=your_newsapi_key
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TODOIST_API_KEY=your_todoist_api_key
ALERT_SENDERS=email1@example.com,email2@example.com
```

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/summary-bot.git
   cd summary-bot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Authenticate with Google:
   - Place `credentials.json` in the root directory.
   - Run the script to authenticate and generate `token.pickle`.

## Usage
Run the script using:
```sh
python Agent.py
```

## How It Works
1. **Fetch News**: Retrieves articles from NewsAPI and scrapes content using BeautifulSoup.
2. **Summarize Content**: OpenAI API summarizes the fetched news.
3. **Extract Emails & Events**: Google API retrieves recent emails and upcoming events.
4. **Compile & Store**: The summarized content is structured into a Google Document.
5. **Share Updates**: Posts a summary to a Telegram chat and creates Todoist tasks.

## File Structure
```
summary-bot/
├── Agent.py         # Main script
├── requirements.txt # Dependencies
├── credentials.json # Google API credentials (not included in repo)
├── .env             # API keys and environment variables
```

## Contributing
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to your branch: `git push origin feature-name`
5. Open a pull request.

## License
This project is licensed under the GPL3 License.