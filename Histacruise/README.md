# Histacruise — Full-Stack Cruise Tracking Application

A full-stack web application for tracking personal cruise history with analytics dashboards, interactive port maps, a social community layer, and a live data pipeline collecting cruise industry stocks, news, and deals on scheduled intervals.

**Live Demo:** https://jc-portfolio-2.onrender.com  
**Demo Login:** `demo@histacruise.com` / `Demo1234!`

---

## Features

- **Interactive Port Map** — Leaflet.js map with markers for every port visited across all cruises
- **Spending Analytics** — Chart.js dashboards breaking down spending by cruise line, region, cabin type, and year
- **Live Data Pipeline** — HC_Pipeline collects cruise stock prices (CCL, RCL, NCLH), industry news, and deals on a schedule via APScheduler
- **Social Community** — follow other cruisers, share posts, react and comment, earn badges, and discover new users
- **User Authentication** — Flask-Login with secure session management and profile privacy controls
- **Friend & Block System** — send/accept friend requests, control cruise visibility per entry
- **Photo Galleries** — upload cruise and profile photos stored as BLOBs in the database
- **Badges & Milestones** — achievement system for cruise milestones (first voyage, globe trotter, days at sea, etc.)
- **Notifications** — real-time notification system for follows, likes, and comments

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Flask 3.0 |
| Database | PostgreSQL (Supabase), SQLAlchemy ORM, Alembic Migrations |
| Auth | Flask-Login, Werkzeug password hashing |
| Pipeline | APScheduler, yfinance, feedparser, BeautifulSoup4 |
| Frontend | Leaflet.js, Chart.js, Jinja2, JavaScript |
| Deployment | Render (Gunicorn), Supabase |

## Pipeline Architecture

The HC_Pipeline runs as a background daemon thread at startup and on a schedule:

| Collector | Interval | Data |
|---|---|---|
| Stock Collector | Every 2 hours | CCL, RCL, NCLH share prices via yfinance |
| News Collector | Every 3 hours | Headlines from cruise industry RSS feeds |
| Deals Collector | Every 6 hours | Active promotions from major cruise lines |
| Ship Collector | Every 24 hours | Technical specs for ships in the database |

## Local Setup

1. Navigate to the Histacruise directory:
   ```bash
   cd Histacruise
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

4. Set up environment variables:
   ```bash
   # Create a .env file with:
   DATABASE_URL=your_postgres_connection_string  # or leave unset for SQLite fallback
   SECRET_KEY=your_secret_key
   ```

5. Run the app:
   ```bash
   python app.py
   ```

6. Open http://localhost:5002

> **Database:** Production uses Supabase PostgreSQL via `DATABASE_URL`. Locally it falls back to SQLite automatically if `DATABASE_URL` is not set.
