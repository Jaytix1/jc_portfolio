# FlakkAi — AI Code Analysis Platform

An AI-powered code analysis platform that detects bugs, security vulnerabilities, and performance issues in real time. Powered by the Claude API (Anthropic).

**Live Demo:** https://jc-portfolio-gjm1.onrender.com

---

## Features

- Real-time code analysis powered by Claude AI
- Supports 13+ programming languages
- Analyzes across 5 dimensions: Bugs, Security, Performance, Best Practices, Readability
- Educational feedback — explains *what* is wrong, *why* it matters, and *how* to fix it
- Multi-file upload support
- Analysis history

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI | Claude API (Anthropic) — `claude-haiku-4-5` |
| Frontend | Vanilla JavaScript, HTML, CSS |
| Deployment | Render |

## Local Setup

1. Clone the repo and navigate to the FlakkAi directory:
   ```bash
   cd FlakkAi
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   source venv/bin/activate      # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your API key:
   ```bash
   cp .env.example .env
   # Add your Anthropic API key to .env
   ```

5. Run the app:
   ```bash
   python app.py
   ```

6. Open http://localhost:5001

## Getting a Claude API Key

1. Go to https://console.anthropic.com
2. Create an account and navigate to API Keys
3. Create a new key and add it to your `.env` as `ANTHROPIC_API_KEY`
