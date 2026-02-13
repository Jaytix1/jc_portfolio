# FlakkAi

AI-powered code review assistant designed for students and development teams.

## Features

- Real-time code analysis with Claude AI
- Multi-language support (Python, JavaScript, Java, C++, and more)
- Educational feedback explaining the "why" behind each suggestion
- Categories: Bugs, Security, Best Practices, Performance, Readability

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # or: source venv/bin/activate  # Mac/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open http://localhost:5001 in your browser

## Getting an API Key

1. Go to https://console.anthropic.com/
2. Create an account
3. Navigate to API Keys
4. Create a new key and copy it to your `.env` file

## Tech Stack

- **Backend**: Flask (Python)
- **AI**: Claude API (Anthropic)
- **Frontend**: Vanilla JS, HTML, CSS
- **Styling**: Custom dark theme with syntax highlighting
