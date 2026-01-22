import os

# Database configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTACRUISE_DIR = os.path.join(BASE_DIR, 'Histacruise')
DATABASE_PATH = os.path.join(HISTACRUISE_DIR, 'instance', 'histacruise.db')
DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# Stock symbols to track
STOCK_SYMBOLS = ['CCL', 'RCL', 'NCLH']

# RSS Feed sources for news
NEWS_FEEDS = [
    {'name': 'CruiseHive', 'url': 'https://www.cruisehive.com/feed'},
    {'name': 'CruiseCritic', 'url': 'https://www.cruisecritic.com/news/rss/'},
    {'name': 'Maritime Executive', 'url': 'https://maritime-executive.com/rss'},
]

# RSS Feed sources for deals
DEALS_FEEDS = [
    {'name': 'CruiseCritic Deals', 'url': 'https://www.cruisecritic.com/deals/rss/'},
]

# Rate limiting (requests per minute)
RATE_LIMITS = {
    'yfinance': 30,
    'rss_feeds': 20,
    'wikipedia': 20,
}

# Logging
LOG_DIR = os.path.join(BASE_DIR, 'HC_Pipeline', 'logs')
LOG_LEVEL = 'INFO'
