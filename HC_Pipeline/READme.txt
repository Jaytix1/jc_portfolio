HC_Pipeline - Cruise Industry Data Pipeline
==========================================

A data pipeline for collecting cruise industry data including:
- Stock prices (CCL, RCL, NCLH) via Yahoo Finance
- Industry news from RSS feeds
- Cruise deals
- Ship specifications from Wikipedia

SETUP
-----
1. Install dependencies:
   pip install -r requirements.txt

2. Make sure Histacruise app is set up with the database

USAGE
-----
Run from the jc_portfolio directory:

  # Collect stock prices
  python -m HC_Pipeline.run_pipeline --job stocks

  # Collect news articles
  python -m HC_Pipeline.run_pipeline --job news

  # Collect cruise deals
  python -m HC_Pipeline.run_pipeline --job deals

  # Collect ship specifications
  python -m HC_Pipeline.run_pipeline --job ships

  # Run all collectors
  python -m HC_Pipeline.run_pipeline --job all

  # Check pipeline status
  python -m HC_Pipeline.run_pipeline --status

API ENDPOINTS
-------------
Once the Flask app is running, these endpoints are available:

  GET /api/pipeline/stocks         - Stock price data
  GET /api/pipeline/stocks/latest  - Latest prices for all symbols
  GET /api/pipeline/stocks/chart/CCL - Chart data for a symbol
  GET /api/pipeline/news           - Industry news articles
  GET /api/pipeline/deals          - Cruise deals
  GET /api/pipeline/ships          - Ships with specs
  GET /api/pipeline/dashboard      - Aggregated dashboard data
  GET /api/pipeline/status         - Pipeline run history

SCHEDULING
----------
For daily automated runs, use Windows Task Scheduler:

  1. Open Task Scheduler
  2. Create Basic Task
  3. Set trigger to Daily
  4. Action: Start a program
  5. Program: python
  6. Arguments: -m HC_Pipeline.run_pipeline --job all
  7. Start in: C:\Users\joshu\OneDrive\Desktop\jc_portfolio

FOLDER STRUCTURE
----------------
HC_Pipeline/
  __init__.py
  config.py           - Configuration settings
  main.py             - Pipeline orchestrator
  run_pipeline.py     - CLI entry point
  requirements.txt    - Dependencies
  collectors/
    base_collector.py   - Abstract base class
    stock_collector.py  - Yahoo Finance stock data
    news_collector.py   - RSS feed news
    deals_collector.py  - Cruise deals
    ship_collector.py   - Wikipedia ship specs
  models/
    pipeline_models.py  - Database model definitions
  api/
    routes.py           - Flask API blueprint
  logs/
    pipeline_*.log      - Execution logs
